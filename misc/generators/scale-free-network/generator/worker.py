import calendar
import datetime
import os
from bisect import bisect_left
from multiprocessing import shared_memory
import numpy as np
import csv
import random

import pickle

BATCH_SIZE = 1_000_000  # Increased to 1M
MAX_EDGE_FILE_LINES = 20_000_000  # Increased to 20M
CSV_BUFFER_SIZE = 1024 * 1024  # MB Buffer

def generate_vertex_id(vtype: str, n: int) -> str:
    """Generate a numeric vertex ID - much faster than alphanumeric."""
    return f"{vtype}{n:019d}"

def generate_int(rng: random.Random, props: dict) -> int:
    minimum = props["min"]
    maximum = props["max"]
    return rng.randint(minimum, maximum)


def generate_long(rng: random.Random, props: dict) -> int:
    minimum = props["min"]
    maximum = props["max"]
    return rng.randint(minimum, maximum)


def generate_double(rng: random.Random, props: dict) -> float:
    minimum = props["min"]
    maximum = props["max"]
    return rng.uniform(minimum, maximum)


def generate_string(rng: random.Random, props: dict) -> str:
    min_size = props["min_size"]
    max_size = props["max_size"]
    allowed = props["allowed_chars"]
    length = rng.randint(min_size, max_size)
    return "".join(rng.choice(allowed) for _ in range(length))


def generate_bool(rng: random.Random, props: dict) -> bool:
    chance = props["true_chance"] / 100.0
    return rng.random() < chance


def generate_date(rng: random.Random, props: dict) -> str:
    min_year = props["min_year"]
    max_year = props["max_year"]
    year = rng.randint(min_year, max_year)
    month = rng.randint(1, 12)
    day = rng.randint(1, calendar.monthrange(year, month)[1])
    randdate = datetime.date(year, month, day)
    return randdate.isoformat()


def generate_list(rng: random.Random, props: dict):
    min_len = props["min_length"]
    max_len = props["max_length"]
    element = props["element"]
    element_type = element["type"]
    length = rng.randint(min_len, max_len)
    return [
        generate_property(element_type, rng, element)
        for _ in range(length)
    ]


def generate_property(type_name: str, rng: random.Random, props: dict):
    dispatch = {
        "int":    generate_int,
        "integer":    generate_int,
        "long":   generate_long,
        "double": generate_double,
        "string": generate_string,
        "bool":   generate_bool,
        "boolean":   generate_bool,
        "date":   generate_date,
        "list":   generate_list,
    }
    try:
        gen = dispatch[type_name.lower()]
    except KeyError:
        raise ValueError(f"Unsupported type '{type_name}'")
    return gen(rng, props)

def generate_line_properties(schema, rng):
    '''Grab types of each, generate random based on type'''
    values = []
    for type, props in schema.items():
        values.append(generate_property(props["type"], rng, props))

    return values

