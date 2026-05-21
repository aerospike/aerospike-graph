# Scale-free network generator (power-law multi-type graph)

Generate scale-free network graphs (power-law distributed) from a single `config.yaml`, with full support for multi-type schemas.

> **Note:** This generator is part of the [Synthetic data generators for Aerospike Graph Service](../README.md) repository. For an overview of all generators, see the main README.

---

## Table of contents

- [How to use](#how-to-use)
  - [Quickstart](#quickstart)
  - [Example command](#example-command)
  - [Validate distribution](#validate-distribution)
- [Features](#features)
- [Requirements](#requirements)
- [CLI reference](#cli-reference)
  - [`--nodes`](#--nodes)
  - [`--workers`](#--workers)
  - [`--seed`](#--seed)
  - [`--gamma`](#--gamma)
  - [`--dry-run`](#--dry-run)
  - [`--validate-distribution`](#--validate-distribution)
  - [`--mount`](#--mount)
  - [`--out-dir`](#--out-dir)
- [Editing schemas](#editing-schemas)
  - [Property schema](#property-schema)
    - [Long](#long)
    - [Integer](#integer)
    - [Double](#double)
    - [Boolean](#boolean)
    - [String](#string)
    - [Date](#date)
    - [List](#list)
- [Vertex schemas](#vertex-schemas)
- [Edge schemas](#edge-schemas)
- [Output format](#output-format)
- [Power-law distribution](#power-law-distribution)
- [Related documentation](#related-documentation)

---

## How to use

### Quickstart

1. Set up a virtual environment (recommended):

   ```bash
   # Create a virtual environment
   python -m venv venv

   # Activate the virtual environment
   # On Windows:
   venv\Scripts\activate
   # On Linux/Mac:
   source venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Edit your schema configuration in `config/config.yaml`:
   - Define vertex types with a `percent` distribution.
   - Define edge types with `from` and `to` relationships.
   - Configure properties for vertices and edges.

4. Run the generator:

   ```bash
   cd generator
   python generate-multitype-scalefree.py \
     --nodes 100000 \
     --out-dir ../output \
     --seed 42 \
     --gamma 2.0
   ```

5. CSV files are written to the output directory, organized as:

   ```text
   output/
   ├── vertices/
   │   └── <vertex_type>/
   │       └── vertices_*.csv
   └── edges/
       └── <edge_type>/
           └── edges_*.csv
   ```

### Example command

Generate a graph with 100,000 vertices using a power-law distribution (gamma=2.0):

```bash
python generator/generate-multitype-scalefree.py \
  --nodes 100000 \
  --out-dir ./output \
  --seed 42 \
  --gamma 2.0 \
  --workers 8
```

### Validate distribution

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

- Scale-free / power-law degree generation driven by `gamma`.
- Multi-type vertices and edges defined in one YAML.
- Parallel execution with worker pools.
- Deterministic runs with a base seed.
- Dry-run and distribution-validation utilities.

---

## Requirements

- Python 3.9 or later.
- `pip install -r requirements.txt`.
- (Optional) mounted disks at `/mnt/data*` if you use `--mount`.

---

## CLI reference

All flags are passed to the generator entrypoint.

### `--nodes`

*Type:* `int` — *Default:* `100000`.
Total number of vertices in the graph.

### `--workers`

*Type:* `int` — *Default:* CPU core count.
Parallel workers for generation.

### `--seed`

*Type:* `int` — *Default:* `0`.
Base RNG seed for reproducibility.

### `--gamma`

*Type:* `number` — *Default:* `2.5`.
Exponent controlling the power-law tail. Larger values produce fewer extreme high-degree nodes. Recommended range: 1–3.

### `--dry-run`

*Type:* flag.
Compute and print degree-distribution statistics only; do **not** emit files.

### `--validate-distribution`

*Type:* `bool` — *Default:* `false`.
Run a helper to compare lognormal and power-law fits.

### `--mount`

*Type:* flag.
Use mounted disks at `/mnt/data*` for I/O.

### `--out-dir`

*Type:* `string` — *Required if not using `--mount`*.
Output directory for all generated files. Required unless you use the `--mount` option.

---

## Editing schemas

Edit all schemas in `config/config.yaml`.

### Property schema

When defining properties for vertices or edges, declare them under a `properties` mapping. Each property has a `type` and type-specific options that constrain how values are generated.

```yaml
vertices:
  vertex_name:
    properties:               # dict of properties
      prop_1:                 # dict of property specifications
        type:                 # type name
        unique_type_prop_1:   # type-specific setting
        unique_type_prop_2:   # type-specific setting
    percent:                  # share of overall node count (see Vertex schemas)
```

Each property `type` must be one of the AGS supported types: `Long`, `Int`, `Integer`, `Double`, `Bool`, `Boolean`, `String`, `Date`, `List`.

> For more information, see the [AGS CSV format](https://aerospike.com/docs/graph/load/csv-format).

**Type-specific options:**

#### Long

Longs are constrained to `-2^63` through `2^63-1`.

```yaml
Long_Property:
  type: Long
  max: 9223372036854775807
  min: 20
```

#### Integer

The type may be `Integer` or `Int`. Constrained to `-2^31` through `2^31-1`.

```yaml
Integer_Property:
  type: Integer
  max: 89412
  min: 20
```

#### Double

64-bit IEEE-754 floating point.

```yaml
Double_Property:
  type: Double
  max: 1954.721
  min: 67.01
```

#### Boolean

The type may be `Bool` or `Boolean`. `true_chance` is a percentage from 0 to 100.

```yaml
Boolean_Property:
  type: Boolean
  true_chance: 15
```

#### String

Any valid string. `max_size` and `min_size` bound the length. `allowed_chars` limits the character set (empty allows all characters).

```yaml
String_Properties:
  type: String
  max_size: 8
  min_size: 2
  allowed_chars: "!@#$%^&*()_+}{:></;?"
```

#### Date

Dates are emitted in ISO-8601 `YYYY-MM-DD` format.

```yaml
Date_Property:
  type: Date
  max_year: 2025
  min_year: 1932
```

#### List

Lists may contain one element type (no nesting). The `element` block is the schema for each list element.

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

## Vertex schemas

Under the top-level `vertices` mapping, create one record per vertex type. Each vertex type must specify a `percent` value indicating what percentage of the total vertex count must be of this type.

```yaml
vertices:
  Vertex_Name:
    properties:
      # ... property definitions
    percent: 25  # 25% of all vertices are of this type
```

> **Note:** The sum of all `percent` values must equal 100.

---

## Edge schemas

Under the top-level `edges` mapping, create one record per edge label, with each edge type as a list item:

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

- `from`: source vertex type name.
- `to`: target vertex type name.
- `median` and `sigma`: parameters for the degree distribution (used for lognormal sampling).

---

## Output format

The generator produces CSV files compatible with AGS bulk loading:

- **Vertices:** `vertices/<vertex_type>/vertices_*.csv` with columns: `~id`, `~label`, `<properties...>`.
- **Edges:** `edges/<edge_type>/edges_*.csv` with columns: `~from`, `~to`, `~label`, `<properties...>`.

The output format follows the [AGS CSV format](https://aerospike.com/docs/graph/load/csv-format) requirements.

---

## Power-law distribution

This generator creates graphs with power-law degree distributions, which are common in real-world networks such as social networks and web graphs. The `--gamma` parameter controls the exponent of the power-law distribution:

- **Lower gamma (1.5–2.0):** more extreme high-degree nodes (hubs).
- **Higher gamma (2.5–3.0):** fewer extreme high-degree nodes; more uniform distribution.

Use `--validate-distribution` to verify that the generated graph follows the expected power-law distribution.

---

## Related documentation

- [Main repository README](../README.md) — overview of all generators.
- [AGS CSV format](https://aerospike.com/docs/graph/load/csv-format) — CSV format requirements.
