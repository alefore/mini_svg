from abc import ABC, abstractmethod
import collections
from dataclasses import dataclass, field, fields
from functools import singledispatchmethod
import itertools
import math
import re
import statistics
from typing import Any, Callable, Iterable, Iterator, NamedTuple, NewType, Protocol, TypeVar, cast

from meta import value_with_default, with_config
from plot_ticks import PlotTicks, PlotTicksConfig
from box import Margins, Box, simple_box
from shape import Circle, Line, Rect, Path, PathPoint, Shape, ShapeParams, ShapeStream, Text, shape_generator
from xyplot import XYPlot, with_plot_config
from svg_writer import SvgWriter, with_svg_writer


def get_domain(points_it: Iterable[tuple[float, float]]) -> Box:
  all_points = list(points_it)
  all_x = [pt[0] for pt in all_points]
  all_y = [pt[1] for pt in all_points]
  return Box(x1=min(all_x), y1=min(all_y), x2=max(all_x), y2=max(all_y))


@with_svg_writer
@with_plot_config
def scatterplot(writer: SvgWriter, plot: XYPlot,
                data: dict[str, list[tuple[float, float]]]) -> None:
  all_points = [pt for pts in data.values() for pt in pts]
  all_x = [pt[0] for pt in all_points]
  all_y = [pt[1] for pt in all_points]
  plot = plot.with_defaults(
      XYPlot(
          output_range=writer.get_box(),
          domain=Box(
              min(0, min(all_x)), min(0, min(all_y)), max(all_x), max(all_y)),
          labels=frozenset(data)))

  shapes: list[Shape] = []
  # There's a subtlety here: the radius will get transformed by ShapeTransformer
  # based on the `x` axis. So we use the `width`.
  radius = plot.domain.width() / 60
  for key, points in data.items():
    for x, y in points:
      shapes.append(
          Circle(x, y, radius,
                 ShapeParams(css_class=key, title=f"{key}: ({x}, {y})")))

  writer.consume(plot.produce() + plot.transformer(shapes))


BinElements = NewType("BinElements", int)


@with_svg_writer
@with_plot_config
def histogram(writer: SvgWriter, plot: XYPlot, bins: int,
              data: dict[str, list[float]]) -> None:
  all_values = [v for obs in data.values() for v in obs]
  min_value, max_value = min(all_values), max(all_values)
  bin_size = (max_value - min_value) / bins

  binned_data: dict[str, list[BinElements]] = dict()
  for label, values in data.items():
    counts: list[BinElements] = [BinElements(0)] * bins
    for v in values:
      index = int((v - min_value) / bin_size)
      if index == bins:
        index -= 1
      counts[index] = BinElements(counts[index] + 1)
    binned_data[label] = counts

  max_count = max(max(bins_list) for bins_list in binned_data.values())
  bin_count = max(len(bins_list) for bins_list in binned_data.values())
  plot = plot.with_defaults(
      XYPlot(
          output_range=writer.get_box(),
          domain=Box(min_value, 0, max_value, max_count),
          y_label="Histogram",
          x_axis_values=PlotTicksConfig(
              values=frozenset(
                  min_value + i * bin_size for i in range(bin_count))),
          y_axis_values=PlotTicksConfig(min_distance=1),
          labels=frozenset(binned_data)))

  shapes: list[Shape] = []
  individual_bin_width = bin_size * 0.8 / len(binned_data)
  for group_index, (label, counts) in enumerate(binned_data.items()):
    for bin_index, count in enumerate(counts):
      if count > 0:
        shapes.append(
            Rect(
                min_value + bin_size *
                (bin_index + 0.1 + 0.8 * group_index / len(binned_data)),
                0, individual_bin_width, count,
                ShapeParams(css_class=label.lower())))

  writer.consume(plot.produce() + plot.transformer(shapes))


