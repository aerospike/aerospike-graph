"""
Generate a directed graph whose out-degree sequence follows a power law distribution,
and export vertices and edges in Aerospike Graph bulk-loader CSV format, with parallelism.

If you want to specify the schema, in config/config.yaml edit the edges and vertices values.
Explanations for each property and name are in the DynamicGenerator.md file

Usage:
    python generate-multiple-scalefree.py \
        --nodes 100000 \
        --workers 8 \
        --out-dir output \
        --seed 42 \
        -- dry-run
"""

# add check that the config and schemas are both size >0
import argparse
import os
import pickle
import tempfile

import numpy as np
import yaml
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from multiprocessing import shared_memory
import time
import signal
import sys
import atexit
import generate as gen

BATCH_SIZE = 1_000_000
MAX_EDGE_FILE_LINES = 20_000_000
CSV_BUFFER_SIZE = 8 * 1024 * 1024

# Global variables for cleanup
shared_mem = None
executor = None

class EdgeConf:
    def __init__(self, name, rel_key, from_type_idx, to_type_idx, median, sigma, index, properties):
        self.name = name
        self.rel_key = rel_key
        self.from_type_idx = from_type_idx
        self.to_type_idx = to_type_idx
        self.median = median
        self.sigma = sigma
        self.index = index
        self.properties = properties

class VertexConf:
    def __init__(self, name, count, index, properties):
        self.name = name
        self.count = count
        self.index = index
        self.properties = properties

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

def get_human_size(size_bytes):
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def get_total_file_size(available_disks=None, out_dir=None):
    """Calculate total size of all generated files."""
    total_size = 0
    files_count = 0
    
    def process_dir(dir_path):
        nonlocal total_size, files_count
        if os.path.exists(dir_path):
            for f in os.listdir(dir_path):
                if f.endswith('.csv'):
                    path = os.path.join(dir_path, f)
                    total_size += os.path.getsize(path)
                    files_count += 1
    
    if out_dir:
        process_dir(os.path.join(out_dir, "vertices"))
        process_dir(os.path.join(out_dir, "edges"))
    else:
        for disk in available_disks:
            process_dir(f"/mnt/data{disk}/vertices")
            process_dir(f"/mnt/data{disk}/edges")
    
    return total_size, files_count

def parse_config_yaml(config_path: str) -> dict[str, dict[str, any]]:
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)
AEROSPIKE_GRAPH_TYPES = {
    "long", "int", "integer", "double", "bool", "boolean", "string", "date"
}
def validate_aerospike_properties(properties, type, sub_type):
    for prop in properties:
        val = prop.lower()
        if ':' not in val:
            raise ValueError(f"Invalid {type} property definition for {type} '{sub_type}': '{prop}': missing ':' separator.")
        name, type_str = val.split(':', 1)
        name = name.strip()
        type_str = type_str.strip()
        if not name:
            raise ValueError(f"Invalid {type} {sub_type} property definition '{prop}': property name is empty.")
        if not type_str:
            raise ValueError(f"Invalid {type} {sub_type} property definition '{prop}': property type is empty.")
        if type_str not in AEROSPIKE_GRAPH_TYPES:
            raise ValueError(
                f"Invalid {type} property type '{type_str}' for property '{name}' in {sub_type} {type}. "
                f"Supported types are: {sorted(AEROSPIKE_GRAPH_TYPES)}"
            )
    return True

def parse_edge_config(config, vertex_idx_mapping):
    result = []
    i = 0
    for edge_type, edge_groups in config.items():
        for rel_key, props in edge_groups.items():
            properties = props['properties']
            if properties == None:
                properties = []
            if not isinstance(properties, list):
                raise ValueError(f"Edge properties are not a list: '{properties}'")
            validate_aerospike_properties(properties, "Edge", edge_type)
            entry = EdgeConf(
                name=edge_type,
                rel_key=rel_key,# The edge label for the graph
                from_type_idx=vertex_idx_mapping[props['from']],
                to_type_idx=vertex_idx_mapping[props['to']],
                properties=properties,
                median=float(props['median']),
                sigma=float(props['sigma']),
                index=i
            )
            result.append(entry)
            i += 1
    return result

def parse_vert_config(config, nodes):
    result = []
    i = 0
    total_percent = 0
    for name, props in config.items():
        properties = props['properties']
        total_percent += props['percent']
        if not isinstance(properties, list):
            raise ValueError(f"Vertex properties are not a list: '{properties}'")
        validate_aerospike_properties(properties, "Vertex", name)
        entry = VertexConf(
            name = name,
            count = int(nodes * (props['percent'] / 100)),
            index=i,
            properties = properties
        )
        result.append(entry)
        i += 1
    if not(total_percent == 100):
        raise ValueError(f"Vertex percents do not add up to 100: '{total_percent}'%")
    return result

def sample_log_normal_deg(N, median, sigma, rng):
    mu = np.log(median)
    degs = rng.lognormal(mean=mu, sigma=sigma, size=N)
    return degs.astype(int)

