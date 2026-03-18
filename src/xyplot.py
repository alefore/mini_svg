from dataclasses import dataclass
from typing import Iterator

from box import Box, Margins
from meta import value_with_default, with_config
from plot_ticks import PlotTicks, PlotTicksConfig
from point_transformer import PointTransformer, MoveAndScale
from shape import Circle, Line, Rect, Shape, ShapeParams, ShapeStream, Text, shape_generator
from shape_transformer import ShapeTransformer


@dataclass(frozen=True, kw_only=True)
class XYPlot:
  domain: Box = Box()
  output_range: Box = Box()
  margins: Margins | None = None

  x_axis_values: PlotTicksConfig = PlotTicksConfig()
  y_axis_values: PlotTicksConfig = PlotTicksConfig()

  x_label: str | None = None
  y_label: str | None = None

  labels: frozenset[str] = frozenset()

  identity_line: bool | None = None

  @property
  def transformer(self) -> ShapeTransformer:
    assert self.domain is not None
    assert self.output_range is not None
    output = self.output_range.with_y_reversed()
    if self.margins:
      output = output.with_margins(self.margins)
    return ShapeTransformer(MoveAndScale(self.domain, output))

  def with_defaults(self, defaults: "XYPlot") -> "XYPlot":
    return XYPlot(
        domain=self.domain.with_defaults(defaults.domain),
        output_range=self.output_range.with_defaults(defaults.output_range),
        margins=self.margins or defaults.margins,
        x_axis_values=self.x_axis_values.with_defaults(defaults.x_axis_values),
        y_axis_values=self.y_axis_values.with_defaults(defaults.y_axis_values),
        x_label=self.x_label or defaults.x_label,
        y_label=self.y_label or defaults.y_label,
        labels=self.labels or defaults.labels,
        identity_line=value_with_default(self.identity_line,
                                         defaults.identity_line))

  def produce(self) -> ShapeStream:
    return self.transformer(self._draw()) + self._legend()

  def _legend(self) -> Iterator[Shape]:
    assert self.output_range is not None
    for i, key in enumerate(sorted(self.labels)):
      lx = self.output_range.width() - 60
      ly = 20 + (i * 20)
      yield Rect(lx, ly, 10, 10, ShapeParams(css_class=key))
      yield Text(key, lx + 15, ly + 9)

    if self.x_label:
      yield Text(self.x_label,
                 self.output_range.width() / 2, self.output_range.height(),
                 ShapeParams(css_class="label-x"))
    if self.y_label:
      yield Text(
          self.y_label, 15,
          self.output_range.height() / 2,
          ShapeParams(
              css_class="label-y",
              transform=f"rotate(-90 15,{self.output_range.height()/2})"))

  @shape_generator
  def _draw(self) -> Iterator[Shape]:
    assert self.domain is not None
    assert self.output_range is not None
    assert self.domain.x1 is not None
    assert self.domain.x2 is not None
    assert self.domain.y1 is not None
    assert self.domain.y2 is not None
    x_values = self.x_axis_values.build(self.domain.x1, self.domain.x2)
    for x in x_values.values:
      yield Line.vertical(x, self.domain.y1, self.domain.y2,
                          ShapeParams(css_class="tic"))
      span = (self.domain.height() / 50) * (
          self.output_range.width() / self.output_range.height())
      yield Line.vertical(x, -span, 0)
      yield Text(f"{x:{x_values.value_format}}", x, 2 * -span,
                 ShapeParams(css_class="tic-value-x"))

    y_values = self.y_axis_values.build(self.domain.y1, self.domain.y2)
    for y in y_values.values:
      yield Line.horizontal(self.domain.x1, self.domain.x2, y,
                            ShapeParams(css_class="tic"))
      span = self.domain.width() / 50
      yield Line.horizontal(self.domain.x1 - span, self.domain.x1, y)
      yield Text(f"{y:{y_values.value_format}}", self.domain.x1 - 2 * span, y,
                 ShapeParams(css_class="tic-value-y"))

    yield Line.vertical(self.domain.x1, self.domain.y1, self.domain.y2)
    yield Line.horizontal(self.domain.x1, self.domain.x2, self.domain.y1)

    if self.identity_line:
      clip = min(self.domain.x2, self.domain.y2)
      yield Line(0, 0, clip, clip, ShapeParams(css_class="identity-line"))


with_plot_config = with_config(XYPlot)
