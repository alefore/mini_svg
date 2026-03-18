from dataclasses import dataclass

from meta import value_with_default


@dataclass(frozen=True)
class Margins:
  top: float = 0
  right: float = 0
  bottom: float = 0
  left: float = 0


@dataclass(frozen=True)
class Box:
  x1: float | None = None
  y1: float | None = None
  x2: float | None = None
  y2: float | None = None

  def with_defaults(self, defaults: "Box") -> "Box":
    return Box(
        x1=value_with_default(self.x1, defaults.x1),
        y1=value_with_default(self.y1, defaults.y1),
        x2=value_with_default(self.x2, defaults.x2),
        y2=value_with_default(self.y2, defaults.y2))

  def width(self) -> float:
    assert self.x1 is not None
    assert self.x2 is not None
    return abs(self.x2 - self.x1)

  def height(self) -> float:
    assert self.y1 is not None
    assert self.y2 is not None
    return abs(self.y2 - self.y1)

  def with_margins(self, margins: Margins) -> "Box":
    assert self.x1 is not None
    assert self.x2 is not None
    assert self.y1 is not None
    assert self.y2 is not None
    if self.y1 < self.y2:
      return Box(self.x1 + margins.left, self.y1 + margins.bottom,
                 self.x2 - margins.right, self.y2 - margins.top)
    return Box(self.x1 + margins.left, self.y1 - margins.bottom,
               self.x2 - margins.right, self.y2 + margins.top)

  def with_y_reversed(self) -> "Box":
    assert self.x1 is not None
    assert self.x2 is not None
    assert self.y1 is not None
    assert self.y2 is not None
    return Box(self.x1, self.y2, self.x2, self.y1)


def simple_box(width: float, height: float) -> Box:
  return Box(0, 0, width, height)


DEFAULT_BOX = simple_box(1.0, 1.0)
