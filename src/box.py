from dataclasses import dataclass


@dataclass(frozen=True)
class Margins:
  top: float = 0
  right: float = 0
  bottom: float = 0
  left: float = 0


@dataclass(frozen=True)
class Box:
  x1: float
  y1: float
  x2: float
  y2: float

  def width(self) -> float:
    return abs(self.x2 - self.x1)

  def height(self) -> float:
    return abs(self.y2 - self.y1)

  def with_margins(self, margins: Margins) -> "Box":
    if self.y1 < self.y2:
      return Box(self.x1 + margins.left, self.y1 + margins.bottom,
                 self.x2 - margins.right, self.y2 - margins.top)
    return Box(self.x1 + margins.left, self.y1 - margins.bottom,
               self.x2 - margins.right, self.y2 + margins.top)

  def with_y_reversed(self) -> "Box":
    return Box(self.x1, self.y2, self.x2, self.y1)


def simple_box(width: float, height: float) -> Box:
  return Box(0, 0, width, height)


DEFAULT_BOX = simple_box(1.0, 1.0)
