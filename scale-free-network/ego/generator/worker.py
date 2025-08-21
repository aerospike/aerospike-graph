import os
import string
from typing import Dict, Tuple, Any, List, Optional
from collections import defaultdict
import numpy as np
import csv
import random
import pickle
BATCH_SIZE = 2_000_000
MAX_EDGE_FILE_LINES = 100
CSV_BUFFER_SIZE = 1024 * 1024

def generate_vertex_id(vtype: string, n: int) -> str:
    """Generate a numeric vertex ID - much faster than alphanumeric."""
    return f"{vtype}{n:019d}"


def generate_line_properties(schema, rng):
    """Grabs types of each, returns generated random values based on type"""
    values = []
    for name, props in (schema or {}).items():
        value = props.get("generator")()
        values.append(value)

    return values

def get_property_header_list(props: dict) -> list:
    """Returns properties header"""
    prop_list = []
    for key, value in (props or {}).items():
        prop_type = value["type"].lower()
        if prop_type == "list":
            element_type = value["element_type"].lower()
            prop_list.append(key + ":" + element_type + ":" + prop_type)
        else:
            prop_list.append(key + ":" + prop_type)
    return prop_list


def _edge_label(src_type: str, dst_type: str, conn_meta: Dict[str, Any], invert_direction: bool) -> str:
    if invert_direction:
        return conn_meta.get("edge_label") or conn_meta.get("type") or f"REL_{dst_type.upper()}_TO_{src_type.upper()}"
    else:
        return conn_meta.get("edge_label") or conn_meta.get("type") or f"REL_{src_type.upper()}_TO_{dst_type.upper()}"


def _sample_degree(meta: Dict[str, any], rng_np: np.random.Generator) -> int:
    """Returns random int degree always >= 0, defaulted to uniform"""
    if meta is None:
        return 0
    median = float(meta.get("median", 1))
    sigma = float(meta.get("sigma", 0.5))
    low, high = median - sigma, median + sigma
    x = rng_np.uniform(low, high)
    return int(round(x))


def _shard_root(base: str, worker_id: int, total_disks: int, out_dir: Optional[str]) -> str:
    if out_dir:
        return os.path.join(out_dir, base)
    disk_no = worker_id % total_disks + 1
    return os.path.join(f"/mnt/data{disk_no}", base)


def _open_vertex_writer(root: str, label: str, props: Dict[str, Any], wid: int):
    path = os.path.join(root, label)
    os.makedirs(path, exist_ok=True)
    f = open(os.path.join(path, f"vertices_part_{wid}_{label}_000.csv"),
             "w", newline="", buffering=CSV_BUFFER_SIZE)
    w = csv.writer(f)
    w.writerow(["~id", "~label"] + get_property_header_list(props))
    return {"file": f, "writer": w, "buf": [], "lines": 0, "index": 0, "subdir": path, "type" : "vertices"}


def _open_edge_writer(root: str, elabel: str, props: Dict[str, Any], wid: int):
    path = os.path.join(root, elabel)
    os.makedirs(path, exist_ok=True)
    f = open(os.path.join(path, f"edges_part_{wid}_{elabel}_000.csv"),
             "w", newline="", buffering=CSV_BUFFER_SIZE)
    w = csv.writer(f)
    w.writerow(["~from", "~to", "~label"] + get_property_header_list(props))
    return {"file": f, "writer": w, "buf": [], "lines": 0, "index": 0, "subdir": path, "type" : "edges"}


def _maybe_rollover(writer, worker_id):
    if writer["lines"] >= MAX_EDGE_FILE_LINES:
        writer["file"].close()
        writer["index"] += 1
        fpath = os.path.join(writer["subdir"], f"{writer["type"]}_part_{worker_id}_{os.path.basename(writer['subdir'])}_{writer['index']:03d}.csv")
        writer["file"] = open(fpath, "w", newline="", buffering=CSV_BUFFER_SIZE)
        writer["writer"] = csv.writer(writer["file"])
        writer["writer"].writerow(["~from", "~to", "~label"])
        writer["lines"] = 0


def _flush_writer(writer, worker_id, force=False):
    if force or len(writer.get("buf")) >= BATCH_SIZE:
        writer["writer"].writerows(writer["buf"])
        writer["lines"] += len(writer["buf"])
        writer["buf"].clear()
        writer["file"].flush()
        _maybe_rollover(writer, worker_id)