def sample_sequence_powerlaw(n, gamma, seed=None):
    """
    Sample `n` integer degrees from a discrete power-law (Zipf) distribution:
      P(k) ∝ k⁻ᵞ  for k = 1,2,3,…

    Args:
        n      (int):   number of samples (vertices)
        gamma  (float): exponent α > 1
        seed   (int):   RNG seed (optional)

    Returns:
        np.ndarray of shape (n,), dtype=int
    """
    rng = np.random.default_rng(seed)
    # Raw Zipf samples (values ≥1), heavy tail
    degs = rng.zipf(gamma, size=n)
    # Cap at n–1 so we never exceed the number of other vertices
    max_possible = n - 1
    degs = np.minimum(degs, max_possible)
    return degs

import powerlaw
import matplotlib.pyplot as plt

def print_degree_distribution(deg_seq: np.ndarray, distribution: str = "lognormal", num_bins: int = 20):
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

    print(f"\n {distribution} Distribution Histogram:")
    if distribution == "lognormal":
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
    else:
        bins = np.linspace(min_deg, max_deg + 1, num_bins).astype(int)
        hist, bin_edges = np.histogram(deg_seq, bins=bins)
        max_count = np.max(hist)
        for count, bin_start, bin_end in zip(hist, bin_edges[:-1], bin_edges[1:]):
            if count > 0:
                bar_len = int((count / max_count) * 50)
                percentage = (count / len(deg_seq)) * 100
                print(f"{bin_start:6} - {bin_end:6} | {'*' * bar_len} ({count:,} vertices, {percentage:.1f}%)")


def validate_and_plot_powerlaw(deg_seq: np.ndarray, plot_title="Degree Distribution", show_plot=True):
    # Filter out 0s (not part of power-law support)
    deg_seq = deg_seq[deg_seq > 0]

    print("\n[Power-Law Validation]")
    print(f"Sample size: {len(deg_seq):,}")
    print(f"Min degree: {deg_seq.min()}, Max degree: {deg_seq.max()}")

    fit = powerlaw.Fit(deg_seq, discrete=True)
    gamma = fit.power_law.alpha
    xmin = fit.power_law.xmin
    D = fit.power_law.D
    print(f"Estimated gamma (α): {gamma:.2f}")
    print(f"Estimated xmin: {xmin}")
    print(f"KS distance: {D:.4f}")

    R, p = fit.distribution_compare('power_law', 'lognormal')
    print(f"Power-law vs Log-normal loglikelihood ratio: R = {R:.3f}, p = {p:.4f}")
    if R > 0 and p < 0.05:
        print("✔ Power-law is a significantly better fit")
    elif R < 0 and p < 0.05:
        print("✘ Log-normal is a better fit")
    else:
        print("❓ Inconclusive: not enough evidence to favor one model")

    if show_plot:
        plt.figure(figsize=(8, 6))
        fit.plot_pdf(color='b', label='Empirical PDF')
        fit.power_law.plot_pdf(color='r', linestyle='--', label='Fitted Power-law')
        plt.title(plot_title)
        plt.xlabel("Degree k")
        plt.ylabel("P(k)")
        plt.legend()
        plt.grid(True, which="both", ls=":")
        plt.show()

def sample_targets(n, u, k, rng):
    targets = set()
    while len(targets) < k:
        v = int(rng.integers(0, n))
        if v != u:
            targets.add(v)
    return list(targets)

def dump_pickle(obj, path=None):
    """
    Serialize object to disk using pickle.
    If no path use a secure temp file and return its path.
    """
    if path is None:
        fd, path = tempfile.mkstemp(suffix=".pkl", prefix="aux_payload_")
        os.close(fd)  # We just want the name, will open with pickle
    with open(path, "wb") as f:
        pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
    return path

