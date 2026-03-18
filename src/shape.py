from dataclasses import dataclass, field
from functools import wraps
import itertools
from typing import Any, Callable, Iterable, Iterator, NewType


@dataclass(frozen=True)
class ShapeParams:
  css_class: str | None = None
  title: str | None = None
  transform: str | None = None

  def as_text(self) -> str:
    # title must be handled separately.
    data = {"class": self.css_class, "transform": self.transform}
    return "".join(
        f" {key}='{value}'" for key, value in data.items() if value is not None)


@dataclass(frozen=True)
class Rect:
  x: float
  y: float
  w: float
  h: float
  params: ShapeParams = ShapeParams()


@dataclass(frozen=True)
class Line:
  x1: float
  y1: float
  x2: float
  y2: float
  params: ShapeParams = ShapeParams()

  @classmethod
  def vertical(cls,
               x: float,
               y1: float,
               y2: float,
               params: ShapeParams | None = None) -> "Line":
    return cls(x, y1, x, y2, params or ShapeParams())

  @classmethod
  def horizontal(cls,
                 x1: float,
                 x2: float,
                 y: float,
                 params: ShapeParams | None = None) -> "Line":
    return cls(x1, y, x2, y, params or ShapeParams())


@dataclass(frozen=True)
class Circle:
  cx: float
  cy: float
  r: float
  params: ShapeParams = ShapeParams()


@dataclass(frozen=True)
class Text:
  text: str
  x: float
  y: float
  params: ShapeParams = ShapeParams()


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
