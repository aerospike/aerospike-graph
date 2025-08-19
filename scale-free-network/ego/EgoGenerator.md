# Ego Networks
Disjoint Islands
can make type a faker input

## Tasks:
- Partition upgrades based on feedback for distribution from Ishaan
- finish node sharing flag

## Step 3: then introduce more complex distributions and faker properties etc

### MVP Candidate Configs

### Generation Algorithm
adding to buffer:
Create Center Ego Node with properties
sample k of each in connections alter coming from the ego, then write them and their edges
    For each partner, go through other alters and sample and create them
keep in a list with CSV, Writer, Buffer

Write to CSVs

This generator accepts properties as faker functions for full user customizability.
Each property takes only `type`, and `generator`, with `type` being the object type, and `generator` being a
faker function call.
```yaml
      property:
        generator: pybool(0.8)
        type: bool
```

The only exception to this is the List type which takes an additional input of `element_type`,
which is the single type of element
```yaml
      property:
        type: List
        element_type: string
        generator: pylist(nb_elements=15, allowed_types=[str])
```

### Type Constraints:
Types must be supported by Aerospike Graph, supported type names are as follows:
`"long", "int", "integer", "double", "bool", "boolean", "string", "date", "list"`
In python, longs and ints are both treated as python ints, and doubles are treated as python floats.

#### Int
must be within `INT_MIN, INT_MAX = -2147483648, 2147483647`

Example Faker Function:
```
    pyint(min_value=-2147483648, max_value=2147483647)
```

#### Long
must be within `LONG_MIN, LONG_MAX = -9223372036854775808, 9223372036854775807`

Example Faker Function:
```
    pyint(min_value=-9223372036854775808, max_value=9223372036854775807)
```

#### Double
must be a 64-bit IEEE 754 floating point

We can't touch the bounds of the 64-bit IEEE 754 floating point (1.7976931348623157e+308) easily with `faker`'s 
`pyfloat`, if you are needing to reach the bounds in generation, create a wrapper and input something similar to this:
```python
import random
import sys
DBL_MAX = sys.float_info.max
(2.0 * random.random() - 1.0) * DBL_MAX
```

Example Faker Function (not wrapper):
```
    pyfloat(min_value=-1.0000000000000001e14, max_value=1.0000000000000001e14)
```

#### List
Lists must be of single type cardinality, that is, there may only be one element type in the list.
Lists may not be nested.

Example Faker Function:
```
    pylist(nb_elements=15, allowed_types=[str])
```

#### Date
Values must be in ISO-8601 format (for example, YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS, YYYY-MM-DDTHH:MM:SSZ)

Example Faker Function:
```
    date()
```
#### String
Can be any string value. 
Quotation marks are optional.

String gives more flexibility, since there are many faker functions such as `company()` and `building()` that have more
realistic outputs.
Example Faker Functions:
```
    pystr(min_chars=5, max_chars=10)
    company()
```

#### Bool
Both `False/True` and `false/true` are accepted in the bulk loader, so no need to worry about conversion

```
    pybool(0.8)
```