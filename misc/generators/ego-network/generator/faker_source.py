from __future__ import annotations
from dataclasses import dataclass, field
import ast, random
from typing import Tuple, Any, List, Dict, Iterator, Optional
from faker import Faker
from datetime import date
import math, sys


AEROSPIKE_GRAPH_TYPES = {
    "long", "int", "integer", "double", "bool", "boolean", "string", "date", "list"
}
INT_MIN, INT_MAX = -2**31, 2**31 - 1
LONG_MIN, LONG_MAX = -2**63, 2**63 - 1
DOUBLE_MIN, DOUBLE_MAX = -sys.float_info.max, sys.float_info.max


def _is_iso_date_string(s: str) -> bool:
    # strict date-only check (YYYY-MM-DD)
    try:
        if len(s) < 10:
            return False
        date.fromisoformat(s[:10])
        return len(s) == 10 or s[10:].strip() == ""
    except Exception:
        return False


def _sample_values(method: str,
                   args: List[Any],
                   kwargs: Dict[str, Any],
                   fake: Optional[Faker],
                   pool: Optional[List[Any]],
                   n_checks: int = 8) -> List[Any]:
    """
    Pick up to n_checks samples, preferring pool entries.
    If pool has fewer than n_checks, top up by drawing from Faker.
    """
    out: List[Any] = []
    if pool:
        k = min(n_checks, len(pool))
        if k <= len(pool):
            out.extend(random.sample(pool, k))
        else:
            out.extend(pool[:])
    need = n_checks - len(out)
    if need > 0 and fake is not None:
        meth = getattr(fake, method, None)
        if not callable(meth):
            raise ValueError(f"Faker has no method '{method}'")
        out.extend(meth(*args, **kwargs) for _ in range(need))
    return out


def validate_faker_int(method: str, args: List[Any], kwargs: Dict[str, Any],
                       fake: Optional[Faker], pool: Optional[List[Any]]):
    max_value = kwargs.get("max_value")
    min_value = kwargs.get("min_value")
    if max_value:
        if max_value < INT_MIN:
            raise ValueError(f"Max value of int method {method} is out of bounds (less then {INT_MIN})")
        if max_value > INT_MAX:
            raise ValueError(f"Min value of int method {method} is out of bounds (greater then {INT_MAX})")
    if min_value:
        if min_value < INT_MIN:
            raise ValueError(f"Min value of int method {method} is out of bounds (less then {INT_MIN})")
        if min_value > INT_MAX:
            raise ValueError(f"Min value of int method {method} is out of bounds (greater then {INT_MAX})")

    for i, v in enumerate(_sample_values(method, args, kwargs, fake, pool)):
        if not isinstance(v, int) or isinstance(v, bool):
            raise TypeError(f"[{i}] expected int, got {_type_name(v)}: {v!r}")
        if v < INT_MIN or v > INT_MAX:
            raise ValueError(f"[{i}] int of method {method} out of 32-bit range: {v}")


def validate_faker_long(method: str, args: List[Any], kwargs: Dict[str, Any],
                        fake: Optional[Faker], pool: Optional[List[Any]]):
    max_value = kwargs.get("max_value")
    min_value = kwargs.get("min_value")
    if max_value:
        if max_value < LONG_MIN:
            raise ValueError(f"Max value of int method {method} is out of bounds (less then {INT_MIN})")
        if max_value > LONG_MAX:
            raise ValueError(f"Min value of int method {method} is out of bounds (greater then {LONG_MAX})")
    if min_value:
        if min_value < LONG_MIN:
            raise ValueError(f"Min value of int method {method} is out of bounds (less then {LONG_MIN})")
        if min_value > LONG_MAX:
            raise ValueError(f"Min value of int method {method} is out of bounds (greater then {LONG_MAX})")

    for i, v in enumerate(_sample_values(method, args, kwargs, fake, pool)):
        if not isinstance(v, int) or isinstance(v, bool):
            raise TypeError(f"[{i}] expected long (int) from method {method}, got {_type_name(v)}: {v!r}")
        if v < LONG_MIN or v > LONG_MAX:
            raise ValueError(f"[{i}] long from method {method} out of 64-bit range: {v}")


