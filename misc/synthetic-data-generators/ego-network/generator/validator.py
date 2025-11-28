from __future__ import annotations
from functools import partial
from typing import Tuple, Any, List, Dict, Iterator, Optional, Callable
import numpy as np
import yaml

from faker_source import FakerSource

def parse_config_yaml(config_path: str) -> dict[str, dict[str, any]]:
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)


def validate_aerospike_properties(properties):
    """Validate that each property is accepted by Aerospike Graph and return their generator"""
    for prop_name, props in (properties or {}).items():
        gen = props.get("generator")
        ptype = props.get("type")
        pool_size = props.get("pool_size") or 20
        unique_flag = props.get("prefer_unique") or False
        if not gen:
            raise ValueError(f"Invalid property definition '{prop_name}': property generator is empty.")
        src = FakerSource(gen, pool_size=pool_size, batch_size=4096, prefer_unique=unique_flag, predicted_type=ptype)
        if not ptype:
            raise ValueError(f"Invalid property definition '{ptype}': property type is empty.")
        props["generator"] = src


def _round_clip(x: float, round_mode: str, min_v: int | None, max_v: int | None) -> int:
    if round_mode == "floor":
        iv = int(np.floor(x))
    elif round_mode == "ceil":
        iv = int(np.ceil(x))
    else:
        iv = int(np.round(x))
    if min_v is not None:
        iv = max(int(min_v), iv)
    if max_v is not None:
        iv = min(int(max_v), iv)
    return iv

def _deg_fixed(rng: np.random.Generator, value: float, round_mode: str, min_v: int | None, max_v: int | None) -> int:
    return _round_clip(value, round_mode, min_v, max_v)

def _deg_uniform(rng: np.random.Generator, low: float, high: float,
                 round_mode: str, min_v: int | None, max_v: int | None) -> int:
    return _round_clip(rng.uniform(low, high), round_mode, min_v, max_v)

def _deg_normal(rng: np.random.Generator, mean: float, sigma: float,
                round_mode: str, min_v: int | None, max_v: int | None) -> int:
    return _round_clip(rng.normal(mean, sigma), round_mode, min_v, max_v)

def _deg_poisson(rng: np.random.Generator, lam: float,
                 round_mode: str, min_v: int | None, max_v: int | None) -> int:
    return _round_clip(float(rng.poisson(lam)), round_mode, min_v, max_v)

def _deg_lognormal(rng: np.random.Generator, meanlog: float, sigma: float,
                   round_mode: str, min_v: int | None, max_v: int | None) -> int:
    return _round_clip(rng.lognormal(mean=meanlog, sigma=sigma), round_mode, min_v, max_v)


def parse_degree(param: Dict[str, Any]) -> Callable[[np.random.Generator], int]:
    """
    Validate/normalize a degree spec and return a picklable callable
    """
    if not isinstance(param, dict):
        raise TypeError("degree must be a dict")

    dist = str(param.get("dist", "uniform")).lower()
    round_mode = str(param.get("round", "round")).lower()
    min_v = param.get("min", 0)
    max_v = param.get("max", None)

    if round_mode not in {"round", "floor", "ceil"}:
        raise ValueError(f"degree.round must be one of round|floor|ceil, got {round_mode}")
    if max_v is not None and min_v is not None and int(max_v) < int(min_v):
        raise ValueError(f"degree.max ({max_v}) cannot be less than degree.min ({min_v})")

    if dist == "fixed":
        if "value" not in param:
            raise ValueError("degree.fixed requires 'value'")
        return partial(_deg_fixed, value=float(param["value"]),
                       round_mode=round_mode, min_v=min_v, max_v=max_v)

    if dist == "uniform":
        if "low" in param and "high" in param:
            low, high = float(param["low"]), float(param["high"])
        else:
            median = float(param.get("median", 1.0))
            sigma = float(param.get("sigma", 0.5))
            if sigma < 0:
                raise ValueError("degree.uniform sigma must be >= 0")
            low, high = median - sigma, median + sigma
        if high < low:
            raise ValueError(f"degree.uniform: high ({high}) < low ({low})")
        return partial(_deg_uniform, low=low, high=high,
                       round_mode=round_mode, min_v=min_v, max_v=max_v)

    if dist == "normal":
        mean = float(param.get("mean", 1.0))
        sigma = float(param.get("sigma", 1.0))
        if sigma < 0:
            raise ValueError("degree.normal sigma must be >= 0")
        return partial(_deg_normal, mean=mean, sigma=sigma,
                       round_mode=round_mode, min_v=min_v, max_v=max_v)

    if dist == "poisson":
        lam = float(param.get("lam", param.get("lambda", 1.0)))
        if lam < 0:
            raise ValueError("degree.poisson lam must be >= 0")
        return partial(_deg_poisson, lam=lam,
                       round_mode=round_mode, min_v=min_v, max_v=max_v)

    if dist == "lognormal":
        sigma = float(param.get("sigma", 1.0))
        if sigma < 0:
            raise ValueError("degree.lognormal sigma must be >= 0")
        if "meanlog" in param:
            meanlog = float(param["meanlog"])
        else:
            median = float(param.get("median", 1.0))
            meanlog = np.log(max(median, 1e-12))
        return partial(_deg_lognormal, meanlog=meanlog, sigma=sigma,
                       round_mode=round_mode, min_v=min_v, max_v=max_v)

    raise ValueError(f"Unsupported degree.dist '{dist}'")


