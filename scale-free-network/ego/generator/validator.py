from __future__ import annotations
from typing import Tuple, Any, List, Dict, Iterator, Optional
import yaml

from faker_source import FakerSource

def parse_config_yaml(config_path: str) -> dict[str, dict[str, any]]:
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)


def validate_aerospike_properties(properties):
    """Validate that each property is accepted by Aerospike Graph and return their generator"""
    for prop_name, props in (properties or {}).items():
        name = prop_name.lower()
        gen = props.get("generator")
        ptype = props.get("type")
        unique_flag = props.get("prefer_unique") or False
        if not gen:
            raise ValueError(f"Invalid property definition '{prop_name}': property generator is empty.")
        src = FakerSource(gen, pool_size=5, batch_size=4096, prefer_unique=unique_flag, predicted_type=ptype)
        if not ptype:
            raise ValueError(f"Invalid property definition '{ptype}': property type is empty.")
        props["generator"] = src


def parse_connections_config(conn_config, full_config, parent, invert_direction) -> Dict:
    """Validates connections properties are valid, and the connection has the distribution properties. Returns properties dict"""
    if len(conn_config) == 0:
        raise ValueError(f"Connections cannot be empty, either make it null or add a connection")
    eprops = {}
    for name, props in conn_config.items():
        conn_props = props.get("properties")
        validate_aerospike_properties(conn_props)
        if not isinstance(props.get("sigma"), float) and not isinstance(props.get("sigma"), int):
            raise TypeError("Sigma is not a float or int")
        if not isinstance(props.get("median"), float) and not isinstance(props.get("median"), int):
            raise TypeError("Sigma is not a float or int")
        if name not in full_config and name not in full_config.get("AlterNodes"):
            raise ValueError(f"Connection type '{name}' not found as a node type")
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