def validate_faker_double(method: str, args: List[Any], kwargs: Dict[str, Any],
                          fake: Optional[Faker], pool: Optional[List[Any]]):
    max_value = kwargs.get("max_value")
    min_value = kwargs.get("min_value")
    if max_value:
        if max_value < DOUBLE_MIN:
            raise ValueError(f"Max value of int method {method} is out of bounds (less then {DOUBLE_MIN})")
        if max_value > DOUBLE_MAX:
            raise ValueError(f"Min value of int method {method} is out of bounds (greater then {DOUBLE_MAX})")
    if min_value:
        if min_value < DOUBLE_MIN:
            raise ValueError(f"Min value of int method {method} is out of bounds (less then {DOUBLE_MIN})")
        if min_value > DOUBLE_MAX:
            raise ValueError(f"Min value of int method {method} is out of bounds (greater then {DOUBLE_MAX})")

    for i, v in enumerate(_sample_values(method, args, kwargs, fake, pool)):
        if not (isinstance(v, (int, float)) and not isinstance(v, bool)):
            raise TypeError(f"[{i}] expected float from method {method}, got {_type_name(v)}: {v!r}")
        fv = float(v)
        if math.isnan(fv) or math.isinf(fv):
            raise ValueError(f"[{i}] float must be finite (no NaN/Inf); got {fv!r} from method {method}")
        if fv < DOUBLE_MIN or fv > DOUBLE_MAX:
            raise ValueError(f"[{i}] float from method {method} out of bounds: {fv!r}")


def validate_faker_date(method: str, args: List[Any], kwargs: Dict[str, Any],
                        fake: Optional[Faker], pool: Optional[List[Any]]):
    for i, v in enumerate(_sample_values(method, args, kwargs, fake, pool)):
        if not isinstance(v, str):
            raise TypeError(f"[{i}] expected ISO date string from method {method}, got {_type_name(v)}: {v!r}")
        if not _is_iso_date_string(v):
            raise ValueError(f"[{i}] not ISO date (YYYY-MM-DD) from method {method}: {v!r}")


def validate_faker_list(method: str, args: List[Any], kwargs: Dict[str, Any],
                        fake: Optional[Faker], pool: Optional[List[Any]]):
    for i, v in enumerate(_sample_values(method, args, kwargs, fake, pool)):
        if not isinstance(v, list):
            raise TypeError(f"[{i}] expected list from method {method}, got {_type_name(v)}: {v!r}")
        if not v:
            continue
        def _scalar_type(x):
            if isinstance(x, (list, tuple, dict, set)):
                return None
            if isinstance(x, bool): return bool
            if isinstance(x, int):  return int
            if isinstance(x, float):return float
            if isinstance(x, str):  return str
            return type(x)
        t0 = _scalar_type(v[0])
        if t0 is None:
            raise ValueError(f"[{i}] nested containers are not allowed; got {_type_name(v[0])} at index 0 from method {method}")
        for j, elt in enumerate(v[1:], start=1):
            tj = _scalar_type(elt)
            if tj is None:
                raise ValueError(f"[{i}] nested containers are not allowed; got {_type_name(elt)} at index {j} from method {method}")
            if tj is not t0:
                raise ValueError(f"[{i}] list must be single element type; got {_type_name(v[0])} then {_type_name(elt)} at index {j} from method {method}")


def validate_faker_output(expected_kind: str,
                          method: str, args: List[Any], kwargs: Dict[str, Any],
                          fake: Optional[Faker], pool: Optional[List[Any]]):
    k = expected_kind.lower()
    if k == "int":    return validate_faker_int(method, args, kwargs, fake, pool)
    if k == "long":   return validate_faker_long(method, args, kwargs, fake, pool)
    if k == "double": return validate_faker_double(method, args, kwargs, fake, pool)
    if k == "date":   return validate_faker_date(method, args, kwargs, fake, pool)
    if k == "list":   return validate_faker_list(method, args, kwargs, fake, pool)
    if k == "string":
        for i, v in enumerate(_sample_values(method, args, kwargs, fake, pool)):
            if not isinstance(v, str):
                raise TypeError(f"[{i}] expected string, got {_type_name(v)}: {v!r} from method {method}")
        return
    if k == "bool":
        for i, v in enumerate(_sample_values(method, args, kwargs, fake, pool)):
            if not isinstance(v, bool):
                raise TypeError(f"[{i}] expected bool, got {_type_name(v)}: {v!r} from method {method}")
        return
    raise ValueError(f"Unsupported property type: {expected_kind!r} from method {method}")

