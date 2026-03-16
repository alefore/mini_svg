from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from functools import singledispatchmethod, wraps
import itertools
import math
import pathlib
import re
import statistics
from typing import Any, Callable, Iterable, Iterator, NamedTuple, NewType


class PointTransformer(ABC):

  @abstractmethod
  def transform(self, x: float, y: float) -> tuple[float, float]:
    pass


class NoopTransformer(PointTransformer):

  def transform(self, x: float, y: float) -> tuple[float, float]:
    return x, y


class PointTranslate(PointTransformer):

  def __init__(self, dx: float, dy: float):
    self.dx, self.dy = dx, dy

  def transform(self, x: float, y: float) -> tuple[float, float]:
    return x + self.dx, y + self.dy


class PointScale(PointTransformer):

  def __init__(self, sx: float, sy: float):
    self.sx, self.sy = sx, sy

  def transform(self, x: float, y: float) -> tuple[float, float]:
    return x * self.sx, y * self.sy


class ComposeTransformers(PointTransformer):

  def __init__(self, transformers: list[PointTransformer]):
    self._transformers = transformers

  def transform(self, x: float, y: float) -> tuple[float, float]:
    for t in self._transformers:
      x, y = t.transform(x, y)
    return x, y


ParamsDict = NewType("ParamsDict", dict[str, str])


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

  def __iter__(self):
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


def MoveAndScale(domain: Box, range: Box) -> ShapeTransformer:
  "Returns a new delegate where drawing is constrained to the box given."

  to_origin = PointTranslate(-domain.x1, -domain.y1)

  sx = (range.x2 - range.x1) / (domain.x2 - domain.x1)
  sy = (range.y2 - range.y1) / (domain.y2 - domain.y1)
  scale = PointScale(sx, sy)

  to_output = PointTranslate(range.x1, range.y1)

  return ShapeTransformer(ComposeTransformers([to_origin, scale, to_output]))


@dataclass(frozen=True)
class PlotTicks:
  values: frozenset[float]
  value_format: str


def value_with_default(value, default):
  if value is not None:
    return value
  return default


@dataclass(frozen=True)
class PlotTicksConfig:
  # List of values where tics should be drawn. If given, all other fields are
  # ignored.
  values: frozenset[float] | None = None

  # Do not draw more than this number of tics.
  max_count: int | None = None

  # Minimum distance between tics.
  min_distance: float | None = None

  value_format: str | None = None

  def with_defaults(self, defaults: "PlotTicksConfig") -> "PlotTicksConfig":
    return PlotTicksConfig(
        values=value_with_default(self.values, defaults.values),
        max_count=value_with_default(self.max_count, defaults.max_count),
        min_distance=value_with_default(self.min_distance,
                                        defaults.min_distance),
        value_format=value_with_default(self.value_format,
                                        defaults.value_format))

  def _find_base(self, low: float, high: float) -> float:
    """Returns the ideal distance between tics."""
    assert low < high
    max_count = value_with_default(self.max_count, 10)
    assert max_count > 0
    assert not self.values
    rough_distance = (high - low) / max_count
    if self.min_distance:
      rough_distance = max(rough_distance, self.min_distance)
    power_of_10 = 10**math.floor(math.log10(rough_distance))
    for factor in [1, 2, 5, 10]:
      candidate: float = power_of_10 * factor
      count = (high - max(low, 0)) // candidate  # Positive tics.
      if low <= 0:
        count += 1  # For zero.
        if low < 0:
          count += abs(low) // candidate  # Negative tics.
      if count <= max_count and (not self.min_distance or
                                 candidate >= self.min_distance):
        return candidate
    assert False

  def _get_values(self, low: float, high: float,
                  base: float) -> frozenset[float]:
    """Returns a list with the values where tics should be drawn."""
    assert low < high
    if self.values is not None:
      return self.values
    max_count = value_with_default(self.max_count, 10)
    if max_count <= 0:
      return frozenset()
    assert base != 0
    first_tic: float = math.ceil(low / base) * base
    if first_tic > high:
      return frozenset()
    return frozenset(
        first_tic + k * base
        for k in range(min(max_count,
                           int((high - first_tic) / base) + 1)))

  def _get_fmt(self, low: float, high: float, base: float) -> str:
    if self.value_format:
      return self.value_format
    return "d" if base > 1 else f".{abs(math.floor(math.log10(base)))}f"

  def build(self, low: float, high: float) -> PlotTicks:
    max_count = value_with_default(self.max_count, 10)
    if max_count <= 0:
      return PlotTicks(values=frozenset(), value_format="ignored")
    if self.values:
      sorted_values = sorted(self.values)
      base = sorted_values[1] - sorted_values[0]
      return PlotTicks(
          values=self.values, value_format=self._get_fmt(low, high, base))
    base = self._find_base(low, high)
    return PlotTicks(
        values=self._get_values(low, high, base),
        value_format=self._get_fmt(low, high, base))


