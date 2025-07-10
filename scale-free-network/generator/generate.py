import os
import string
from bisect import bisect_left
from multiprocessing import shared_memory
import numpy as np
import csv
import time
import random

import pickle

BATCH_SIZE = 1_000_000  # Increased to 1M
MAX_EDGE_FILE_LINES = 20_000_000  # Increased to 20M
CSV_BUFFER_SIZE = 1024 * 1024  # MB Buffer

def generate_vertex_id(vtype: string, n: int) -> str:
    """Generate a numeric vertex ID - much faster than alphanumeric."""
    return f"{vtype}{n:019d}"

def generate_long_property(rng: random.Random) -> int:
    return rng.randint(0, 9223372036854775807)

def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_edge_property(rng: random.Random) -> int:
    return rng.randint(0, 2147483647)

def generate_random_property(type):
    type = str(type).lower()
    if type == "int":
        return str(random.randint(0, 2147483647))
    elif type == "double":
        value = random.uniform(0.0, 100000.0)
        return str(round(value, 2))
    elif type == "string":
        return random_string()
    elif type == "date":
        return str(int(time.time() - random.randint(0,31000000)))
    elif type == "long":
        return str(random.randint(0, 9223372036854775807))
    elif type == "bool":
        return str(random.randint(1, 5) == 1)
    else:
        raise ValueError(f"{type} not recognized, use either int, double, string, date, long, or bool")

def generate_line_properties(schema):
    '''Grab types of each, generate random based on type'''
    values = []
    for property in schema:
        type = str(property).split(':')[1]
        values.append(generate_random_property(type))

    return values

def sample_targets(n, u, k, rng):
    targets = set()
    while len(targets) < k:
        v = int(rng.integers(0, n))
        if v != u:
            targets.add(v)
    return list(targets)

def sample_targets_from_pool(pool: np.ndarray, k: int, seed: int):
    rng = np.random.default_rng(seed)
    if k > len(pool):
        raise ValueError("Not enough targets in pool")
    return rng.choice(pool, size=k, replace=False)


def get_shard_path(base_dir: str, worker_id: int, total_disks: int, out_dir: str = None) -> str:
    """Get path for output files. If out_dir is specified, use that, otherwise use mounted disks."""
    if out_dir:
        return os.path.join(out_dir, base_dir)
    disk_number = worker_id % total_disks + 1
    return os.path.join(f"/mnt/data{disk_number}", base_dir)

