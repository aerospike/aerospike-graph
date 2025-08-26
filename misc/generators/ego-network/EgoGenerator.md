# Ego Network Generator (Identity Graph)

Generate synthetic CSV data for identity graphs using a configurable ego–alter expansion algorithm driven by your YAML schema.

---

## ✨ Features

* Schema‑driven vertex/edge generation (labels, properties, connection degrees)
* Multiple degree distributions (fixed, uniform, normal, poisson, lognormal)
* Parallel execution with chunking
* Deterministic runs with a seed
* Optional node sharing from ego to second‑hop nodes
* Dry‑run + validation

---

## 📦 Requirements

* Python 3.9+
* `pip install -r requirements.txt` (includes `faker`, `pyyaml`, `numpy`)
* Optional: `gsutil` if you plan to push to GCS later

---

## 🚀 Quickstart

1. Create a schema YAML (see **Schema Reference** below) and save as `schema.yaml`.
2. Run the generator:

```bash
python ego_network_generator.py \
  --schema ./schema.yaml \
  --sf 100000 \
  --target-chunks 16 \
  --workers 8 \
  --out-dir ./output \
  --seed 42
```

> **Note:** If you have a separate *scale‑free* script (e.g., `generate-multitype-scalefree.py` with flags like `--nodes`, `--gamma`), keep its example in that repo/file. This README documents the ego‑network generator CLI shown below.

---

## ⚙️ CLI Reference

All flags are passed to the script entrypoint.

### `--schema` **(required)**

*Type:* `str`
Path to the schema YAML file.

### `--sf`

*Type:* `int` — *Default:* `100000`
Number of **ego networks** (Egos) to generate.

### `--chunk-size`

*Type:* `int` — *Default:* `50000`
Number of Egos per work chunk.

### `--target-chunks`

*Type:* `int | null` — *Default:* `null`
Desired number of chunks. If set, overrides `--chunk-size`.
General rule of thumb is to have this double the worker count

### `--workers`

*Type:* `int` — *Default:* CPU count
Number of parallel workers.

### `--seed`

*Type:* `int` — *Default:* `0`
Base RNG seed for reproducibility.

### `--node-sharing-chance`

*Type:* `int` — *Default:* `0`
Percent chance that the Ego node also connects directly to a second‑hop leaf (i.e., `Ego→Alter→Leaf` **plus** `Ego→Leaf`).

### `--invert-direction`

*Type:* flag
Flip edge direction to generate inbound edges (i.e., `Ego←Alter←Leaf`).

### `--dry-run`

*Type:* flag
Parse config and plan generation without writing vertices/edges.

### `--mount`

*Type:* flag
Use mounted disks at `/mnt/data*` for I/O.

### `--out-dir`

*Type:* `str` — *Default:* `aerospikegraph/scale-free-network/ego/output`
Output directory for generated CSV files.

---

## 🧱 Schema Reference

Your schema must define exactly one **EgoNode** and one **AlterNodes** mapping.

```yaml
EgoNode:
  label: EgoLabel
  connections:
    Vert1:
      degree:
        dist: normal
        mean: 2
        sigma: 1
        round: round
        min: 1
        max: 6

AlterNodes:
  Vert1:
    label: Vert1Label
    connections:
      Vert2:
        degree:
          dist: lognormal
          median: 6.00
          sigma: 0.8
          max: 20
    properties:
      prop1:
        type: bool
        generator: pybool(0.4)
  Vert2:
    label: Vert2Label
    properties:
      prop1:
        type: string
        generator: random_element(["Graph", "KeyValue", "Vector"])
      prop2:
        type: date
        generator: date()
```

### Nodes

Each node entry supports `label` (required) plus optional `properties` and `connections`.

```yaml
NodeName:
  label: <string>
  connections: { ... }
  properties: { ... }
```

### Connections

Each connection points to a target node type and must include a `degree` block.
You may optionally provide `properties` for edges, and/or an explicit edge `label` if supported by your version.

```yaml
connections:
  TargetVert:
    # Optional edge label; if omitted, the generator uses a default (REL_SOURCE_TO_TARGET)
    degree: { ... }   # required
    properties: { ... }  # optional edge properties
```

---

## 📊 Degree Distributions

A `degree` block is **required** on every connection. After sampling, values are rounded and clamped to `[min, max]`.

**Common options** (apply to all dists):

| Property | Type                     | Default | Notes                |
| -------- | ------------------------ | ------: | -------------------- |
| `round`  | `round`\|`floor`\|`ceil` | `round` | Float→int conversion |
| `min`    | integer                  |     `0` | Lower clip bound     |
| `max`    | integer\|`null`          |  `null` | Upper clip bound     |

### `fixed`

```yaml
degree:
  dist: fixed
  value: 3
```

### `uniform`

Bounds **or** median/sigma.

```yaml
degree:
  dist: uniform
  low: 1.5
  high: 4.5
  round: floor
```

```yaml
degree:
  dist: uniform
  median: 2
  sigma: 1
```

### `normal`

```yaml
degree:
  dist: normal
  mean: 2
  sigma: 1
  min: 0
```

### `poisson`

```yaml
degree:
  dist: poisson
  lam: 6.44
  max: 50
```

### `lognormal`

```yaml
degree:
  dist: lognormal
  median: 6.44
  sigma: 0.8
  max: 200
```

---

## 🧬 Property Schema

Properties are generated via Faker functions.
Each property requires a `type` and a `generator`.

Optional tuning:

* `pool_size: int` — value cache size (default 20)
* `prefer_unique: bool` — try producing unique values (more memory/CPU)

```yaml
some_flag:
  type: bool
  generator: pybool(0.8)
  pool_size: 50
```

**List properties** must specify a single `element_type`:

```yaml
names:
  type: List
  element_type: string
  generator: pylist(nb_elements=15, allowed_types=[str])
```

### Supported Types

`long`, `int`/`integer`, `double`, `bool`/`boolean`, `string`, `date`, `list`

> Int bounds: `[-2_147_483_648, 2_147_483_647]`
> Long bounds: `[-9_223_372_036_854_775_808, 9_223_372_036_854_775_807]`

**Date** values must be ISO‑8601 (e.g., `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ`).

---

## 🗂️ Outputs
Output folder structure will look something like:
`
edges |
     - edge_type_name |
                      - edges_part_{chunkid}_edgetypename_{fileindex}.csv
                      - ...
vertices |
         - vertex_type_name |
                            - vertices_part_{chunkid}_vertextypename_{fileindex}.csv
                            - ...
`

* `vertices_*.csv` — rows: `id,label,<vertex props...>`
* `edges_*.csv` — rows: `src_id,dst_id,label,<edge props...>`

---

## 🧪 Validation & Dry Run

Use `--dry-run` to validate the schema without writing files. The tool reports any schema errors.

---

## ⚠️ Safety Notes

* Large `--sf` and high degrees can create huge edge sets. Ensure you have disk space.
* If you use `--invert-direction`, verify the loader expects inbound relationships.
* If you publish configs/examples, avoid real PII or production identifiers.

---
