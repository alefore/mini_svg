from dataclasses import dataclass, field
from functools import wraps
import itertools
from typing import Any, Callable, Iterable, Iterator, NewType

ParamsDict = NewType("ParamsDict", dict[str, str])


@dataclass(frozen=True)
class Rect:
  x: float
  y: float
  w: float
  h: float
  params: ParamsDict = field(default_factory=lambda: ParamsDict({}))


@dataclass(frozen=True)
class Line:
  x1: float
  y1: float
  x2: float
  y2: float
  params: ParamsDict = field(default_factory=lambda: ParamsDict({}))


def vertical_line(x: float,
                  y1: float,
                  y2: float,
                  params: ParamsDict | None = None) -> Line:
  return Line(x, y1, x, y2, params or ParamsDict({}))


def horizontal_line(x1: float,
                    x2: float,
                    y: float,
                    params: ParamsDict | None = None) -> Line:
  return Line(x1, y, x2, y, params or ParamsDict({}))


@dataclass(frozen=True)
class Circle:
  cx: float
  cy: float
  r: float
  params: ParamsDict = field(default_factory=lambda: ParamsDict({}))


@dataclass(frozen=True)
class Text:
  text: str
  x: float
  y: float
  params: ParamsDict = field(default_factory=lambda: ParamsDict({}))


Shape = Rect | Line | Circle | Text


class ShapeStream:

  def __init__(self, iterable: Iterable[Shape]) -> None:
    self._it = iterable

  def __iter__(self) -> Iterator[Shape]:
    yield from self._it

  def __add__(self, other: Iterable[Shape]) -> "ShapeStream":
    """Allow: stream_a + stream_b"""
    return ShapeStream(itertools.chain(self._it, other))


def shape_generator(
    func: Callable[..., Iterable[Shape]]) -> Callable[..., ShapeStream]:

  @wraps(func)
  def wrapper(*args: Any, **kwargs: Any) -> ShapeStream:
    return ShapeStream(func(*args, **kwargs))

  return wrapper
