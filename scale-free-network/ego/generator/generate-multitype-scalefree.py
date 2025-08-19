import numpy as np
import worker as gen
import validator
import argparse
import os
import pickle
import tempfile
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import time
import signal
import sys
import atexit


BATCH_SIZE = 1_000_000
MAX_EDGE_FILE_LINES = 20_000_000
CSV_BUFFER_SIZE = 8 * 1024 * 1024
executor = None


def cleanup():
    """Cleanup function to handle shared resources."""
    global executor
    if executor is not None:
        print("\nShutting down workers...", file=sys.stderr)
        executor.shutdown(wait=False)


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
            for fold_name in os.listdir(dir_path):
                folder_path = os.path.join(dir_path, fold_name)
                for file in os.listdir(folder_path):
                    if file.endswith('.csv'):
                        path = os.path.join(folder_path, file)
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


def sample_targets(n, u, k, rng):
    targets = set()
    while len(targets) < k:
        v = int(rng.integers(0, n))
        if v != u:
            targets.add(v)
    return list(targets)


def sample_lognormal_degree(rng, median: float, sigma: float, cap: int = 1_000_000) -> int:
    mu = np.log(median)
    x = rng.lognormal(mean=mu, sigma=sigma)
    return int(min(cap, round(x)))


def dump_pickle(obj, path=None):
    """
    Serialize object to disk using pickle.
    If no path use a secure temp file and return its path.
    """
    if path is None:
        fd, path = tempfile.mkstemp(suffix=".pkl", prefix="aux_payload_")
        os.close(fd)
    with open(path, "wb") as f:
        pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
    return path


def partition_even(total: int, parts: int):
    """
    Evenly partition 'total' items into 'parts' (prefix-heavy remainder).
    Returns a list of (start, count).
    """
    base = total // parts
    rem = total % parts
    partitions = []
    start = 0
    for i in range(parts):
        cnt = base + (1 if i < rem else 0)
        partitions.append((start, cnt))
        start += cnt
    return partitions


def main():
    global executor
    
    # Register cleanup handlers
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    start_time = time.time()

    try:
        p = argparse.ArgumentParser(
            description="Generate log-normal directed graph CSVs with parallelism"
        )
        p.add_argument('--sf', type=int, default=100000,
                       help='Number of ego networks to generate')
        p.add_argument('--workers', type=int, default=None,
                       help='Number of parallel workers (default = CPU count)')
        p.add_argument('--seed', type=int, default=0,
                       help='Base RNG seed for reproducibility')
        p.add_argument('--node-sharing-chance', type=int, default=0,
                       help='Percent chance of the EgoNode being connected to a Alters leaf node '
                            '(Ego->Alter->AlterLeaf ++ Ego->AlterLeaf')
        p.add_argument('--dry-run', action='store_true',
                       help='Only show degree distribution statistics without generating files')
        p.add_argument('--schema', type=str, required=True,
                       help='Path to schema yaml file')
        output_group = p.add_mutually_exclusive_group(required=False)
        output_group.add_argument('--mount', action='store_true',
                                help='Use mounted disks at /mnt/data*')
        output_group.add_argument('--out-dir',
                                help='Output directory for all files')
        args = p.parse_args()
        num_egos = args.sf

        config_path = args.schema
        config = validator.parse_config_yaml(config_path)
        config_flatmap, vert_prop_map, edge_prop_map = validator.parse_config(config)

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

        aux_payload = {
            "config": config_flatmap,
            "edge_properties": edge_prop_map,
            "vertex_properties": vert_prop_map
        }
        aux_path = dump_pickle(aux_payload)
        edges_written = 0
        vertices_written = 0
        parts = partition_even(num_egos, workers)

        with ProcessPoolExecutor(max_workers=workers) as executor_ctx:
            executor = executor_ctx
            futures = []
            total_disks = len(available_disks) if available_disks else workers
            for wid, (start_idx, count) in enumerate(parts):
                if count == 0:
                    continue
                futures.append(
                    executor.submit(
                        gen.process_full_worker,
                        worker_id=wid,
                        aux_path=aux_path,
                        seed=args.seed + wid,     # worker-local seed
                        ego_start=start_idx,
                        ego_count=count,
                        total_disks=total_disks,
                        out_dir=args.out_dir,
                        node_share_chance=args.node_sharing_chance,
                        num_workers=len(parts)
                    )
                )
            
            completed = 0
            for f in futures:
                verts, edges = f.result()
                vertices_written += verts
                edges_written += edges
                completed += 1
                print(f"\nProgress: {completed}/{workers} workers completed ({(completed/workers)*100:.1f}%)")

        total_size, files_count = get_total_file_size(available_disks, args.out_dir)
        if args.mount:
            print(f'\n✔ Files distributed across {len(available_disks)} disks')
        else:
            print(f'\n✔ Files written to {args.out_dir}')
        print(f'✔ Total data written: {get_human_size(total_size)} in {files_count} files')
        print(f'✔ Vertices Written: {vertices_written}')
        print(f'✔ Edges Written: {edges_written}')
        print(f'✔ Completed in {(time.time() - start_time):.2f} seconds')

    except Exception as e:
        print(f"\nError: {str(e)}", file=sys.stderr)
        raise


if __name__ == '__main__':
    main()
