## Development principles

* Classes should generally be immutable.

  * Prefer @dataclass(frozen=True) over NamedTuple.

* All functions should have static type annotations.

* Graphs should be generated as a stream of shapes.

* The public interfaces should try to hide implementation details.
  They should simply receive parameters, defined in terms of intent.
  Meet the users where they are.

* Graphs should be expressed using SVG primitives as cleanly as possible.
