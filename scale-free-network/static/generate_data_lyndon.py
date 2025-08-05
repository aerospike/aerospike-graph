import argparse
import os
import csv
import numpy as np
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import random
from multiprocessing import shared_memory
from time import time

def get_shard_path(base_dir: str, worker_id: int, total_disks: int) -> str:
    disk_number = worker_id % total_disks + 1
    return os.path.join(f"/mnt/data{disk_number}", base_dir)

BATCH_SIZE = 1_000_000
MAX_EDGE_FILE_LINES = 20_000_000

def generate_vertex_id(n: int) -> str:
    return f"A{n:019d}"

def generate_long_property(rng: random.Random) -> int:
    return rng.randint(0, 9223372036854775807)

def generate_edge_property(rng: random.Random) -> int:
    return rng.randint(-2147483648, 2147483647)

def sample_targets(n, u, k, rng):
    targets = set()
    while len(targets) < k:
        v = int(rng.integers(0, n))
        if v != u:
            targets.add(v)
    return list(targets)

def process_full_worker(worker_id, shm_name, shape, dtype, seed, n, total_disks, total_workers):
    existing_shm = shared_memory.SharedMemory(name=shm_name)
    deg_seq = np.ndarray(shape, dtype=dtype, buffer=existing_shm.buf)

    edge_output_dir = get_shard_path("edges", worker_id, total_disks)
    vertex_output_dir = get_shard_path("vertices", worker_id, total_disks)

    os.makedirs(edge_output_dir, exist_ok=True)
    os.makedirs(vertex_output_dir, exist_ok=True)

    edge_buffer = []
    edge_file_index = 0
    edge_file_line_count = 0
    edge_file_path = os.path.join(edge_output_dir, f'edges_part_{worker_id:02d}_{edge_file_index:03d}.csv')
    edge_file = open(edge_file_path, 'w', newline='')
    edge_writer = csv.writer(edge_file)
    edge_writer.writerow(['~from', '~to', '~label',
                          'eprop1:Int', 'eprop2:Int', 'eprop3:Int', 'eprop4:Int', 'eprop5:Int'])

    vertex_buffer = []
    vertex_file_path = os.path.join(vertex_output_dir, f'vertices_part_{worker_id:02d}.csv')
    vertex_file = open(vertex_file_path, 'w', newline='')
    vertex_writer = csv.writer(vertex_file)
    vertex_writer.writerow(['~id', 'outDegree:Int', 'prop1:Long', 'prop2:Long', 'prop3:Long', 'prop4:Long'])

    edges_written = 0
    vertices_written = 0

    for u in range(worker_id, n, total_workers):
        deg = deg_seq[u]

        vertex_id = generate_vertex_id(u)
        vrng = random.Random(seed + u)
        props = [generate_long_property(vrng) for _ in range(4)]
        vertex_buffer.append([vertex_id, deg] + props)
        vertices_written += 1
        if len(vertex_buffer) >= BATCH_SIZE:
            vertex_writer.writerows(vertex_buffer)
            print(f"Worker {worker_id}: Flushed {len(vertex_buffer)} vertices")
            vertex_buffer.clear()

        if deg > 0:
            rng = np.random.default_rng(seed + u)
            for v in sample_targets(n, u, deg, rng):
                erng = random.Random(int(seed + u * n + int(v)))
                row = [
                    generate_vertex_id(u),
                    generate_vertex_id(v),
                    'edge'
                ] + [generate_edge_property(erng) for _ in range(5)]
                edge_buffer.append(row)
                edges_written += 1

                if len(edge_buffer) >= BATCH_SIZE:
                    edge_writer.writerows(edge_buffer)
                    print(f"Worker {worker_id}: Flushed {len(edge_buffer)} edges")
                    edge_file_line_count += len(edge_buffer)
                    edge_buffer.clear()
                    edge_file.flush()

                    if edge_file_line_count >= MAX_EDGE_FILE_LINES:
                        edge_file.close()
                        edge_file_index += 1
                        edge_file_path = os.path.join(edge_output_dir, f'edges_part_{worker_id:02d}_{edge_file_index:03d}.csv')
                        edge_file = open(edge_file_path, 'w', newline='')
                        edge_writer = csv.writer(edge_file)
                        edge_writer.writerow(['~from', '~to', '~label',
                                              'eprop1:Int', 'eprop2:Int', 'eprop3:Int', 'eprop4:Int', 'eprop5:Int'])
                        print(f"Worker {worker_id}: Rolled over to new edge file {edge_file_path}")
                        edge_file_line_count = 0

    if vertex_buffer:
        vertex_writer.writerows(vertex_buffer)
        print(f"Worker {worker_id}: Flushed final {len(vertex_buffer)} vertices")
    vertex_file.close()

    if edge_buffer:
        edge_writer.writerows(edge_buffer)
        print(f"Worker {worker_id}: Flushed final {len(edge_buffer)} edges")
    edge_file.close()

    existing_shm.close()
    print(f"Worker {worker_id}: Wrote {vertices_written} vertices and {edges_written} edges")

def main():
    start = time()

    p = argparse.ArgumentParser()
    p.add_argument('--nodes', type=int, default=100_000)
    p.add_argument('--median', type=float, default=20.0)
    p.add_argument('--sigma', type=float, default=1.0)
    p.add_argument('--workers', type=int, default=None)
    p.add_argument('--disks', type=int, default=24)
    p.add_argument('--seed', type=int, default=0)
    args = p.parse_args()

    workers = args.workers or multiprocessing.cpu_count()
    rng = np.random.default_rng(args.seed)
    mu = np.log(args.median)
    exp_deg = rng.lognormal(mean=mu, sigma=args.sigma, size=args.nodes)
    deg_seq = np.round(exp_deg).astype(np.int32)

    shm = shared_memory.SharedMemory(create=True, size=deg_seq.nbytes)
    shm_array = np.ndarray(deg_seq.shape, dtype=deg_seq.dtype, buffer=shm.buf)
    shm_array[:] = deg_seq[:]

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(process_full_worker, wid, shm.name, deg_seq.shape, deg_seq.dtype.name, args.seed, args.nodes, args.disks, workers)
                   for wid in range(workers)]
        for f in futures:
            f.result()

    shm.close()
    shm.unlink()

    print(f'✔ Wrote {args.nodes} vertices and edges sharded across /mnt/data[1-{args.disks}]')
    print(f'✔ Completed in {(time() - start):.2f} seconds')

if __name__ == '__main__':
    main()