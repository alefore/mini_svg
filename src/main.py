import argparse
import collections
from dataclasses import dataclass
import json
import pathlib
import sys
from typing import Any, cast

from meta import create_from_json_data
from mini_svg import boxplot, histogram, lineplot, scatterplot
from svg_writer import SvgWriter
from xyplot import XYPlot


def read_distributions(data_path: pathlib.Path) -> dict[str, list[float]]:
  data = collections.defaultdict(list)
  with open(data_path, 'r') as f:
    for line in f:
      parts = line.split()
      assert len(parts) == 2
      data[parts[0]].append(float(parts[1]))
  return data


def read_functions(
    data_path: pathlib.Path) -> dict[str, list[tuple[float, float]]]:
  data: dict[str, list[tuple[float, float]]] = collections.defaultdict(list)
  with open(data_path, 'r') as f:
    for line in f:
      parts = line.split()
      assert len(parts) == 3
      data[parts[0]].append((float(parts[1]), float(parts[2])))
  return data


def _boxplot(config_data: Any) -> None:

  @dataclass(frozen=True)
  class Config:
    writer: SvgWriter
    plot: XYPlot = XYPlot()
    data_path: pathlib.Path = pathlib.Path("/dev/stdin")

  config = create_from_json_data(Config, config_data)
  boxplot(config.writer, config.plot, data=read_distributions(config.data_path))


def _histogram(config_data: Any) -> None:

  @dataclass(frozen=True)
  class HistogramConfig:
    writer: SvgWriter | None
    plot: XYPlot = XYPlot()
    bins: int = 10
    data_path: pathlib.Path = pathlib.Path("/dev/stdin")

  config = create_from_json_data(HistogramConfig, config_data)
  histogram(
      config.writer,
      config.plot,
      data=read_distributions(config.data_path),
      bins=config.bins)


def _lineplot(config_data: Any) -> None:

  @dataclass(frozen=True)
  class Config:
    writer: SvgWriter | None
    plot: XYPlot = XYPlot()
    data_path: pathlib.Path = pathlib.Path("/dev/stdin")

  config = create_from_json_data(Config, config_data)
  lineplot(config.writer, config.plot, read_functions(config.data_path))


def _scatterplot(config_data: Any) -> None:

  @dataclass(frozen=True)
  class ScatterplotConfig:
    writer: SvgWriter | None
    plot: XYPlot = XYPlot()
    data_path: pathlib.Path = pathlib.Path("/dev/stdin")

  config = create_from_json_data(ScatterplotConfig, config_data)
  scatterplot(config.writer, config.plot, data=read_functions(config.data_path))


def main() -> None:
  parser = argparse.ArgumentParser(description="Generate SVG plots.")

  parser.add_argument(
      "config", type=argparse.FileType('r'), help="Path to JSON config.")

  args = parser.parse_args()

  with args.config as f:
    try:
      config_data = json.loads(f.read())
    except json.JSONDecodeError as e:
      parser.error(f"{f.name}: Invalid JSON in config: {e}")

  HANDLERS = {
      "boxplot": _boxplot,
      "histogram": _histogram,
      "lineplot": _lineplot,
      "scatterplot": _scatterplot
  }
  if len(config_data) != 1:
    parser.error(f"{f.name}: Too many entries in config (expected at most 1).")
  plot_type = list(config_data)[0]
  HANDLERS[plot_type](config_data[plot_type])


if __name__ == "__main__":
  main()