def process_full_worker(
        worker_id: int,
        aux_path: str,
        num_workers: int,
        ego_start: int,
        ego_count: int,
        node_share_chance: int,
        invert_direction: bool,
        seed: int,
        total_disks: int,
        out_dir: str | None = None) -> tuple[int | Any, int | Any]:
    payload = pickle.load(open(aux_path, "rb"))
    config_flatmap = payload["config"]
    vertex_properties = payload["vertex_properties"]
    edge_properties = payload["edge_properties"]
    ego_label = config_flatmap["EgoNode"]["label"]
    rng_py = seed
    rng_np = np.random.default_rng()

    vroot = _shard_root("vertices", worker_id, total_disks, out_dir)
    eroot = _shard_root("edges", worker_id, total_disks, out_dir)
    os.makedirs(vroot, exist_ok=True)
    os.makedirs(eroot, exist_ok=True)

    vertex_writers: Dict[str, Dict[str, Any]] = {}
    edge_writers: Dict[str, Dict[str, Any]] = {}

    def vw(label: str):
        if label not in vertex_writers:
            vertex_writers[label] = _open_vertex_writer(vroot, label, vertex_properties[label], worker_id)
        return vertex_writers[label]

    def ew(label: str, share_properties: Dict | None = None):
        if label not in edge_writers and not label == "":
            if share_properties:
                edge_writers[label] = _open_edge_writer(eroot, label, share_properties, worker_id)
            else:
                edge_writers[label] = _open_edge_writer(eroot, label, edge_properties.get(label), worker_id)
        return edge_writers.get(label)

    def ew_buff_write(buff: List[Any], origin: str, nbr: str, label: str, props: List[Any]) -> None:
        if invert_direction:
            buff.append([nbr, origin, elabel] + props)
        else:
            buff.append(props)

    counters = defaultdict(int)

    def next_id(label: str) -> str:
        idx = generate_vertex_id(label, counters[label] + worker_id)
        counters[label] += num_workers
        return idx

    vertices_written = 0
    edges_written = 0
    for _ego_idx in range(ego_start, ego_start + ego_count):
        ego_props = vertex_properties[ego_label]
        ego_conns = config_flatmap["EgoNode"].get("connections")

        d1_plan: List[Tuple[str, str, int, Dict[str, Any]]] = []  # (dst_type, edge_label, count, dst_conn_meta)
        ego_out = 0
        if ego_conns:
            for dst_type, meta in ego_conns.items():
                if dst_type not in vertex_properties.keys():
                    continue
                count = _sample_degree(meta, rng_np)
                if count <= 0:
                    continue
                elabel = _edge_label(ego_label, dst_type, meta, invert_direction)
                d1_plan.append((dst_type, elabel, count, meta))

        ego_id = next_id(ego_label)
        vw(ego_label)["buf"].append([ego_id, ego_label] + generate_line_properties(ego_props, rng_py))
        vertices_written+=1

        for dst_type, elabel, cnt, _meta in d1_plan:
            dst_label = dst_type
            dst_props = vertex_properties[dst_type]
            dst_conns = config_flatmap[dst_type].get("connections")

            for _ in range(cnt):
                d2_plan: List[Tuple[str, str, int]] = []
                if dst_conns:
                    for d2_type, d2_meta in dst_conns.items():
                        if d2_type == "EgoNode" or d2_type == ego_label or d2_type not in vertex_properties.keys():
                            continue
                        k = _sample_degree(d2_meta, rng_np)
                        if k <= 0:
                            continue
                        d2_elabel = _edge_label(dst_type, d2_type, d2_meta, invert_direction)
                        d2_plan.append((d2_type, d2_elabel, k))
                        vertices_written+=1

                nbr_id = next_id(dst_label)
                vw(dst_label)["buf"].append([nbr_id, dst_label] + generate_line_properties(dst_props, rng_py))

                ew_buff_write(ew(elabel)["buf"], ego_id, nbr_id, elabel, generate_line_properties(edge_properties[elabel], rng_py))

                vertices_written+=1
                edges_written+=1
                _flush_writer(vw(dst_label), worker_id)
                _flush_writer(ew(elabel), worker_id)

                for d2_type, d2_elabel, k in d2_plan:
                    leaf_label = config_flatmap[d2_type]["label"]
                    leaf_props = vertex_properties[d2_type]
                    for _ in range(k):
                        leaf_id = next_id(leaf_label)
                        vw(leaf_label)["buf"].append([leaf_id, leaf_label] + generate_line_properties(leaf_props, rng_py))
                        d2_edge_props = edge_properties[d2_elabel]
                        edge_props = generate_line_properties(d2_edge_props, rng_py)
                        ew_buff_write(ew(d2_elabel)["buf"], nbr_id, leaf_id, d2_elabel, edge_props)

                        vertices_written+=1
                        edges_written+=1
                        if random.randint(0, 100) <= node_share_chance:
                            share_label = _edge_label(ego_label, d2_type, {}, invert_direction)
                            ew_buff_write(ew(share_label, d2_edge_props)["buf"], ego_id, leaf_id, share_label, edge_props)
                            _flush_writer(ew(share_label), worker_id)
                    _flush_writer(ew(d2_elabel), worker_id)
                    _flush_writer(vw(leaf_label), worker_id)
            _flush_writer(vw(ego_label), worker_id)

    for v in vertex_writers.values():
        _flush_writer(v, worker_id, force=True)
        v["file"].close()
    for e in edge_writers.values():
        _flush_writer(e, worker_id, force=True)
        e["file"].close()

    print(f"Worker {worker_id:02d}: 100% complete - {vertices_written} vertices, {edges_written} edges")
    return vertices_written, edges_written