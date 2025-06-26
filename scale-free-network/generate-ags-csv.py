#!/usr/bin/env python3
"""
generate_log_normal_directed_graph_csv_parallel.py

Generate a directed graph whose out-degree sequence follows a log-normal distribution,
and export vertices and edges in Aerospike Graph bulk-loader CSV format, with parallelism.

Vertices CSV format:
    ~id:String,outDegree:Int,prop1:Long,prop2:Long,prop3:Long,prop4:Long

Edges CSV format:
    ~from:String,~to:String,~label:String,eprop1:Int,eprop2:Int,eprop3:Int,eprop4:Int,eprop5:Int

Usage:
    python generate_log_normal_directed_graph_csv_parallel.py \
        --nodes 100000 \
        --median 20.0 \
        --sigma 1.0 \
        --workers 8 \
        --out_dirs /mnt/disk1,/mnt/disk2,/mnt/disk3 \
        --seed 42
"""

import argparse
import os
import csv
import numpy as np
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import random
from multiprocessing import shared_memory
from time import time
import signal
import sys
import atexit

BATCH_SIZE = 1_000_000  # Increased to 1M
MAX_EDGE_FILE_LINES = 20_000_000  # Increased to 20M
CSV_BUFFER_SIZE = 8 * 1024 * 1024  # 8MB buffer

# Global variables for cleanup
shared_mem = None
executor = None

def cleanup():
    """Cleanup function to handle shared resources."""
    global shared_mem, executor
    if executor is not None:
        print("\nShutting down workers...", file=sys.stderr)
        executor.shutdown(wait=False)
    
    if shared_mem is not None:
        try:
            print("Cleaning up shared memory...", file=sys.stderr)
            shared_mem.close()
            shared_mem.unlink()
        except Exception:
            pass

def signal_handler(signum, frame):
    """Handle interrupt signals."""
    signal_name = signal.Signals(signum).name
    print(f"\nReceived {signal_name}. Cleaning up...", file=sys.stderr)
    cleanup()
    sys.exit(1)

def get_shard_path(base_dir: str, worker_id: int, total_disks: int) -> str:
    disk_number = worker_id % total_disks + 1
    return os.path.join(f"/mnt/data{disk_number}", base_dir)

def generate_vertex_id(n: int) -> str:
    """Generate a numeric vertex ID - much faster than alphanumeric."""
    return f"A{n:019d}"

def generate_long_property(rng: random.Random) -> int:
    return rng.randint(0, 9223372036854775807)

def generate_edge_property(rng: random.Random) -> int:
    return rng.randint(0, 2147483647)

def sample_targets(n, u, k, rng):
    """More efficient target sampling using sets."""
    targets = set()
    while len(targets) < k:
        v = int(rng.integers(0, n))
        if v != u:
            targets.add(v)
    return list(targets)