@dataclass(frozen=True, kw_only=True)
class _XYPlot:
  domain: Box | None = None
  output_range: Box | None = None
  margins: Margins | None = None

  x_axis_values: PlotTicksConfig = PlotTicksConfig()
  y_axis_values: PlotTicksConfig = PlotTicksConfig()

  x_label: str | None = None
  y_label: str | None = None

  labels: frozenset[str] = frozenset()

  identity_line: bool | None = None

  @property
  def transformer(self) -> ShapeTransformer:
    assert self.domain
    assert self.output_range
    assert self.margins
    return MoveAndScale(
        self.domain,
        self.output_range.with_y_reversed().with_margins(self.margins))

  def with_defaults(self, defaults: "_XYPlot") -> "_XYPlot":
    return _XYPlot(
        domain=self.domain or defaults.domain,
        output_range=self.output_range or defaults.output_range,
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
    assert self.output_range
    for i, key in enumerate(sorted(self.labels)):
      lx = self.output_range.width() - 60
      ly = 20 + (i * 20)
      yield Rect(lx, ly, 10, 10, ParamsDict({"class": key}))
      yield Text(key, lx + 15, ly + 9)

    if self.x_label:
      yield Text(self.x_label,
                 self.output_range.width() / 2, self.output_range.height(),
                 ParamsDict({"class": "label-x"}))
    if self.y_label:
      yield Text(
          self.y_label, 15,
          self.output_range.height() / 2,
          ParamsDict({
              "class": "label-y",
              "transform": f"rotate(-90 15,{self.output_range.height()/2})"
          }))

  @shape_generator
  def _draw(self) -> Iterator[Shape]:
    assert self.domain
    assert self.output_range
    x_values = self.x_axis_values.build(self.domain.x1, self.domain.x2)
    for x in x_values.values:
      yield vertical_line(x, self.domain.y1, self.domain.y2,
                          ParamsDict({"class": "tic"}))
      span = (self.domain.height() / 50) * (
          self.output_range.width() / self.output_range.height())
      yield vertical_line(x, -span, 0)
      yield Text(f"{x:{x_values.value_format}}", x, 2 * -span,
                 ParamsDict({"class": "tic-value-x"}))

    y_values = self.y_axis_values.build(self.domain.y1, self.domain.y2)
    for y in y_values.values:
      yield horizontal_line(self.domain.x1, self.domain.x2, y,
                            ParamsDict({"class": "tic"}))
      span = self.domain.width() / 50
      yield horizontal_line(self.domain.x1 - span, self.domain.x1, y)
      yield Text(f"{y:{y_values.value_format}}", self.domain.x1 - 2 * span, y,
                 ParamsDict({"class": "tic-value-y"}))

    yield vertical_line(self.domain.x1, self.domain.y1, self.domain.y2)
    yield horizontal_line(self.domain.x1, self.domain.x2, self.domain.y1)

    if self.identity_line:
      clip = min(self.domain.x2, self.domain.y2)
      yield Line(0, 0, clip, clip, ParamsDict({"style": "stroke: var(--text)"}))


def with_config(config_class):
  config_fields = {f.name for f in fields(config_class)}

  def decorator(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
      relevant_kwargs = {k: v for k, v in kwargs.items() if k in config_fields}
      remaining_kwargs = {
          k: v for k, v in kwargs.items() if k not in config_fields
      }
      if args and isinstance(args[0], config_class):
        return func(*args, **remaining_kwargs)
      config = config_class(**relevant_kwargs)
      if args and not isinstance(args[0], config_class):
        # Handle `obj.method(...)`. `args` includes `obj`.
        return func(args[0], config, *args[1:], **remaining_kwargs)
      return func(config, *args, **remaining_kwargs)

    return wrapper

  return decorator


with_plot_config = with_config(_XYPlot)


class ShapeProducer(ABC):

  @abstractmethod
  def produce(self, plot: _XYPlot) -> ShapeStream:
    pass


@dataclass(frozen=True)
class SvgWriter:

  output_path: pathlib.Path
  width: float
  height: float
  css: list[pathlib.Path]

  def get_box(self) -> Box:
    return simple_box(self.width, self.height)

  def _get_extra(self, params: ParamsDict) -> str:
    extra_params = ""
    for keyword in ['style', 'class', 'transform']:
      value = params.get(keyword)
      if value:
        extra_params += f" {keyword}='{value}'"
    return extra_params

  def consume(self, shapes: Iterable[Shape]) -> None:
    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"',
        '  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">',
        f'<svg xmlns:xlink="http://www.w3.org/1999/xlink" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}" xmlns="http://www.w3.org/2000/svg" version="1.1">',
    ]

    if self.css:
      lines += ["<style>"]
      for path in self.css:
        lines += [path.read_text()]
      lines += ['</style>']

    lines += map(self._write_shape, shapes)
    lines += ["</svg>"]
    with open(self.output_path, 'w') as f:
      f.write("\n".join(lines))

  @singledispatchmethod
  def _write_shape(self, arg: Any) -> str:
    raise TypeError(f"Cannot handle type {type(arg)}")

  @_write_shape.register
  def _(self, line: Line) -> str:
    extra_params = self._get_extra(line.params)
    return f'<line x1="{line.x1:.1f}" y1="{line.y1:.1f}" x2="{line.x2:.1f}" y2="{line.y2:.1f}"{extra_params}/>'

  @_write_shape.register
  def _(self, rect: Rect) -> str:
    extra_params = self._get_extra(rect.params)
    return f'<rect x="{rect.x:.1f}" y="{rect.y:.1f}" width="{rect.w:.1f}" height="{rect.h:.1f}"{extra_params}/>'

  @_write_shape.register
  def _(self, circle: Circle) -> str:
    extra_params = self._get_extra(circle.params)
    contents = f"circle cx='{circle.cx:.1f}' cy='{circle.cy:.1f}' r='{circle.r:.1f}'{extra_params}"
    title = circle.params.get("title")
    if title:
      return f"<{contents}><title>{title}</title></circle>"
    else:
      return f"<{contents}/>"

  @_write_shape.register
  def _(self, text: Text) -> str:
    extra_params = self._get_extra(text.params)
    return f"<text x='{text.x}' y='{text.y}'{extra_params}>{text.text}</text>"


with_svg_writer = with_config(SvgWriter)

DataDict = NewType("DataDict", dict[str, list[tuple[float, float]]])


@dataclass(frozen=True)
class _Scatterplot(ShapeProducer):
  data: DataDict
  domain: Box

  @shape_generator
  def _draw(self) -> Iterable[Shape]:
    radius = min(self.domain.width(), self.domain.height()) / 30
    for key, points in self.data.items():
      for x, y in points:
        yield Circle(x, y, radius,
                     ParamsDict({
                         "class": key,
                         "title": f"{key}: ({x}, {y})"
                     }))

  def produce(self, plot: _XYPlot) -> ShapeStream:
    plot = plot.with_defaults(
        _XYPlot(domain=self.domain, labels=frozenset(self.data)))
    print(plot)
    return plot.produce() + plot.transformer(self._draw())


@with_svg_writer
@with_plot_config
def scatterplot(writer: SvgWriter, plot: _XYPlot,
                data: dict[str, list[tuple[float, float]]]) -> None:
  all_points = [pt for pts in data.values() for pt in pts]
  all_x = [pt[0] for pt in all_points]
  all_y = [pt[1] for pt in all_points]
  writer.consume(
      _Scatterplot(
          DataDict(data),
          domain=Box(
              min(0, min(all_x)), min(0, min(all_y)), max(all_x),
              max(all_y))).produce(
                  plot.with_defaults(_XYPlot(output_range=writer.get_box()))))


BinElements = NewType("BinElements", int)


@dataclass(frozen=True)
class _Histogram(ShapeProducer):
  binned_data: dict[str, list[BinElements]]

  bin_size: float
  min_value: float
  max_value: float
  max_count: BinElements

  def _draw(self) -> Iterable[Shape]:
    individual_bin_width = self.bin_size * 0.8 / len(self.binned_data)
    for group_index, (label, counts) in enumerate(self.binned_data.items()):
      for bin_index, count in enumerate(counts):
        if count > 0:
          start_range = self.bin_size * bin_index
          yield Rect(
              self.min_value + self.bin_size *
              (bin_index + 0.1 + 0.8 * group_index / len(self.binned_data)), 0,
              individual_bin_width, count, ParamsDict({"class": label.lower()}))

  def produce(self, plot: _XYPlot) -> ShapeStream:
    bin_count = max(len(bins) for bins in self.binned_data.values())
    plot = plot.with_defaults(
        _XYPlot(
            domain=Box(self.min_value, 0, self.max_value, self.max_count),
            y_label="Histogram",
            x_axis_values=PlotTicksConfig(
                values=frozenset(self.min_value + i * self.bin_size
                                 for i in range(0, bin_count, 2))),
            y_axis_values=PlotTicksConfig(min_distance=1),
            labels=frozenset(self.binned_data)))
    return plot.produce() + plot.transformer(self._draw())


@with_svg_writer
@with_plot_config
def histogram(writer: SvgWriter, plot: _XYPlot, bins: int,
              data: dict[str, list[float]]) -> None:
  print(writer)
  print(plot)
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

  max_count = max(max(bins) for bins in binned_data.values())
  writer.consume(
      _Histogram(
          binned_data, bin_size, min_value, max_value, max_count).produce(
              plot.with_defaults(_XYPlot(output_range=writer.get_box()))))


@dataclass(frozen=True)
class _BoxPlotOne:
  label: str
  y_min: float
  y_max: float
  quantiles: tuple[float, float, float]
  min_whisker: float
  max_whisker: float

  @classmethod
  def create(cls, label: str, data: list[float]):
    data = sorted(data)
    q1, median, q3 = statistics.quantiles(data, n=4, method='inclusive')
    iqr = q3 - q1
    fences = [q1 - 1.5 * iqr, q3 + 1.5 * iqr]
    min_whisker = min(x for x in data if x >= fences[0])
    max_whisker = max(x for x in data if x <= fences[1])

    return cls(label, min(data), max(data), (q1, median, q3), min_whisker,
               max_whisker)

  def draw(self, index: int, plot: _XYPlot) -> Iterable[Shape]:
    x = plot.transformer.transformer.transform(index, 0)[0]
    assert plot.output_range
    assert plot.margins
    return plot.transformer(self._shapes(index)) + [
        Text(self.label, x,
             plot.output_range.height() - plot.margins.bottom - 20,
             ParamsDict({"class": "boxplot-label"}))
    ]

  @shape_generator
  def _shapes(self, index) -> Iterable[Shape]:
    q1, median, q3 = self.quantiles
    box_w = 0.7
    yield vertical_line(index, self.min_whisker, self.max_whisker)
    for y in [self.min_whisker, self.max_whisker]:
      yield horizontal_line(index - box_w / 2, index + box_w / 2, y)
    yield Rect(index - box_w / 2, q1, box_w, q3 - q1,
               ParamsDict({"style": "fill: var(--text)"}))
    yield horizontal_line(index - box_w / 2, index + box_w / 2, median,
                          ParamsDict({"style": "stroke: var(--bg-mild)"}))


@dataclass(frozen=True)
class _BoxPlot(ShapeProducer):

  data: dict[str, _BoxPlotOne]
  y_min: float
  y_max: float

  @shape_generator
  def _draw(self, plot: _XYPlot) -> Iterable[Shape]:
    return itertools.chain.from_iterable(
        self.data[key].draw(index, plot)
        for index, key in enumerate(sorted(self.data)))

  def produce(self, plot: _XYPlot) -> ShapeStream:
    plot = plot.with_defaults(
        _XYPlot(
            domain=Box(-1, math.floor(self.y_min), len(self.data),
                       math.ceil(self.y_max)),
            x_axis_values=PlotTicksConfig(max_count=0)))
    return plot.produce() + self._draw(plot)


@with_svg_writer
@with_plot_config
def boxplot(writer: SvgWriter, plot: _XYPlot, data: dict[str,
                                                         list[float]]) -> None:
  box_data = {k: _BoxPlotOne.create(k, v) for k, v in data.items()}
  writer.consume(
      _BoxPlot(box_data, min(d.y_min for d in box_data.values()),
               max(d.y_max for d in box_data.values())).produce(
                   plot.with_defaults(_XYPlot(output_range=writer.get_box()))))