def main():
    global shared_mem, executor
    
    # Register cleanup handlers
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    start_time = time.time()

    try:
        p = argparse.ArgumentParser(
            description="Generate log-normal directed graph CSVs with parallelism"
        )
        p.add_argument('--nodes', type=int, default=100000,
                       help='Number of vertices')
        p.add_argument('--workers', type=int, default=None,
                       help='Number of parallel workers (default = CPU count)')
        p.add_argument('--seed', type=int, default=0,
                       help='Base RNG seed for reproducibility')
        p.add_argument('--gamma', type=float, default=2.5,
                       help='Gamma for power-law generation')
        p.add_argument('--dry-run', action='store_true',
                       help='Only show degree distribution statistics without generating files')
        p.add_argument('--validate-distribution', action='store_true',
                       help='Runs a function to see the fit between lognormal and powerlaw')
        output_group = p.add_mutually_exclusive_group(required=False)
        output_group.add_argument('--mount', action='store_true',
                                help='Use mounted disks at /mnt/data*')
        output_group.add_argument('--out-dir',
                                help='Output directory for all files')
        args = p.parse_args()
        nodes = args.nodes

        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config','config.yaml')
        config = parse_config_yaml(config_path)
        vertice_configs = parse_vert_config(config.get('vertices', {}), nodes)

        vertex_ranges = [0]
        running_count = 0
        for conf in vertice_configs:
            vertex_ranges.append(vertex_ranges[-1] + conf.count)

        # Precompute Arrays
        vertex_type_idx = np.zeros(nodes, dtype=np.uint16)
        vertex_idx_mapping = {}
        vertex_local_idx = np.zeros(nodes, dtype=np.int64)
        for i, t in enumerate(vertice_configs):
            start, end = vertex_ranges[i], vertex_ranges[i+1]
            vertex_type_idx[start:end] = i
            vertex_local_idx[start:end] = np.arange(end - start)
            vertex_idx_mapping[t.name] = i

        edge_configs = parse_edge_config(config.get('edges', {}), vertex_idx_mapping)

        # Sparse COO tensor: (src_global_id, edge_type_index, degree)
        degree_records = []
        rng = np.random.default_rng(1234)
        for E in edge_configs:
            src_type = E.from_type_idx
            start, end = vertex_ranges[src_type], vertex_ranges[src_type+1]
            N_src = end - start
            degs = sample_sequence_powerlaw(
                N_src,
                gamma=args.gamma,
                seed=args.seed
            )
            for i, d in enumerate(degs):
                degree_records.append((start + i, E.index, d))
        degree_tensor = np.zeros((nodes, len(edge_configs)), dtype=np.int32)
        for u, eidx, d in degree_records:
            degree_tensor[u, eidx] = d

        # 6. Build target pools for each vertex type
        target_pools = []
        for t in vertice_configs:
            start, end = vertex_ranges[vertex_idx_mapping[t.name]], vertex_ranges[vertex_idx_mapping[t.name] + 1]
            pool = np.arange(start, end)
            target_pools.append(pool)

        # Sum across all edge-types to get each vertex’s total out-degree
        degree_sequence = degree_tensor.sum(axis=1)
        print_degree_distribution(degree_sequence)
        if(args.validate_distribution):
            validate_and_plot_powerlaw(degree_sequence)

        if args.dry_run:
            print("\n✔ Dry run completed. No files were generated.")
            return

        # Handle output location
        available_disks = None
        if args.mount:
            available_disks = [i for i in range(1, 25) if os.path.ismount(f"/mnt/data{i}")]
            if not available_disks:
                raise RuntimeError("No mounted disks found in /mnt/data*. Please run mount_disks.sh first.")
            print(f"\nFound {len(available_disks)} mounted disks: {', '.join(f'/mnt/data{i}' for i in available_disks)}")
        else:
            os.makedirs(args.out_dir, exist_ok=True)
            print(f"\nOutput directory: {args.out_dir}")

        # Setup shared memory for degree sequence
        tensor_bytes = degree_tensor.nbytes
        deg_shm = shared_memory.SharedMemory(create=True, size=tensor_bytes)
        np.ndarray(degree_tensor.shape, degree_tensor.dtype, deg_shm.buf)[:] = degree_tensor

        # Pickle useful data
        aux_payload = {
            "vertex_ranges": vertex_ranges,
            "edge_configs": edge_configs,
            "vertice_configs": vertice_configs,
            "vertex_idx_mapping": vertex_idx_mapping
        }
        aux_path = dump_pickle(aux_payload)

        # Optimize worker count
        cpu_count = multiprocessing.cpu_count()
        if args.workers is None:
            if args.mount:
                workers = max(1, min(len(available_disks), cpu_count))
            else:
                workers = max(1, min(8, cpu_count))  # Default to 8 workers for single directory
        else:
            workers = min(args.workers, cpu_count)

        print(f"\nOptimized configuration:")
        print(f"Workers: {workers} (out of {cpu_count} CPUs)")
        print(f"Batch size: {BATCH_SIZE:,}")
        print(f"Edge file size: {MAX_EDGE_FILE_LINES:,}") #need to be updated
        # Process in parallel
        with ProcessPoolExecutor(max_workers=workers) as executor_ctx:
            executor = executor_ctx  # Store for cleanup
            futures = [
                executor.submit(
                    gen.process_full_worker,
                    wid,
                    deg_shm.name,
                    degree_tensor.shape,
                    degree_tensor.dtype.name,
                    aux_path,
                    args.seed, args.nodes,
                    len(available_disks) if available_disks else workers,
                    workers,
                    args.out_dir
                )
                for wid in range(workers)
            ]
            
            completed = 0
            for f in futures:
                f.result()
                completed += 1
                print(f"\nProgress: {completed}/{workers} workers completed ({(completed/workers)*100:.1f}%)")

        # Normal cleanup
        executor = None
        if(shared_mem):
            shared_mem.close()
            shared_mem.unlink()
        shared_mem = None

        total_edges = np.sum(degree_tensor)
        total_size, files_count = get_total_file_size(available_disks, args.out_dir)
        
        print(f'\n✔ Generated graph with {args.nodes:,} vertices and {total_edges:,} edges')
        if args.mount:
            print(f'✔ Files distributed across {len(available_disks)} disks')
        else:
            print(f'✔ Files written to {args.out_dir}')
        print(f'✔ Total data written: {get_human_size(total_size)} in {files_count} files')
        print(f'✔ Completed in {(time.time() - start_time):.2f} seconds')

    except Exception as e:
        print(f"\nError: {str(e)}", file=sys.stderr)
        raise

if __name__ == '__main__':
    main()
