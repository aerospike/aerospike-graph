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

BATCH_SIZE = 10000
MAX_EDGE_FILE_LINES = 1000000  # 1M lines per file

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

def get_next_disk(disk_iterator):
    """Get the next disk in round-robin fashion."""
    try:
        return next(disk_iterator)
    except StopIteration:
        return None

def process_chunk(start: int, end: int, deg_seq: np.ndarray, seed: int, n: int, out_dirs: list):
    """Process a chunk of vertices and generate their edges."""
    # Create iterators for round-robin disk selection
    vertex_disk_iter = itertools.cycle(out_dirs)
    edge_disk_iter = itertools.cycle(out_dirs)
    
    # Initialize counters and buffers
    vertex_buffer = []
    edge_buffer = []
    edge_file_line_count = 0
    edge_file_index = 0
    
    # Open initial vertex file
    current_vertex_disk = get_next_disk(vertex_disk_iter)
    vertex_file = os.path.join(current_vertex_disk, 'vertices', f'vertices_part_{start:08d}_{end:08d}.csv')
    os.makedirs(os.path.dirname(vertex_file), exist_ok=True)
    vf = open(vertex_file, 'w', newline='')
    vertex_writer = csv.writer(vf)
    vertex_writer.writerow(['~id', 'outDegree:Int', 'prop1:Long', 'prop2:Long', 'prop3:Long', 'prop4:Long'])
    
    # Open initial edge file
    current_edge_disk = get_next_disk(edge_disk_iter)
    edge_file = os.path.join(current_edge_disk, 'edges', f'edges_part_{start:08d}_{edge_file_index:03d}.csv')
    os.makedirs(os.path.dirname(edge_file), exist_ok=True)
    ef = open(edge_file, 'w', newline='')
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
                print(f"Chunk {start}-{end}: Flushed {len(vertex_buffer)} vertices to {vertex_file}")
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
                        print(f"Chunk {start}-{end}: Flushed {len(edge_buffer)} edges to {edge_file}")
                        edge_file_line_count += len(edge_buffer)
                        edge_buffer.clear()
                        ef.flush()
                        
                        # Roll over to new edge file if needed
                        if edge_file_line_count >= MAX_EDGE_FILE_LINES:
                            ef.close()
                            edge_file_index += 1
                            current_edge_disk = get_next_disk(edge_disk_iter)
                            edge_file = os.path.join(current_edge_disk, 'edges', 
                                                   f'edges_part_{start:08d}_{edge_file_index:03d}.csv')
                            os.makedirs(os.path.dirname(edge_file), exist_ok=True)
                            ef = open(edge_file, 'w', newline='')
                            edge_writer = csv.writer(ef)
                            edge_writer.writerow(['~from:String', '~to:String', '~label:String',
                                                'eprop1:Int', 'eprop2:Int', 'eprop3:Int', 'eprop4:Int', 'eprop5:Int'])
                            edge_file_line_count = 0
                            print(f"Chunk {start}-{end}: Rolled over to new edge file {edge_file}")
        
        # Flush remaining buffers
        if vertex_buffer:
            vertex_writer.writerows(vertex_buffer)
        if edge_buffer:
            edge_writer.writerows(edge_buffer)
            
    finally:
        vf.close()
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
    p.add_argument('--out_dirs', type=str, default='data',
                   help='Comma-separated list of output directories (for multiple disks)')
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

    # Parse output directories
    out_dirs = [d.strip() for d in args.out_dirs.split(',')]
    print(f"\nWriting to {len(out_dirs)} output directories: {out_dirs}")

    # Set up parallel processing
    workers = args.workers or multiprocessing.cpu_count()
    chunk_size = (args.nodes + workers - 1) // workers
    chunks = [(i, min(i + chunk_size, args.nodes)) for i in range(0, args.nodes, chunk_size)]

    # Process chunks in parallel
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(process_chunk, start, end, deg_seq, args.seed, args.nodes, out_dirs)
            for start, end in chunks
        ]
        for f in futures:
            f.result()  # Wait for completion and propagate any errors

    print(f"✔ Generated graph with {args.nodes} vertices and {sum(deg_seq)} edges")
    print(f"✔ Files written across directories: {', '.join(out_dirs)}")

if __name__ == '__main__':
    main()
