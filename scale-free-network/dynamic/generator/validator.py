import re
import string
import datetime
import numpy as np
import sys
import yaml
import powerlaw
import matplotlib.pyplot as plt
from numpy.f2py.auxfuncs import throw_error


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

AEROSPIKE_GRAPH_TYPES = {
    "long", "int", "integer", "double", "bool", "boolean", "string", "date", "list"
}
INT_MIN, INT_MAX = -2**31, 2**31 - 1
LONG_MIN, LONG_MAX = -2**63, 2**63 - 1
DOUBLE_MIN, DOUBLE_MAX = -sys.float_info.max, sys.float_info.max

def validate_int(props):
    max = props.get("max")
    min = props.get("min")
    if not isinstance(max, int):
        raise TypeError("Int max is not an int")
    if max < INT_MIN or max > INT_MAX:
        raise ValueError("Int max is out of bounds for java int")
    if not isinstance(min, int):
        raise TypeError("Int min is not an int")
    if min < INT_MIN or min > INT_MAX:
        raise ValueError("Int min is out of bounds for java int")
    if max < min:
        raise ValueError("Int max is smaller then min")

def validate_long(props):
    max = props.get("max")
    min = props.get("min")
    if not isinstance(max, int):
        raise TypeError("Long max is not a number")
    if max < LONG_MIN or max > LONG_MAX:
        raise ValueError("Long max is out of bounds for java Long")
    if not isinstance(min, int):
        raise TypeError("Long min is not a number")
    if min < LONG_MIN or min > LONG_MAX:
        raise ValueError("Long min is out of bounds for java Long")
    if max < min:
        raise ValueError("Long max is smaller then min")

def validate_double(props):
    max = props.get("max")
    min = props.get("min")
    if not (isinstance(max, float) or isinstance(max, int)):
        raise TypeError("Double max is not a python float (decimal number)")
    if max < DOUBLE_MIN or max > DOUBLE_MAX:
        raise ValueError("Double max is out of bounds for java Double")
    if not (isinstance(min, float) or isinstance(min, int)):
        raise TypeError("Double min is not a python float (decimal number)")
    if min < DOUBLE_MIN or min > DOUBLE_MAX:
        raise ValueError("Double min is out of bounds for java Double")
    if max < min:
        raise ValueError("Double max is smaller then min")

def validate_string(props):
    max_size = props.get("max_size")
    min_size = props.get("min_size")
    allowed_chars = props.get("allowed_chars")

    if not isinstance(max_size, int):
        raise TypeError("String max_size is not an int")
    if max_size < 0 or max_size > 2147483647:
        raise ValueError("String max_size is out of bounds for java String size")
    if not isinstance(min_size, int):
        raise TypeError("String min_size is not an int")
    if min_size < 0 or min_size > 2147483647:
        raise ValueError("String min_size is out of bounds for java String size")
    if max_size < min_size:
        raise ValueError("String max_size is smaller then min_size")
    if not isinstance(allowed_chars, str):
        raise TypeError("String allowed_chars is not a string")

def validate_bool(props):
    true_chance = props.get("true_chance")
    if not (isinstance(true_chance, float) or isinstance(true_chance, int)):
        raise TypeError("Booleans true_chance is not a float or int")
    if true_chance < 0 or true_chance > 100:
        raise ValueError("Booleans true_chance is not a valid percent chance, make it between 1 and 100")


def validate_date(props):
    max_year = props.get("max_year")
    min_year = props.get("min_year")
    if not isinstance(max_year, int):
        raise TypeError("Date max_year is not an int")
    if max_year < 0 or max_year > 9999:
        raise ValueError("Date max_year is out of bounds for year")
    if not isinstance(min_year, int):
        raise TypeError("Date min_year is not an int")
    if min_year < 0 or min_year > 9999:
        raise ValueError("Date min_year is out of bounds for year")
    if max_year < min_year:
        raise ValueError("Date max_size is smaller then min_size")

def validate_list(props):
    max_length = props.get("max_length")
    min_length = props.get("min_length")
    element = props.get("element")
    if not isinstance(max_length, int):
        raise TypeError("List max_length is not an int")
    if max_length < 0 or max_length > 2147483647:
        raise ValueError("List max_length is out of bounds for java List size")
    if not isinstance(min_length, int):
        raise TypeError("List min_length is not an int")
    if min_length < 0 or min_length > 2147483647:
        raise ValueError("List min_length is out of bounds for java List size")
    if max_length < min_length:
        raise ValueError("List max_length is smaller then min_length")
    if not isinstance(element, dict):
        raise TypeError("Element is not dict")
    element_type = element.get("type")
    if element_type == "list":
        raise ValueError("Nested Lists are not allowed, please select another element type")

    validate_property(element_type, element)

def validate_property(prop_type: str, props: dict):
    name = prop_type.lower()
    dispatch = {
        "int":    validate_int,
        "integer":    validate_int,
        "long":   validate_long,
        "double": validate_double,
        "string": validate_string,
        "bool":   validate_bool,
        "boolean":   validate_bool,
        "date":   validate_date,
        "list":   validate_list,
    }
    gen = dispatch[name]
    gen(props)
    return

def parse_config_yaml(config_path: str) -> dict[str, dict[str, any]]:
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def validate_aerospike_properties(properties, type, sub_type):
    for prop_name, props in properties.items():
        name = prop_name.lower()
        type_str = props.get("type").strip().lower()
        if not name:
            raise ValueError(f"Invalid {type} {sub_type} property definition '{prop_name}': property name is empty.")
        if not type_str:
            raise ValueError(f"Invalid {type} {sub_type} property definition '{prop_name}': property type is empty.")
        if type_str not in AEROSPIKE_GRAPH_TYPES:
            raise ValueError(
                f"Invalid {type} property type '{type_str}' for property '{name}' in {sub_type} {type}. "
                f"Supported types are: {sorted(AEROSPIKE_GRAPH_TYPES)}"
            )
        validate_property(type_str, props)
    return True

def parse_edge_config(config, vertex_idx_mapping):
    result = []
    i = 0
    for edge_type, edge_groups in config.items():
        for rel_key, props in edge_groups.items():
            properties = props['properties']
            if properties == None:
                properties = []
            if not isinstance(properties, dict):
                raise ValueError(f"Edge properties are not a dict: '{properties}'")
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
        if not isinstance(properties, dict):
            raise ValueError(f"Vertex properties are not a dict: '{properties}'")
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