def process_full_worker(worker_id, shm_name, shape, dtype, seed, n, total_disks, total_workers):
    """Process vertices and edges for a worker using shared memory."""
    # Get shared memory array
    existing_shm = shared_memory.SharedMemory(name=shm_name)
    deg_seq = np.ndarray(shape, dtype=dtype, buffer=existing_shm.buf)

    # Setup output directories
    edge_output_dir = get_shard_path("edges", worker_id, total_disks)
    vertex_output_dir = get_shard_path("vertices", worker_id, total_disks)
    os.makedirs(edge_output_dir, exist_ok=True)
    os.makedirs(vertex_output_dir, exist_ok=True)

    # Initialize files and buffers
    edge_buffer = []
    edge_file_index = 0
    edge_file_line_count = 0
    edge_file_path = os.path.join(edge_output_dir, f'edges_part_{worker_id:02d}_{edge_file_index:03d}.csv')
    edge_file = open(edge_file_path, 'w', newline='', buffering=CSV_BUFFER_SIZE)
    edge_writer = csv.writer(edge_file)
    edge_writer.writerow(['~from', '~to', '~label:String', 
                         'eprop1:Int', 'eprop2:Int', 'eprop3:Int', 'eprop4:Int', 'eprop5:Int'])

    vertex_buffer = []
    vertex_file_path = os.path.join(vertex_output_dir, f'vertices_part_{worker_id:02d}.csv')
    vertex_file = open(vertex_file_path, 'w', newline='', buffering=CSV_BUFFER_SIZE)
    vertex_writer = csv.writer(vertex_file)
    vertex_writer.writerow(['~id', 'outDegree:Int', 'prop1:Long', 'prop2:Long', 'prop3:Long', 'prop4:Long'])

    edges_written = 0
    vertices_written = 0
    last_progress_time = time()
    total_vertices = n // total_workers + (1 if worker_id < n % total_workers else 0)

    # Process vertices in strided fashion
    for u in range(worker_id, n, total_workers):
        deg = deg_seq[u]
        
        # Generate and buffer vertex
        vertex_id = generate_vertex_id(u)
        vrng = random.Random(seed + u)
        props = [generate_long_property(vrng) for _ in range(4)]
        vertex_buffer.append([vertex_id, deg] + props)
        vertices_written += 1

        # Flush vertex buffer if needed
        if len(vertex_buffer) >= BATCH_SIZE:
            vertex_writer.writerows(vertex_buffer)
            vertex_buffer.clear()
            vertex_file.flush()

        # Generate edges if needed
        if deg > 0:
            rng = np.random.default_rng(seed + u)
            for v in sample_targets(n, u, deg, rng):
                erng = random.Random(int(seed + u * n + int(v)))
                edge_buffer.append([
                    generate_vertex_id(u),
                    generate_vertex_id(v),
                    'edge'
                ] + [generate_edge_property(erng) for _ in range(5)])
                edges_written += 1

                # Flush edge buffer if needed
                if len(edge_buffer) >= BATCH_SIZE:
                    edge_writer.writerows(edge_buffer)
                    edge_file_line_count += len(edge_buffer)
                    edge_buffer.clear()
                    edge_file.flush()

                    # Roll over edge file if needed
                    if edge_file_line_count >= MAX_EDGE_FILE_LINES:
                        edge_file.close()
                        edge_file_index += 1
                        edge_file_path = os.path.join(edge_output_dir, f'edges_part_{worker_id:02d}_{edge_file_index:03d}.csv')
                        edge_file = open(edge_file_path, 'w', newline='', buffering=CSV_BUFFER_SIZE)
                        edge_writer = csv.writer(edge_file)
                        edge_writer.writerow(['~from', '~to', '~label:String',
                                           'eprop1:Int', 'eprop2:Int', 'eprop3:Int', 'eprop4:Int', 'eprop5:Int'])
                        edge_file_line_count = 0

        # Print progress every 5 seconds
        current_time = time()
        if current_time - last_progress_time >= 5:
            progress = (vertices_written / total_vertices) * 100
            print(f"Worker {worker_id:02d}: {progress:.1f}% ({vertices_written:,}/{total_vertices:,} vertices, {edges_written:,} edges)")
            last_progress_time = current_time

    # Flush remaining buffers
    if vertex_buffer:
        vertex_writer.writerows(vertex_buffer)
    vertex_file.close()

    if edge_buffer:
        edge_writer.writerows(edge_buffer)
    edge_file.close()

    existing_shm.close()
    print(f"Worker {worker_id:02d}: 100% complete - {vertices_written:,} vertices, {edges_written:,} edges")

def print_degree_distribution(deg_seq: np.ndarray, num_bins: int = 20):
    """Print detailed statistics about the degree distribution."""
    max_deg = np.max(deg_seq)
    min_deg = np.min(deg_seq)
    mean_deg = np.mean(deg_seq)
    median_deg = np.median(deg_seq)
    total_edges = np.sum(deg_seq)
    
    print("\nDegree Distribution Statistics:")
    print(f"Total vertices: {len(deg_seq):,}")
    print(f"Total edges: {total_edges:,}")
    print(f"Maximum degree: {max_deg:,}")
    print(f"Minimum degree: {min_deg:,}")
    print(f"Average degree: {mean_deg:.2f}")
    print(f"Median degree: {median_deg:.2f}")
    
    # Print logarithmic histogram for the rest
    print("\nLogarithmic Distribution Histogram:")
    if max_deg > 10:
        # Create logarithmic bins
        high_deg_seq = deg_seq[deg_seq > 10]
        if len(high_deg_seq) > 0:
            log_max = np.log10(max_deg)
            # Generate more bins than needed and then remove duplicates
            raw_bins = np.logspace(1, log_max, num=40)
            # Round and ensure unique, monotonically increasing bins
            bins = np.unique(np.round(raw_bins))
            # Add 11 as the starting point if not present
            if bins[0] > 11:
                bins = np.concatenate(([11], bins))
            
            hist, bin_edges = np.histogram(high_deg_seq, bins=bins)
            max_count = np.max(hist)
            
            for count, bin_start, bin_end in zip(hist, bin_edges[:-1], bin_edges[1:]):
                if count > 0:
                    bar_len = int((count / max_count) * 50)
                    percentage = (count / len(deg_seq)) * 100
                    print(f"{bin_start:6.0f} - {bin_end:6.0f} | {'*' * bar_len} ({count:,} vertices, {percentage:.1f}%)")

