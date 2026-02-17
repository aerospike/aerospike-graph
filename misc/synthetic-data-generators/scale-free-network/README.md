# Scale-Free Network Generator (Power-Law Multitype Graph)

Generate scale-free network graphs (power‑law distributed) from a single `config.yaml`, with full support for multi‑type schemas.

> **Note**: This generator is part of the [Synthetic Data Generators for Aerospike Graph Service](../README.md) repository. For an overview of all generators, see the main README.

---

## Table of Contents

- [How to Use](#how-to-use)
  - [Quick Start](#quick-start)
  - [Example Command](#example-command)
  - [Validate Distribution](#validate-distribution)
- [Features](#features)
- [Requirements](#requirements)
- [CLI Reference](#cli-reference)
  - [`--nodes`](#--nodes)
  - [`--workers`](#--workers)
  - [`--seed`](#--seed)
  - [`--gamma`](#--gamma)
  - [`--dry-run`](#--dry-run)
  - [`--validate-distribution`](#--validate-distribution)
  - [`--mount`](#--mount)
  - [`--out-dir`](#--out-dir)
- [Editing Schemas](#editing-schemas)
  - [Property Schema](#property-schema)
    - [Long](#long)
    - [Integer](#integer)
    - [Double](#double)
    - [Boolean](#boolean)
    - [String](#string)
    - [Date](#date)
    - [List](#list)
- [Vertex Schemas](#vertex-schemas)
- [Edge Schemas](#edge-schemas)
- [Output Format](#output-format)
- [Power-Law Distribution](#power-law-distribution)
- [Related Documentation](#related-documentation)

---

## How to Use

### Quick Start

1. **Set up a virtual environment** (recommended):
   ```bash
   # Create a virtual environment
   python -m venv venv
   
   # Activate the virtual environment
   # On Windows:
   venv\Scripts\activate
   # On Linux/Mac:
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Edit your schema configuration** in `config/config.yaml`:
   - Define vertex types with `percent` distribution
   - Define edge types with `from` and `to` relationships
   - Configure properties for vertices and edges

4. **Run the generator**:
   ```bash
   cd generator
   python generate-multitype-scalefree.py \
     --nodes 100000 \
     --out-dir ../output \
     --seed 42 \
     --gamma 2.0
   ```

5. **Output**: CSV files will be generated in the specified output directory, organized as:
   ```
   output/
   ├── vertices/
   │   └── <vertex_type>/
   │       └── vertices_*.csv
   └── edges/
       └── <edge_type>/
           └── edges_*.csv
   ```

### Example Command

Generate a graph with 100,000 vertices using power-law distribution (gamma=2.0):
```bash
python generator/generate-multitype-scalefree.py \
  --nodes 100000 \
  --out-dir ./output \
  --seed 42 \
  --gamma 2.0 \
  --workers 8
```

### Validate Distribution

To validate that the generated graph follows a power-law distribution:
```bash
python generator/generate-multitype-scalefree.py \
  --nodes 100000 \
  --gamma 2.0 \
  --validate-distribution \
  --dry-run
```

---

## Features

- Scale‑free / power‑law degree generation driven by `gamma`
- Multi‑type vertices and edges defined in one YAML
- Parallel execution with worker pools
- Deterministic runs with a base seed
- Dry‑run & distribution validation utilities

---

## Requirements

- Python 3.9+
- `pip install -r requirements.txt`
- (Optional) mounted disks at `/mnt/data*` if you use `--mount`

---

## CLI Reference

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
Exponent controlling the power‑law tail. Larger values → fewer extreme high‑degree nodes. Recommended range ~ **1–3**.

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

*Type:* `string` — *Required if not using `--mount`*
Output directory for all generated files. Must be specified unless using the `--mount` option.

---

## Editing Schemas

All schema editing is done in **`config/config.yaml`**.

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

Each property `type` must be one of Aerospike Graph's supported types:
`Long, Int, Integer, Double, Bool, Boolean, String, Date, List`

> More details: [Aerospike Graph Service CSV Format](https://aerospike.com/docs/graph/develop/data-loading/csv-format/)

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

## Vertex Schemas

Under the top‑level `vertices` mapping, create one record per vertex type. Each vertex type must specify a `percent` value indicating what percentage of the total vertex count should be of this type.

```yaml
vertices:
  Vertex_Name:
    properties:
      # ... property definitions
    percent: 25  # 25% of all vertices will be of this type
```

**Note**: The sum of all `percent` values should equal 100.

---

## Edge Schemas

Under the top‑level `edges` mapping, create one record per edge label, with each edge type under it as a list item:

```yaml
edges:
  TRACKS:  # Edge label
    Delivery_Tracks_Warehouse:  # Edge type name
      properties:
        # ... edge property definitions
      from: Delivery  # Source vertex type
      to: Warehouse   # Target vertex type
      median: 4       # Degree distribution parameters
      sigma: 2
```

Each edge type must specify:
- `from`: The source vertex type name
- `to`: The target vertex type name
- `median` and `sigma`: Parameters for the degree distribution (used for lognormal sampling)

---

## Output Format

The generator produces CSV files compatible with Aerospike Graph Service bulk loading:

- **Vertices**: `vertices/<vertex_type>/vertices_*.csv` with columns: `id,label,<properties...>`
- **Edges**: `edges/<edge_type>/edges_*.csv` with columns: `src_id,dst_id,label,<properties...>`

The output format follows the [Aerospike Graph Service CSV format](https://aerospike.com/docs/graph/develop/data-loading/csv-format/) requirements.

---

## Power-Law Distribution

This generator creates graphs with power-law degree distributions, which are common in real-world networks (social networks, web graphs, etc.). The `--gamma` parameter controls the exponent of the power-law distribution:

- **Lower gamma (1.5-2.0)**: More extreme high-degree nodes (hubs)
- **Higher gamma (2.5-3.0)**: Fewer extreme high-degree nodes, more uniform distribution

Use `--validate-distribution` to verify that your generated graph follows the expected power-law distribution.

---

## Related Documentation

- [Main Repository README](../README.md) - Overview of all generators
- [Aerospike Graph Service CSV Format](https://aerospike.com/docs/graph/develop/data-loading/csv-format/) - CSV format requirements