def get_property_list(props: dict) -> list:
    prop_list = []
    for key, value in props.items():
        prop_type = value["type"].lower()
        if prop_type == "list":
            element_type = value["element"]["type"].lower()
            prop_list.append(key + ":" + element_type + ":" + prop_type)
        else:
            prop_list.append(key + ":" + prop_type)
    return prop_list

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
        print("ERROR: Not enough targets in pool, defaulting to using whole pool")
        return rng.choice(pool, size=len(pool), replace=False)
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
    # Get shared memory array
    payload = pickle.load(open(aux_path, "rb"))
    vertex_ranges = payload["vertex_ranges"]
    vertice_configs = payload["vertice_configs"]
    edge_configs = payload["edge_configs"]
    vertex_idx_mapping = payload["vertex_idx_mapping"]

    rng = random.Random(1234)
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
        vertex_subdir = os.path.join(get_shard_path("vertices", worker_id, total_disks, out_dir), V.name)
        os.makedirs(vertex_subdir, exist_ok=True)
        fname = f'vertices_{V.name}_{worker_id:02d}.csv'
        vprop_list = []
        for key, props in V.properties.items():
            vprop_list.append(key + ":" + props["type"])
        f = open(os.path.join(vertex_subdir, fname), "w", newline="", buffering=CSV_BUFFER_SIZE)
        w = csv.writer(f);  w.writerow(['~id', 'outDegree:Int'] + get_property_list(V.properties))
        vertex_writers[vertex_idx_mapping[V.name]] = (w, f, []) # writer, file handle, in‑mem buffer

    edge_writers = {}
    edge_file_index = 0
    for E in edge_configs:
        edge_subdir = os.path.join(get_shard_path("edges", worker_id, total_disks, out_dir), E.rel_key)
        os.makedirs(edge_subdir, exist_ok=True)
        edge_file_path = os.path.join(edge_subdir, f'edges_{E.rel_key}_part_{worker_id:02d}_{edge_file_index:03d}.csv')
        edge_file = open(edge_file_path, 'w', newline='', buffering=CSV_BUFFER_SIZE)
        edge_writer = csv.writer(edge_file)
        edge_writer.writerow(['~from', '~to', '~label'] + get_property_list(E.properties))
        edge_writers[E.index] = (edge_writer, edge_file, [])
        edge_file_index += 1

    def flush_if_needed(buffer: list, idx: int, kind: str):
        if len(buffer) >= BATCH_SIZE:
            if kind == "vertex":
                writer = vertex_writers[idx][0]
            else:
                writer = edge_writers[idx][0]
            writer.writerows(buffer)
            buffer.clear()
    vertices_written = 0
    edges_written = 0
    # Process vertices in strided fashion
    for u in range(worker_id, total_nodes, total_workers):
        src_type = vertex_type_of(u)
        name = vertice_configs[src_type].name
        vertex_id = generate_vertex_id(name, u)
        out_deg = int(deg_mat[u].sum())          # total across edge types
        vbuf = vertex_writers[src_type][2]
        vbuf.append([vertex_id, str(out_deg)] + generate_line_properties(vertice_configs[vertex_idx_mapping.get(name)].properties, rng))
        vertices_written += 1

        flush_if_needed(vbuf, src_type, "vertex") #and write if needed

        edge_file_line_count = 0
        for E in edge_configs:
            k = deg_mat[u, E.index]
            if k == 0: continue
            tgt_ids = sample_targets_from_pool(target_pools[E.to_type_idx], k, seed)
            ebuff = edge_writers[E.index][2]
            efile = edge_writers[E.index][1]
            ewriter = edge_writers[E.index][0]
            name = vertice_configs[E.to_type_idx].name
            for v in tgt_ids:
                ebuff.append([
                                 vertex_id,
                                 generate_vertex_id(name, v),
                                 E.name] +
                             generate_line_properties(E.properties, rng)
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
                    edge_file_path = os.path.join(edge_output_dir, f'edges_{E.rel_key}_part_{worker_id:02d}_{edge_file_index:03d}.csv')
                    efile = open(edge_file_path, 'w', newline='', buffering=CSV_BUFFER_SIZE)
                    edge_writer = csv.writer(efile)
                    edge_writer.writerow(['~from', '~to', '~label'] + generate_line_properties(E.properties, rng))
                    edge_writers[E.index] = tuple([edge_writer, efile, ebuff])
                    edge_file_line_count = 0
    for vert_tuple in vertex_writers:
        buffer = vertex_writers[vert_tuple][2]
        file = vertex_writers[vert_tuple][1]
        writer = vertex_writers[vert_tuple][0]
        if buffer:
            writer.writerows(buffer)
        if file:
            file.close()
    for edge_tuple in edge_writers:
        buffer = edge_writers[edge_tuple][2]
        file = edge_writers[edge_tuple][1]
        writer = edge_writers[edge_tuple][0]
        if buffer:
            writer.writerows(buffer)
        if file:
            file.close()
    shm.close()
    print(f"Worker {worker_id:02d}: 100% complete - {vertices_written} vertices, {edges_written} edges")