def main():
    global shared_mem, executor
    
    # Register cleanup handlers
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    start = time()

    try:
        p = argparse.ArgumentParser(
            description="Generate log-normal directed graph CSVs with parallelism"
        )
        p.add_argument('--nodes', type=int, default=100000,
                       help='Number of vertices')
        p.add_argument('--median', type=float, default=20.0,
                       help='Log-normal median of out-degrees')
        p.add_argument('--sigma', type=float, default=1.0,
                       help='Log-normal σ for out-degrees')
        p.add_argument('--workers', type=int, default=None,
                       help='Number of parallel workers (default = CPU count)')
        p.add_argument('--seed', type=int, default=0,
                       help='Base RNG seed for reproducibility')
        p.add_argument('--dry-run', action='store_true',
                       help='Only show degree distribution statistics without generating files')
        args = p.parse_args()

        # Sample degree sequence
        rng = np.random.default_rng(args.seed)
        mu = np.log(args.median)
        exp_deg = rng.lognormal(mean=mu, sigma=args.sigma, size=args.nodes)
        deg_seq = np.round(exp_deg).astype(np.int32)  # Use int32 for shared memory efficiency
        deg_seq[deg_seq < 0] = 0

        # Print detailed distribution statistics
        print_degree_distribution(deg_seq)
        
        if args.dry_run:
            print("\n✔ Dry run completed. No files were generated.")
            return

        # Check for mounted disks
        available_disks = [i for i in range(1, 25) if os.path.ismount(f"/mnt/data{i}")]
        if not available_disks:
            raise RuntimeError("No mounted disks found in /mnt/data*. Please run mount_disks.sh first.")
        print(f"\nFound {len(available_disks)} mounted disks: {', '.join(f'/mnt/data{i}' for i in available_disks)}")

        # Setup shared memory for degree sequence
        shared_mem = shared_memory.SharedMemory(create=True, size=deg_seq.nbytes)
        shm_array = np.ndarray(deg_seq.shape, dtype=deg_seq.dtype, buffer=shared_mem.buf)
        shm_array[:] = deg_seq[:]

        # Optimize worker count
        cpu_count = multiprocessing.cpu_count()
        if args.workers is None:
            workers = max(1, min(len(available_disks), cpu_count))
        else:
            workers = min(args.workers, cpu_count)

        print(f"\nOptimized configuration:")
        print(f"Workers: {workers} (out of {cpu_count} CPUs)")
        print(f"Batch size: {BATCH_SIZE:,}")
        print(f"Edge file size: {MAX_EDGE_FILE_LINES:,}")

        # Process in parallel
        with ProcessPoolExecutor(max_workers=workers) as executor_ctx:
            executor = executor_ctx  # Store for cleanup
            futures = [
                executor.submit(process_full_worker, wid, shared_mem.name, deg_seq.shape, deg_seq.dtype.name,
                              args.seed, args.nodes, len(available_disks), workers)
                for wid in range(workers)
            ]
            
            completed = 0
            for f in futures:
                f.result()
                completed += 1
                print(f"\nProgress: {completed}/{workers} workers completed ({(completed/workers)*100:.1f}%)")

        # Normal cleanup
        executor = None
        shared_mem.close()
        shared_mem.unlink()
        shared_mem = None

        total_edges = np.sum(deg_seq)
        print(f'\n✔ Generated graph with {args.nodes:,} vertices and {total_edges:,} edges')
        print(f'✔ Files distributed across {len(available_disks)} disks')
        print(f'✔ Completed in {(time() - start):.2f} seconds')

    except Exception as e:
        print(f"\nError: {str(e)}", file=sys.stderr)
        raise

if __name__ == '__main__':
    main()
