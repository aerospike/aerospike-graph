import random
import pytest
from pathlib import Path

from food_delivery_app.food_delivery_datasetgen import (
    generate_dataset,
    vertex_types,
    edge_types,
    vertex_headers,
    edge_headers,
)

ROOT = Path(__file__).resolve().parent.parent

def count_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)

@pytest.mark.parametrize(
    "nc,nr,nd,min_o,max_o",
    [
        (3, 2, 1, 1, 1),
        (5, 3, 2, 1, 2),
    ]
)
def test_small_generation(tmp_path, nc, nr, nd, min_o, max_o):
    random.seed(0)

    generate_dataset(
        n_customers=nc,
        n_restaurants=nr,
        n_drivers=nd,
        min_orders_per_customer=min_o,
        max_orders_per_customer=max_o,
    )

    for label, sub in vertex_types.items():
        p = ROOT / "vertices" / sub / f"{sub}.csv"
        print(p)
        assert p.exists(), f"{sub}.csv missing"
        header = p.read_text(encoding="utf-8").splitlines()[0]
        assert header == vertex_headers[label]

    for label, sub in edge_types.items():
        p = ROOT / "edges" / sub / f"{sub}.csv"
        print(p)
        assert p.exists(), f"{sub}.csv missing"
        header = p.read_text(encoding="utf-8").splitlines()[0]
        assert header == edge_headers[label]

    # spot checks
    cust = ROOT / "vertices" / "customer" / "customer.csv"
    assert count_lines(cust) == 1 + nc

    # recompute expected orders
    random.seed(0)
    exp_orders = sum(random.randint(min_o, max_o) for _ in range(nc))
    placed = ROOT / "edges" / "placed" / "placed.csv"
    assert count_lines(placed) - 1 <= max_o* nc
    assert count_lines(placed) - 1 >= min_o* nc

    contains = ROOT / "edges" / "contains" / "contains.csv"
    assert count_lines(contains) - 1 >= exp_orders

    has_addr = ROOT / "edges" / "has_address" / "has_address.csv"
    assert count_lines(has_addr) == 1 + nc

    rated = ROOT / "edges" / "rated" / "rated.csv"
    num_rated = count_lines(rated) - 1
    assert 0 <= num_rated <= exp_orders
