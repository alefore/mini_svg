from functools import singledispatchmethod
from typing import Any, Iterable

from point_transformer import PointTransformer
from shape import Circle, Line, Rect, Shape, ShapeStream, Text


class ShapeTransformer:

  def __init__(self, transformer: PointTransformer) -> None:
    self.transformer = transformer

  def __call__(self, shapes: Iterable[Shape]) -> ShapeStream:
    return ShapeStream(map(self._handle, shapes))

  @singledispatchmethod
  def _handle(self, arg: Any) -> Shape:
    raise TypeError(f"Cannot handle type {type(arg)}")

  @_handle.register
  def _(self, line: Line) -> Line:
    tx1, ty1 = self.transformer.transform(line.x1, line.y1)
    tx2, ty2 = self.transformer.transform(line.x2, line.y2)
    return Line(tx1, ty1, tx2, ty2, line.params)

  @_handle.register
  def _(self, rect: Rect) -> Rect:
    # Map two points to find the new bounding box
    tx1, ty1 = self.transformer.transform(rect.x, rect.y)
    tx2, ty2 = self.transformer.transform(rect.x + rect.w, rect.y + rect.h)

    # Calculate new top-left and dimensions
    nx, ny = min(tx1, tx2), min(ty1, ty2)
    nw, nh = abs(tx1 - tx2), abs(ty1 - ty2)
    return Rect(nx, ny, nw, nh, rect.params)

  @_handle.register
  def _(self, circle: Circle) -> Circle:
    tx, ty = self.transformer.transform(circle.cx, circle.cy)
    return Circle(
        tx, ty,
        abs(
            self.transformer.transform(circle.cx + circle.r, circle.cy)[0] -
            tx), circle.params)

  @_handle.register
  def _(self, text: Text) -> Text:
    tx, ty = self.transformer.transform(text.x, text.y)
    return Text(text.text, tx, ty, text.params)