@dataclass(frozen=True)
class _BoxPlotOne:
  label: str
  y_min: float
  y_max: float
  quantiles: tuple[float, float, float]
  min_whisker: float
  max_whisker: float

  @classmethod
  def create(cls, label: str, data: list[float]) -> "_BoxPlotOne":
    data = sorted(data)
    q1, median, q3 = statistics.quantiles(data, n=4, method='inclusive')
    iqr = q3 - q1
    fences = [q1 - 1.5 * iqr, q3 + 1.5 * iqr]
    min_whisker = min(x for x in data if x >= fences[0])
    max_whisker = max(x for x in data if x <= fences[1])

    return cls(label, min(data), max(data), (q1, median, q3), min_whisker,
               max_whisker)

  def draw(self, index: int, plot: XYPlot) -> Iterable[Shape]:
    x = plot.transformer.transformer.transform(index, 0)[0]
    assert plot.output_range
    margins_bottom: float = 0
    if plot.margins:
      margins_bottom = plot.margins.bottom
    return plot.transformer(self._shapes(index)) + [
        Text(self.label, x,
             plot.output_range.height() - margins_bottom - 20,
             ShapeParams(css_class="boxplot-label"))
    ]

  @shape_generator
  def _shapes(self, index: int) -> Iterable[Shape]:
    q1, median, q3 = self.quantiles
    box_w = 0.7
    yield Line.vertical(
        index, self.min_whisker, self.max_whisker,
        ShapeParams(css_class="boxplot-whisker boxplot-whisker-span"))
    for y in [self.min_whisker, self.max_whisker]:
      yield Line.horizontal(
          index - box_w / 2, index + box_w / 2, y,
          ShapeParams(css_class="boxplot-whisker boxplot-whisker-end"))
    yield Rect(index - box_w / 2, q1, box_w, q3 - q1,
               ShapeParams(css_class="boxplot"))
    yield Line.horizontal(index - box_w / 2, index + box_w / 2, median,
                          ShapeParams(css_class="boxplot-median"))


@with_svg_writer
@with_plot_config
def boxplot(writer: SvgWriter, plot: XYPlot, data: dict[str,
                                                        list[float]]) -> None:
  box_data = {k: _BoxPlotOne.create(k, v) for k, v in data.items()}

  plot = plot.with_defaults(
      XYPlot(
          output_range=writer.get_box(),
          domain=Box(-1, min(d.y_min for d in box_data.values()), len(box_data),
                     max(d.y_max for d in box_data.values())),
          x_axis_values=PlotTicksConfig(max_count=0)))

  writer.consume(plot.produce() + itertools.chain.from_iterable(
      box_data[key].draw(index, plot)
      for index, key in enumerate(sorted(box_data))))


@dataclass(frozen=True)
class _LinePlotOne:
  label: str
  data: tuple[tuple[float, float], ...]

  def draw(self, plot: XYPlot) -> Iterable[Shape]:
    count_by_x: dict[float, int] = collections.defaultdict(int)
    for d in set(self.data):
      count_by_x[d[0]] += 1
    repeated_values = {x for (x, count) in count_by_x.items() if count > 1}
    if repeated_values:
      raise ValueError(
          f"{self.label}: Multiple y values for x values: {repeated_values}")
    points: list[PathPoint] = []
    points.append(PathPoint("M", self.data[0][0], self.data[0][1]))
    for point in self.data[1:]:
      points.append(PathPoint("L", point[0], point[1]))
    yield Path(tuple(points), ShapeParams(css_class=f"lineplot-{self.label}"))


@with_svg_writer
@with_plot_config
def lineplot(writer: SvgWriter, plot: XYPlot,
             data: dict[str, list[tuple[float, float]]]) -> None:
  line_data = {k: _LinePlotOne(k, tuple(sorted(v))) for k, v in data.items()}
  plot = plot.with_defaults(
      XYPlot(
          output_range=writer.get_box(),
          labels=frozenset(line_data),
          domain=get_domain(itertools.chain.from_iterable(data.values()))))
  writer.consume(plot.produce() + itertools.chain.from_iterable(
      plot.transformer(line_data[key].draw(plot)) for key in sorted(line_data)))
