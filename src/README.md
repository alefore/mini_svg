## Development principles

* Most classes are immutable.

  * Prefer @dataclass(frozen=True) over NamedTuple.

* All functions must have static type annotations.

* Graphs should be generated as a stream of shapes.

* Graphs should be expressed using SVG primitives as cleanly as possible.
