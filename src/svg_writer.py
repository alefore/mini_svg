from dataclasses import dataclass
from functools import singledispatchmethod
import pathlib
from typing import Any, Iterable

from box import Box, simple_box
from meta import with_config
from shape import Circle, Line, Rect, Path, Shape, Text


@dataclass(frozen=True)
class SvgWriter:

  output_path: pathlib.Path = pathlib.Path('/dev/stdout')
  width: float = 400.0
  height: float = 300.0
  css: tuple[pathlib.Path, ...] = ()

  def get_box(self) -> Box:
    return simple_box(self.width, self.height)

  def consume(self, shapes: Iterable[Shape]) -> None:
    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"',
        '  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">',
        f'<svg xmlns:xlink="http://www.w3.org/1999/xlink" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}" xmlns="http://www.w3.org/2000/svg" version="1.1">'
    ]

    if self.css:
      lines += ["<style>"]
      for path in self.css:
        lines += [path.read_text()]
      lines += ["</style>"]

    lines += map(self._write_shape, shapes)
    lines += ["</svg>"]
    with open(self.output_path, "w") as f:
      f.write("\n".join(lines))

  @singledispatchmethod
  def _write_shape(self, arg: Any) -> str:
    raise TypeError(f"Cannot handle type {type(arg)}")

  @_write_shape.register
  def _(self, line: Line) -> str:
    return f'<line x1="{line.x1:.1f}" y1="{line.y1:.1f}" x2="{line.x2:.1f}" y2="{line.y2:.1f}"{line.params.as_text()}/>'

  @_write_shape.register
  def _(self, rect: Rect) -> str:
    return f'<rect x="{rect.x:.1f}" y="{rect.y:.1f}" width="{rect.w:.1f}" height="{rect.h:.1f}"{rect.params.as_text()}/>'

  @_write_shape.register
  def _(self, circle: Circle) -> str:
    contents = f"circle cx='{circle.cx:.1f}' cy='{circle.cy:.1f}' r='{circle.r:.1f}'{circle.params.as_text()}"
    title = circle.params.title
    if title is not None:
      return f"<{contents}><title>{title}</title></circle>"
    else:
      return f"<{contents}/>"

  @_write_shape.register
  def _(self, text: Text) -> str:
    return f"<text x='{text.x:.1f}' y='{text.y}:.1f'{text.params.as_text()}>{text.text}</text>"

  @_write_shape.register
  def _(self, path: Path) -> str:
    return f"<path d='{' '.join(str(p) for p in path.points)}' {path.params.as_text()}/>"


with_svg_writer = with_config(SvgWriter)
