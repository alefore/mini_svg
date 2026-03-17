from abc import ABC, abstractmethod

from box import Box


class PointTransformer(ABC):

  @abstractmethod
  def transform(self, x: float, y: float) -> tuple[float, float]:
    pass


class _Translate(PointTransformer):

  def __init__(self, dx: float, dy: float):
    self.dx, self.dy = dx, dy

  def transform(self, x: float, y: float) -> tuple[float, float]:
    return x + self.dx, y + self.dy


class _Scale(PointTransformer):

  def __init__(self, sx: float, sy: float):
    self.sx, self.sy = sx, sy

  def transform(self, x: float, y: float) -> tuple[float, float]:
    return x * self.sx, y * self.sy


class _Compose(PointTransformer):

  def __init__(self, transformers: list[PointTransformer]):
    self._transformers = transformers

  def transform(self, x: float, y: float) -> tuple[float, float]:
    for t in self._transformers:
      x, y = t.transform(x, y)
    return x, y


def MoveAndScale(domain: Box, range: Box) -> PointTransformer:
  "Returns a new delegate where drawing is constrained to the box given."

  to_origin = _Translate(-domain.x1, -domain.y1)

  sx = (range.x2 - range.x1) / (domain.x2 - domain.x1)
  sy = (range.y2 - range.y1) / (domain.y2 - domain.y1)
  scale = _Scale(sx, sy)

  to_output = _Translate(range.x1, range.y1)

  return _Compose([to_origin, scale, to_output])
