# Overview
This generator will create Power-Law distributed graphs based on specifications made in the config.yaml
with support for multi-type graph schemas.

# Startup
Edit the yaml with your edge and vertex types, refer to the `Edge Schemas` and `Vertex Schemas` sections for guidance
Tune the config options too your specifications, refer to `Config Options` section for guidance.
An example of how to run the application would be
```shell 
python generate-multitype-scalefree --nodes 100000 --out-dir C:\Repos\aerospike-graph\scale-free-network\output --seed 42 --gamma 2.0 --validate-distribution --dry-run
```
# Config Options
`--nodes`, type=int, default=100000
Number of vertices (nodes) in the overall Graph

`--workers`, type=int, default=None
Number of Parallel workers to run the generator with, will default to your CPU Core count

`--seed`, type=int, default=0
Base RNG seed for reproducibility

`--gamma`, type=int, default=2.5
Gamma for power-law generation, controls the size of the tail, with a > gamma  resulting in fewer large values
Recommended to stay between 1-3

`--dry-run`
Flag to only show degree distribution statistics without generating files

`--validate-distribution`, type=bool, default=False
Flag to run a function to see the fit between lognormal and powerlaw

`--mount`
Flag to use mounted disks at /mnt/data*

`--out-dir`
Output directory for all files
# Editing Schemas
All schema editing is done in the config.yaml file

## Vertex Schemas
Under the `vertices` property, create a record for each vertex type.
Each vertex type should have the following properties:
```
properties:             # List <String>: properties of the edge
    - prop_name:Type    # String
    - prop_name1:Type   # String
    - prop_name2:Type   # String
percent:                # Integer: percent of overall node count
```

The total of all percent properties should add up to 100
Each `property` type must correspond to one of the supported types by Aerospike:
`Long, Int, Integer, Double, Bool, Boolean, String, Date`
## Edge Schemas
Under the `edges` property, create a record for each edge type.
Each edge type should have the following properties:
```yaml
composite_edge_name:
    properties:             # List <String>: properties of the edge
        - prop_name:Type    # String
        - prop_name1:Type   # String
        - prop_name2:Type   # String
    from: vertex_type       # String: name of the FROM vertex type 
    to: vertex_type         # String: name of the TO vertex type 
    median: 2.5             # Double: median number of OUTGOING edges, meaning going from each FROM vertex
    sigma: .6               # Double: standard deviation for number of outgoing edges
```
Each `vertex_type` must map directly to a name of an existing vertex in the schema
Each `property` type must correspond to one of the supported types by Aerospike:
`Long, Int, Integer, Double, Bool, Boolean, String, Date`
