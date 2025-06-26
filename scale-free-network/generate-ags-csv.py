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
import string
import random
import itertools
import sys

BATCH_SIZE = 50000
MAX_EDGE_FILE_LINES = 5000000

# Add buffer size for CSV writers
CSV_BUFFER_SIZE = 1024 * 1024  # 1MB buffer

def generate_vertex_id(n: int, seed: int) -> str:
    """Generate a 25-character alphanumeric vertex ID."""
    rng = random.Random(seed + n)
    chars = string.ascii_uppercase + string.digits
    return 'U' + ''.join(rng.choice(chars) for _ in range(24))

def generate_long_property(rng: random.Random) -> int:
    """Generate a random long integer property."""
    return rng.randint(0, 9223372036854775807)

def generate_edge_property(rng: random.Random) -> int:
    """Generate a random integer property for edges."""
    return rng.randint(-2147483648, 2147483647)  # Int32 range

def sample_targets(n: int, u: int, deg: int, rng: np.random.Generator) -> np.ndarray:
    """Sample target vertices according to the degree distribution."""
    targets = np.arange(n)
    if u < n:
        targets = np.delete(targets, u)  # exclude self-loops
    if deg <= len(targets):
        return rng.choice(targets, size=deg, replace=False)
    else:
        chosen = list(targets)
        extra = rng.choice(targets, size=deg - len(targets), replace=True)
        return np.concatenate([chosen, extra])

def get_shard_path(base_dir: str, worker_id: int, total_disks: int) -> str:
    """Get the path for a specific worker's shard across available disks."""
    disk_number = worker_id % total_disks + 1
    return os.path.join(f"/mnt/data{disk_number}", base_dir)

def process_chunk(start: int, end: int, deg_seq: np.ndarray, seed: int, n: int, worker_id: int, total_workers: int):
    """Process a chunk of vertices and generate their edges."""
    # Determine total available disks (look for mounted /mnt/data* directories)
    available_disks = [i for i in range(1, 25) if os.path.ismount(f"/mnt/data{i}")]
    if not available_disks:
        raise RuntimeError("No mounted disks found in /mnt/data*")
    total_disks = len(available_disks)
    
    # Get shard-specific paths
    vertex_dir = get_shard_path('vertices', worker_id, total_disks)
    edge_dir = get_shard_path('edges', worker_id, total_disks)
    
    vertex_file = os.path.join(vertex_dir, f'vertices_part_{worker_id:02d}.csv')
    edge_file = os.path.join(edge_dir, f'edges_part_{worker_id:02d}.csv')
    
    os.makedirs(vertex_dir, exist_ok=True)
    os.makedirs(edge_dir, exist_ok=True)

    vertex_buffer = []
    edge_buffer = []
    edge_file_line_count = 0
    edge_file_index = 0
    
    with open(vertex_file, 'w', newline='', buffering=CSV_BUFFER_SIZE) as vf:
        vertex_writer = csv.writer(vf)
        vertex_writer.writerow(['~id', 'outDegree:Int', 'prop1:Long', 'prop2:Long', 'prop3:Long', 'prop4:Long'])
        
        # Open initial edge file with buffering
        ef = open(edge_file, 'w', newline='', buffering=CSV_BUFFER_SIZE)
        edge_writer = csv.writer(ef)
        edge_writer.writerow(['~from', '~to', '~label:String', 
                            'eprop1:Int', 'eprop2:Int', 'eprop3:Int', 'eprop4:Int', 'eprop5:Int'])
        
        try:
            for u in range(start, end):
                deg = deg_seq[u]
                
                # Generate vertex
                vertex_id = generate_vertex_id(u, seed)
                vrng = random.Random(seed + u)
                props = [generate_long_property(vrng) for _ in range(4)]
                vertex_buffer.append([vertex_id, deg] + props)
                
                # Flush vertex buffer if needed
                if len(vertex_buffer) >= BATCH_SIZE:
                    vertex_writer.writerows(vertex_buffer)
                    print(f"Worker {worker_id}: Flushed {len(vertex_buffer)} vertices to {vertex_file}")
                    vertex_buffer.clear()
                    vf.flush()
                
                # Generate edges if degree > 0
                if deg > 0:
                    rng = np.random.default_rng(seed + u)
                    for v in sample_targets(n, u, deg, rng):
                        erng = random.Random(int(seed + u * n + int(v)))
                        edge_props = [generate_edge_property(erng) for _ in range(5)]
                        edge_buffer.append([
                            generate_vertex_id(u, seed),
                            generate_vertex_id(int(v), seed),
                            'edge'
                        ] + edge_props)
                        
                        # Flush edge buffer if needed
                        if len(edge_buffer) >= BATCH_SIZE:
                            edge_writer.writerows(edge_buffer)
                            print(f"Worker {worker_id}: Flushed {len(edge_buffer)} edges to {edge_file}")
                            edge_file_line_count += len(edge_buffer)
                            edge_buffer.clear()
                            ef.flush()
                            
                            # Roll over to new edge file if needed
                            if edge_file_line_count >= MAX_EDGE_FILE_LINES:
                                ef.close()
                                edge_file_index += 1
                                edge_file = os.path.join(edge_dir, f'edges_part_{worker_id:02d}_{edge_file_index:03d}.csv')
                                ef = open(edge_file, 'w', newline='', buffering=CSV_BUFFER_SIZE)
                                edge_writer = csv.writer(ef)
                                edge_writer.writerow(['~from', '~to', '~label:String',
                                                    'eprop1:Int', 'eprop2:Int', 'eprop3:Int', 'eprop4:Int', 'eprop5:Int'])
                                edge_file_line_count = 0
                                print(f"Worker {worker_id}: Rolled over to new edge file {edge_file}")
            
            # Flush remaining buffers
            if vertex_buffer:
                vertex_writer.writerows(vertex_buffer)
            if edge_buffer:
                edge_writer.writerows(edge_buffer)
                
        finally:
            ef.close()

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
    deg_seq = np.round(exp_deg).astype(int)
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

    # Optimize worker count based on available CPUs and disk count
    cpu_count = multiprocessing.cpu_count()
    if args.workers is None:
        # Use 75% of available CPUs by default
        workers = max(1, min(len(available_disks), int(cpu_count * 0.75)))
    else:
        workers = min(args.workers, cpu_count)
    
    # Calculate optimal chunk size (aim for at least 100K vertices per chunk)
    min_chunk_size = 100000
    chunk_size = max(min_chunk_size, (args.nodes + workers - 1) // workers)
    chunks = [(i, min(i + chunk_size, args.nodes)) for i in range(0, args.nodes, chunk_size)]
    
    print(f"\nOptimized configuration:")
    print(f"Workers: {workers} (out of {cpu_count} CPUs)")
    print(f"Chunk size: {chunk_size:,} vertices")
    print(f"Total chunks: {len(chunks)}")

    # Process chunks in parallel
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(process_chunk, start, end, deg_seq, args.seed, args.nodes, worker_id, workers)
            for worker_id, (start, end) in enumerate(chunks)
        ]
        
        # Monitor progress
        completed = 0
        for f in futures:
            f.result()  # Wait for completion and propagate any errors
            completed += 1
            print(f"Progress: {completed}/{len(chunks)} chunks completed ({(completed/len(chunks))*100:.1f}%)")

if __name__ == '__main__':
    main()
