import argparse
import collections
from dataclasses import dataclass
import json
import pathlib
import sys
from typing import Any, cast

from meta import create_from_json_data
from mini_svg import SvgWriter, boxplot, histogram, lineplot
from xyplot import XYPlot


def json_file(path: str) -> dict[str, Any]:
  try:
    with open(path, 'r') as f:
      return cast(dict[str, Any], json.load(f))
  except json.JSONDecodeError as e:
    raise argparse.ArgumentTypeError(
        f"{path} contains invalid JSON: {e}") from e


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


def main() -> None:
  parser = argparse.ArgumentParser(description="Generate SVG plots.")

  parser.add_argument(
      '--config', type=json_file, help="Path to JSON config.", required=True)

  args = parser.parse_args()

  HANDLERS = {
      "boxplot": _boxplot,
      "histogram": _histogram,
      "lineplot": _lineplot
  }
  for key, value in HANDLERS.items():
    if key in args.config:
      value(args.config[key])


if __name__ == "__main__":
  main()