def process_full_worker(
        worker_id: int,
        shm_name: str,
        shm_shape: tuple[int, int],
        shm_dtype: str,
        aux_path: str,
        seed: int,
        total_nodes: int,
        total_disks: int,
        total_workers: int,
        out_dir: str | None = None) -> None:
    """Process vertices and edges for a worker using shared memory."""
    # Get shared memory array
    payload = pickle.load(open(aux_path, "rb"))
    vertex_ranges = payload["vertex_ranges"]
    vertice_configs = payload["vertice_configs"]
    edge_configs = payload["edge_configs"]
    edge_schemas = payload["edge_schemas"]
    vertice_schemas = payload["vertice_schemas"]
    vertex_idx_mapping = payload["vertex_idx_mapping"]

    shm = shared_memory.SharedMemory(name=shm_name)
    deg_mat = np.ndarray(shm_shape, dtype=np.dtype(shm_dtype), buffer=shm.buf)
    def vertex_type_of(u: int) -> int:
        return bisect_left(vertex_ranges, u+1) - 1
    target_pools = {
        t_idx: np.arange(vertex_ranges[t_idx],
                         vertex_ranges[t_idx+1],
                         dtype=np.int64)
        for t_idx in range(len(vertex_ranges)-1)
    }

    # Setup output directories
    edge_output_dir = get_shard_path("edges", worker_id, total_disks, out_dir)
    vertex_output_dir = get_shard_path("vertices", worker_id, total_disks, out_dir)
    os.makedirs(edge_output_dir, exist_ok=True)
    os.makedirs(vertex_output_dir, exist_ok=True)

    vertex_writers = {}
    for V in vertice_configs:
        fname = f'vertices_{V.name}_{worker_id:02d}.csv'
        path  = get_shard_path("vertices", worker_id, total_disks, out_dir)
        os.makedirs(path, exist_ok=True)
        f = open(os.path.join(path, fname), "w", newline="", buffering=CSV_BUFFER_SIZE)
        w = csv.writer(f);  w.writerow(['~id', 'outDegree:Int'] + vertice_schemas[V.name])
        vertex_writers[vertex_idx_mapping[V.name]] = (w, f, [])      # writer, file handle, in‑mem buffer

    edge_writers = {}
    edge_file_index = 0
    for E in edge_configs:
        edge_file_path = os.path.join(edge_output_dir, f'edges_{E.name}_part_{worker_id:02d}_{edge_file_index:03d}.csv')
        edge_file = open(edge_file_path, 'w', newline='', buffering=CSV_BUFFER_SIZE)
        edge_writer = csv.writer(edge_file)
        edge_writer.writerow(['~from', '~to', '~label'] + edge_schemas[E.name])
        edge_writers[E.index] = (edge_writer, edge_file, [])
        edge_file_index += 1

    def flush_if_needed(buffer: list, idx: int, kind: str):
        if len(buffer) >= BATCH_SIZE:
            if kind == "vertex":
                writer = vertex_writers[idx][0]
            else:
                writer = edge_writers[idx]
            writer.writerows(buffer)
            buffer.clear()
    vertices_written = 0
    edges_written = 0
    # Process vertices in strided fashion
    for u in range(worker_id, total_nodes, total_workers):
        src_type = vertex_type_of(u)
        name = vertice_configs[src_type].name
        vertex_id = generate_vertex_id(name, u)
        # 1) write vertex row
        out_deg = int(deg_mat[u].sum())          # total across edge types
        vbuf = vertex_writers[src_type][2]
        vbuf.append([vertex_id, str(out_deg)] + generate_line_properties(vertice_schemas[name]))
        vertices_written += 1

        flush_if_needed(vbuf, src_type, "vertex") #and write if needed

        # 2) iterate over each edge type that uses this src_type
        edge_file_line_count = 0
        for E in edge_configs:      # pre‑build dict {src_type: [EdgeConf,..]}
            k = deg_mat[u, E.index]
            if k == 0: continue # skip any vert that has no edges
            tgt_ids = sample_targets_from_pool(target_pools[E.to_type_idx], k, seed)
            ebuff = edge_writers[E.index][2]
            efile = edge_writers[E.index][1]
            ewriter = edge_writers[E.index][0]
            name = vertice_configs[E.to_type_idx].name# list associated with edge writer
            for v in tgt_ids:
                ebuff.append([
                                 vertex_id,
                                 generate_vertex_id(name, v),
                                 E.name] +
                             generate_line_properties(edge_schemas[E.name])
                             )
                edges_written += 1
            if len(ebuff) >= BATCH_SIZE:
                ewriter.writerows(ebuff)
                edge_file_line_count += len(ebuff)
                ebuff.clear()
                efile.flush()

                # Roll over edge file if needed
                if edge_file_line_count >= MAX_EDGE_FILE_LINES:
                    efile.close()
                    edge_file_index += 1
                    edge_file_path = os.path.join(edge_output_dir, f'edges_{E.name}_part_{worker_id:02d}_{edge_file_index:03d}.csv')
                    efile = open(edge_file_path, 'w', newline='', buffering=CSV_BUFFER_SIZE)
                    edge_writer = csv.writer(efile)
                    edge_writer.writerow(['~from', '~to', '~label'] + edge_schemas[E.name])
                    edge_writers[E.index] = tuple([edge_writer, efile, ebuff])
                    edge_file_line_count = 0
    for vert_tuple in vertex_writers:
        buffer = vertex_writers[vert_tuple][2]
        file = vertex_writers[vert_tuple][1]
        writer = vertex_writers[vert_tuple][0]
        if buffer: #buffer
            writer.writerows(buffer)
        if file:
            file.close()
    for edge_tuple in edge_writers:
        buffer = edge_writers[edge_tuple][2]
        file = edge_writers[edge_tuple][1]
        writer = edge_writers[edge_tuple][0]
        if buffer: #buffer
            writer.writerows(buffer)
        if file:
            file.close()
    shm.close()
    print(f"Worker {worker_id:02d}: 100% complete - vertices_written vertices, edges_written edges")