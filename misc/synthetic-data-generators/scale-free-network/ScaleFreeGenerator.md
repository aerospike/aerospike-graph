# Power‑Law Multitype Graph Generator

Generate  scale-free network graphs (power‑law distributed) from a single `config.yaml`, with full support for multi‑type schemas.

---

## ✨ Features

* Scale‑free / power‑law degree generation driven by `gamma`
* Multi‑type vertices and edges defined in one YAML
* Parallel execution with worker pools
* Deterministic runs with a base seed
* Dry‑run & distribution validation utilities

---

## 📦 Requirements

* Python 3.9+
* `pip install -r requirements.txt`
* (Optional) mounted disks at `/mnt/data*` if you use `--mount`

---

## 🚀 Quickstart

Edit `config.yaml` to define your vertex and edge types (see **Editing Schemas** below). Then run:

```bash
python ./generator/generate-multitype-scalefree \\
  --nodes 100000 \\
  --out-dir C:\\Path\\To\\Directory\\output \\
  --seed 42 \\
  --gamma 2.0 \\
  --validate-distribution \\
  --dry-run
```

---

## ⚙️ Config Options (CLI)

All flags are passed to the generator entrypoint.

### `--nodes`

*Type:* `int` — *Default:* `100000`
Total number of vertices in the graph.

### `--workers`

*Type:* `int` — *Default:* CPU core count
Parallel workers for generation.

### `--seed`

*Type:* `int` — *Default:* `0`
Base RNG seed for reproducibility.

### `--gamma`

*Type:* `number` — *Default:* `2.5`
Exponent controlling the power‑law tail. Larger values → fewer extreme high‑degree nodes. Recommended range \~ **1–3**.

### `--dry-run`

*Type:* flag
Only compute/print degree distribution statistics; do **not** emit files.

### `--validate-distribution`

*Type:* `bool` — *Default:* `false`
Run a helper to compare lognormal vs power‑law fit.

### `--mount`

*Type:* flag
Use mounted disks at `/mnt/data*` for I/O.

### `--out-dir`

*Type:* `string`
Output directory for all generated files.

---

## 🛠️ Editing Schemas

All schema editing is done in **`config.yaml`**.

### Property Schema

When defining properties (for **vertices** and **edges**), declare them under a `properties` mapping. Each property has a `type` and type‑specific options that constrain how values are generated.

```yaml
vertices:
  vertex_name:
    properties:               # <— dict of properties
      prop_1:                 # <— dict of property specifications
        type:                 # <— type name
        unique_type_prop_1:   # <— type‑specific setting
        unique_type_prop_2:   # <— type‑specific setting
    percent:                  # <— share of overall node count (see Vertex Schemas)
```

Each property `type` must be one of Aerospike Graph’s supported types:
`Long, Int, Integer, Double, Bool, Boolean, String, Date, List`

> More details: [https://aerospike.com/docs/graph/develop/data-loading/csv-format/](https://aerospike.com/docs/graph/develop/data-loading/csv-format/)

**Type‑specific options**

#### Long

Longs are constrained to `-2^63 .. 2^63-1`.

```yaml
Long_Property:
  type: Long
  max: 9223372036854775807
  min: 20
```

#### Integer

Type may be `Integer` or `Int`. Constrained to `-2^31 .. 2^31-1`.

```yaml
Integer_Property:
  type: Integer
  max: 89412
  min: 20
```

#### Double

64‑bit IEEE‑754 floating point.

```yaml
Double_Property:
  type: Double
  max: 1954.721
  min: 67.01
```

#### Boolean

Type may be `Bool` or `Boolean`. `true_chance` is **0–100** (percentage).

```yaml
Boolean_Property:
  type: Boolean
  true_chance: 15
```

#### String

Any valid string. `max_size`/`min_size` bound the length. `allowed_chars` limits the character set (empty → all chars allowed).

```yaml
String_Properties:
  type: String
  max_size: 8
  min_size: 2
  allowed_chars: "!@#$%^&*()_+}{:></;?"
```

#### Date

Dates are emitted in ISO‑8601 `YYYY-MM-DD`.

```yaml
Date_Property:
  type: Date
  max_year: 2025
  min_year: 1932
```

#### List

Lists may contain **one element type** (no nesting). The `element` block is the schema for each list element.

```yaml
List_Property:
  type: List
  min_length: 0
  max_length: 100
  element:
    type: String
    max_size: 8
    min_size: 2
    allowed_chars: "!@#$%^&*()_+}{:></;?"
```

---

## 🧩 Vertex Schemas

Under the top‑level `vertices` mapping, create one record per vertex type.

```yaml
vertices:
  Vertex_Name:
```

## 🧩 Edge Schemas

Under the top‑level `edges` mapping, create one record per edge label, with each edge type under it as a list item:

```yaml
edges:
  TRACKS:
      Delivery_Tracks_Warehouse:
```
