# Overview
This generator will create Power-Law distributed graphs based on specifications made in the config.yaml
with support for multi-type graph schemas.

# Startup
Edit the yaml with your edge and vertex types, refer to the `Property Schema`, `Edge Schemas`, and `Vertex Schemas` sections for guidance.
Tune the config options to your specifications, refer to `Config Options` section for guidance.
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

## Property Schema
When defining a property for both Vertices, and Edges, it must be declared in the `properties` dictionary.
Each property will contain their own properties, such as `type` which will be present in all properties, and
unique specifications based off the `type` property to constrain how the values are generated.
```yaml
vertices:
  vertex_name:
    properties:               # <-- Dict of properties
      prop_1:                 # <-- Dict of property specifications
        type:                 # <-- String name of property type
        unique_type_prop_1:   # <-- Unique property, type varies
        unique_type_prop_2:   # <-- Unique property, type varies
    percent:
```
Each `property`'s `type` must correspond to one of the supported types by Aerospike Graph:
`Long, Int, Integer, Double, Bool, Boolean, String, Date, List`
More on that here: https://aerospike.com/docs/graph/develop/data-loading/csv-format/

The `type` unique properties are as follows:

### Long
Longs are constrained to allowable values of `-2^63 to 2^63-1`
```yaml
Long_Property:
    type: Long
    max: 9223372036854775807
    min: 20
```
### Integer
Integers can be declared with the type name of either `Integer` or `Int`
Integers are constrained to allowable values of `-2^31 to 2^31-1`
```yaml
Integer_Property:
    type: Integer
    max: 89412
    min: 20
```
### Double
Doubles are constrained to allowable values of a 64-bit IEEE 754 floating point
```yaml
Double_Property:
    type: Double
    max: 1954.721
    min: 67.01
```
### Boolean
Booleans can be declared with the type name of either `Bool` or `Boolean`
`true_chance` is a float between 0 and 100 describing the chance of the value being true
```yaml
type: Boolean
true_chance: 15
```
### String
Any valid string value is accepted
`max_size` and `min_size` are the bounds for the size of the string
`allowed_chars` is a string including all possible chars for the string generation, leaving the value as an empty string will default to all chars being allowed
```yaml
String_Properties:
    type: String
    max_size: 8
    min_size: 2
    allowed_chars: "!@#$%^&*()_+}{:></;?"
```
### Date
Dates will be output as a ISO-8601 format of `YYYY-MM-DD`
```yaml
Date_Property:
  max_year: 2025
  min_year: 1932
```
### List
Lists may only contain a single type of element
Lists may not be nested
The `element` property of a list, will be the dictionary of the element type it contains, with all their properties
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

## Vertex Schemas
Under the `vertices` property, create a record for each vertex type.
Each vertex type should have the following properties:
```YAML
vertices:
  Vertex_Name:                                  # String: Name of the Vertex, this will also be the folder name
    properties:                                 # Dict <String>: properties of the edge
      property1:
        type: String
        max_size: 8
        min_size: 2
        allowed_chars: "aeiou123450^&*(_+{}:"
      property2:
        type: Long
        max: 9223372036854775807
        min: 20
      property3:
        type: Boolean
        true_chance: 15
      property4:
        type: List
        min_length: 0
        max_length: 100
        element:
          type: String
          max_size: 8
          min_size: 2
          allowed_chars: "!@#$%^&*()_+}{:></;?"
    percent: 25                                 # Integer: percent of overall node count        
```

The total of all percent properties should add up to 100
Each `property` type must correspond to one of the supported types by Aerospike:
`Long, Int, Integer, Double, Bool, Boolean, String, Date`
## Edge Schemas
Under the `edges` property, create a record for each edge type.
Best practice for naming an Edge is using the Composite Naming pattern, adding two underscores which looks like 
`VertType1_EdgeLabel_VertType2`
Each edge type should have the following properties:
```yaml
edges:
    VertType1_EdgeLabel_VertType2:  # String: name of the edge, will also be the folder name
      properties:                   # List <String>: properties of the edge
          profit_margin:
            type: Double
            max: 2.8
            min: 0
            available_stock:
              type: Int
              max: 500000
              min: 0
      from: vertex_type           # String: name of the vertex type the edge will come from
      to: vertex_type             # String: name of the vertex type the edge will go to
      median: 6                   # Double: median number of OUTGOING edges, meaning going from each FROM vertex
      sigma: 3                    # Double: standard deviation for number of outgoing edges
```
Each `vertex_type` must map directly to a name of an existing vertex in the schema