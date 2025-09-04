import shutil
from tqdm.auto import tqdm
import numpy as np
import worker as gen
import validator
import argparse
import os
from pathlib import Path
import pickle
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import time
import signal
import sys
import atexit
from typing import List, Tuple

BATCH_SIZE = 1_000_000
MAX_EDGE_FILE_LINES = 20_000_000
CSV_BUFFER_SIZE = 8 * 1024 * 1024
executor = None
_AUX_PATH = None

def cleanup():
    """Cleanup function to handle shared resources."""
    global executor
    if executor is not None:
        print("\nShutting down workers...", file=sys.stderr)
        executor.shutdown(wait=False)
    try:
        os.remove(_AUX_PATH)
    except OSError:
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

def _run_chunk(worker_slot, *, aux_path, seed, ego_start, ego_count, total_disks, out_dir,
               node_share_chance, num_workers, invert_direction):
    verts, edges = gen.process_full_worker(
        worker_id=worker_slot,
        aux_path=aux_path,
        seed=seed,
        ego_start=ego_start,
        ego_count=ego_count,
        total_disks=total_disks,
        out_dir=out_dir,
        node_share_chance=node_share_chance,
        num_workers=num_workers,
        invert_direction=invert_direction
    )
    return verts, edges, ego_count


def partition_chunks(num_egos: int, target_chunks: int, chunk_size: int) -> List[Tuple[int, int]]:
    if target_chunks and target_chunks > 0:
        chunk_size = max(1, (num_egos + target_chunks - 1) // target_chunks)
    else:
        chunk_size = max(1, chunk_size)

    chunks = []
    start = 0
    while start < num_egos:
        cnt = min(chunk_size, num_egos - start)
        chunks.append((start, cnt))
        start += cnt

    print(f"\nOver-partitioning into {len(chunks)} chunks of ~{chunk_size:,} egos each")
    return chunks


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
        p.add_argument('--invert-direction', action='store_true',
                       help='Changes the generation algorithms direction from out to in vertices from the ego node')
        p.add_argument('--schema', type=str, required=True,
                       help='Path to schema yaml file')
        p.add_argument('--chunk-size', type=int, default=50_000,
                       help='Number of egos per task chunk (smaller = more over-partitioning)')
        p.add_argument('--target-chunks', type=int, default=None,
                       help='Desired number of chunks (overrides --chunk-size if set)')
        output_group = p.add_mutually_exclusive_group(required=False)
        output_group.add_argument('--mount', action='store_true',
                                help='Use mounted disks at /mnt/data*')
        output_group.add_argument('--out-dir',
                                help='Output directory for all files')
        args = p.parse_args()
        num_egos = args.sf
        base_dir = Path(__file__).resolve().parent.parent

        config_path = args.schema
        config = validator.parse_config_yaml(config_path)
        config_flatmap, vert_prop_map, edge_prop_map = validator.parse_config(config, args.invert_direction)

        if args.dry_run:
            print("\n✔ Dry run completed. No files were generated.")
            return

        # Handle output location
        available_disks = None
        out_dir = None
        if args.mount:
            available_disks = [i for i in range(1, 25) if os.path.ismount(f"/mnt/data{i}")]
            if not available_disks:
                raise RuntimeError("No mounted disks found in /mnt/data*. Please run mount_disks.sh first.")
            print(f"\nFound {len(available_disks)} mounted disks: {', '.join(f'/mnt/data{i}' for i in available_disks)}")
        else:
            if args.out_dir is not None:
                os.makedirs(args.out_dir, exist_ok=True)
                out_dir = args.out_dir
                print(f"\nOutput directory: {args.out_dir}")
            else:
                out_dir = base_dir / "output"
                out_dir.mkdir(parents=True, exist_ok=True)
                print(f"\nOutput directory: {out_dir}")
            if os.path.exists(out_dir):
                shutil.rmtree(out_dir)

        # Optimize worker count
        cpu_count = multiprocessing.cpu_count()
        if args.workers is None:
            if args.mount:
                workers = max(1, min(len(available_disks), cpu_count))
            else:
                workers = max(1, min(8, cpu_count)) # Default to 8 workers for single directory
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
        _AUX_PATH = dump_pickle(aux_payload)

        chunks = partition_chunks(num_egos, args.target_chunks, args.chunk_size)
        total_chunks = len(chunks)

        vertices_written = 0
        edges_written = 0

        with ProcessPoolExecutor(max_workers=workers) as executor_ctx:
            executor = executor_ctx
            total_disks = len(available_disks) if available_disks else workers

            future_to_chunk = {}
            for idx, (ego_start, ego_count) in enumerate(chunks):
                worker_slot = idx % workers  # spreads any worker-id-based routing deterministically
                future = executor.submit(
                    _run_chunk,
                    idx,
                    aux_path=_AUX_PATH,
                    seed=np.random.default_rng(args.seed + worker_slot),
                    ego_start=ego_start,
                    ego_count=ego_count,
                    total_disks=total_disks,
                    out_dir=out_dir,
                    node_share_chance=args.node_sharing_chance,
                    num_workers=total_chunks,
                    invert_direction=args.invert_direction
                )
                future_to_chunk[future] = (ego_start, ego_count)

            # Progress bar updates when each chunk finishes
            with tqdm(total=num_egos, unit="ego", smoothing=0.05, dynamic_ncols=True) as pbar:
                completed_chunks = 0
                for f in as_completed(future_to_chunk):
                    verts, edges, processed = f.result()
                    vertices_written += verts
                    edges_written += edges
                    pbar.update(processed)
                    completed_chunks += 1

        print(f"\n✔ Vertices Written: {vertices_written}")
        print(f"✔ Edges Written: {edges_written}")

        total_size, files_count = get_total_file_size(available_disks, out_dir)
        if args.mount:
            print(f'\n✔ Files distributed across {len(available_disks)} disks')
        else:
            print(f'\n✔ Files written to {out_dir}')
        print(f'✔ Total data written: {get_human_size(total_size)} in {files_count} files')
        print(f'✔ Vertices Written: {vertices_written}')
        print(f'✔ Edges Written: {edges_written}')
        print(f'✔ Completed in {(time.time() - start_time):.2f} seconds')

    except Exception as e:
        print(f"\nError: {str(e)}", file=sys.stderr)
        raise


if __name__ == '__main__':
    main()