def parse_connections_config(conn_config, full_config, parent, invert_direction) -> Dict:
    """Validates connections properties are valid, and the connection has the distribution properties. Returns properties dict"""
    if len(conn_config) == 0:
        raise ValueError(f"Connections cannot be empty, either make it null or add a connection")
    eprops = {}
    for name, props in conn_config.items():
        conn_props = props.get("properties")
        validate_aerospike_properties(conn_props)
        if not isinstance(props.get("degree"), Dict):
            raise TypeError("degree is not a dict for {name}")
        props["degree"] = parse_degree(props.get("degree"))
        if name not in full_config and name not in full_config.get("AlterNodes"):
            raise ValueError(f"Connection type '{name}' not found as a node type")
        label = props.get("label")
        if label:
            eprops[label] = conn_props
        else:
            if invert_direction:
                eprops["REL_" + name.upper() + "_TO_" + parent.upper()] = conn_props
            else:
                eprops["REL_" + parent.upper() + "_TO_" + name.upper()] = conn_props
    return eprops


def parse_node_config(props, full_config, invert_direction) -> (Dict, Dict):
    """Validates connections properties are valid, and the connection has the distribution properties. Returns properties dict"""
    properties = props.get('properties')
    label = props.get("label")
    connections = props.get("connections")
    vprops = (properties or {})
    eprops = {}
    if not isinstance(vprops, dict):
        raise ValueError(f"Properties are not a dict: '{vprops}'")
    validate_aerospike_properties(vprops)
    if not label or not isinstance(label, str):
        raise ValueError(f"Invalid Label Value: '{label}'")
    if connections:
        eprops = parse_connections_config(connections, full_config, label, invert_direction)

    return vprops, eprops


def parse_config(config, invert_direction) -> (Dict, Dict, Dict):
    """Returns flatmap of the config"""
    EgoNode = config.get('EgoNode')
    AlterNodes = config.get('AlterNodes')
    if not EgoNode: raise ValueError(f"Config is missing EgoNodes'")
    if not AlterNodes: raise ValueError(f"Config is missing AlterNodes'")
    newdict = {"EgoNode": EgoNode}
    edge_props = {}
    vert_props = {}
    for name, props in config.items():
        lname = name.lower()
        if lname == "egonode":
            vprop, eprops = parse_node_config(props, config, invert_direction)
            vert_props[props["label"]] = vprop
            edge_props.update(eprops)
        else:
            for alter, alterProps in props.items():
                vprop, eprops = parse_node_config(alterProps, config, invert_direction)
                newdict[alter] = alterProps
                vert_props[alter] = vprop
                edge_props.update(eprops)

    return newdict, vert_props, edge_props