def _ast_to_value(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.List):
        return [_ast_to_value(elt) for elt in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_ast_to_value(elt) for elt in node.elts)
    if isinstance(node, ast.Set):
        return {_ast_to_value(elt) for elt in node.elts}
    if isinstance(node, ast.Dict):
        return {
            _ast_to_value(k): _ast_to_value(v)
            for k, v in zip(node.keys, node.values)
        }

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        val = _ast_to_value(node.operand)
        if not isinstance(val, (int, float)):
            raise ValueError("Unary +/- only allowed on numbers")
        return +val if isinstance(node.op, ast.UAdd) else -val

    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
        left = _ast_to_value(node.left)
        right = _ast_to_value(node.right)
        if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
            raise ValueError("Binary +/- only allowed on numbers")
        return left + right if isinstance(node.op, ast.Add) else left - right
    raise ValueError(f"Unsupported value syntax: {ast.dump(node, include_attributes=False)}")


def _parse_faker_call(call_str: str, predicted_type : str) -> Tuple[str, List[Any], Dict[str, Any]]:
    """Verify that the given faker call is valid"""
    tree = ast.parse(call_str, mode="eval")
    if not isinstance(tree, ast.Expression) or not isinstance(tree.body, ast.Call):
        raise ValueError("Faker call must be a single function call expression")
    call = tree.body
    if not isinstance(call.func, ast.Name):
        raise ValueError("Use an unqualified method name like 'pyint(...)'")
    method = call.func.id
    if predicted_type.lower() not in AEROSPIKE_GRAPH_TYPES:
        raise ValueError(f"Predicted type {predicted_type} for faker call {call_str}, is not an accepted Aerospike Graph Type")
    try:
        args = [ast.literal_eval(a) for a in call.args]
    except Exception as e:
        raise ValueError(f"Only literal positional arguments are allowed: {e}") from e
    kwargs = {}
    for kw in call.keywords:
        if kw.arg is None:
            raise ValueError("**kwargs is not allowed")
        kwargs[kw.arg] = _ast_to_value(kw.value)
    return method, args, kwargs


def _type_name(x: Any) -> str:
    m, n = x.__class__.__module__, x.__class__.__qualname__
    return n if m == "builtins" else f"{m}.{n}"

"""Class that optimizes and handles property generation using Faker Generators"""
@dataclass
class FakerSource:
    call_str: str
    locale: str = "en_US"
    seed: Optional[int] = 1337
    batch_size: int = 1024
    pool_size: int = 0
    predicted_type: str=""
    prefer_unique: bool = False
    _method_name: str = field(init=False, repr=False)
    _args: tuple = field(init=False, repr=False)
    _kwargs: dict = field(init=False, repr=False)
    _fake: Faker = field(init=False, repr=False)
    _method: Any = field(init=False, repr=False)   # bound provider method
    _buf: list = field(default_factory=list, repr=False)
    _pool: Optional[List[Any]] = field(default=None, repr=False)
    _pool_idx: int = field(default=0, repr=False)
    _rng_state: Any = field(default=None, repr=False)
    def __post_init__(self):
        self._method_name, args, kwargs = _parse_faker_call(self.call_str, self.predicted_type)
        self._args, self._kwargs = tuple(args), dict(kwargs)

        self._fake = Faker(self.locale)
        if self.seed is not None:
            Faker.seed(self.seed)

        self._method = getattr(self._fake, self._method_name, None)
        if self._method is None or not callable(self._method):
            raise ValueError(f"Faker has no method '{self._method_name}'")

        if self.pool_size > 0:
            self._pool = [self._method(*self._args, **self._kwargs) for _ in range(self.pool_size)]
            random.Random(self.seed).shuffle(self._pool)  # deterministic order

        validate_faker_output(self.predicted_type, self._method_name, list(self._args), self._kwargs, self._fake, self._pool)


    def _refill(self):
        n = self.batch_size
        m = self._method
        a, kw = self._args, self._kwargs
        out = self._buf
        out.extend(m(*a, **kw) for _ in range(n))


    def _next_value(self):
        if self._pool is not None:
            v = self._pool[self._pool_idx]
            self._pool_idx += 1
            if self._pool_idx == len(self._pool):
                self._pool_idx = 0
            return v

        if not self._buf and self.prefer_unique:
            self._refill()
        return self._buf.pop()


    def __call__(self) -> Any:
        return self._next_value()
    def __iter__(self) -> Iterator[Any]:
        return self
    def __next__(self) -> Any:
        return self._next_value()