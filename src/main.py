from abc import ABC
import argparse
import collections
import datetime
from dataclasses import dataclass
import json
import pathlib
from typing import Any, cast, Callable

import file_watcher
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
    for index, line in enumerate(f):
      try:
        parts = line.split()
        if len(parts) != 3:
          raise ValueError(f"Unable to break into 3 parts")
        data[parts[0]].append((float(parts[1]), float(parts[2])))
      except Exception as e:
        raise ValueError(f"{data_path}:{index+1}: Invalid line: {e}") from e
  return data


def watch(writer: SvgWriter | None, data: pathlib.Path,
          watcher: file_watcher.FileWatcher) -> None:
  if writer:
    for path in writer.css:
      watcher.add_file(path)
  watcher.add_file(data)


def _boxplot(config_data: Any, watcher: file_watcher.FileWatcher) -> None:

  @dataclass(frozen=True)
  class BoxPlot:
    writer: SvgWriter
    plot: XYPlot = XYPlot()
    data_path: pathlib.Path = pathlib.Path("/dev/stdin")

  config = create_from_json_data(BoxPlot, config_data)
  watch(config.writer, config.data_path, watcher)
  boxplot(config.writer, config.plot, data=read_distributions(config.data_path))


def _histogram(config_data: Any, watcher: file_watcher.FileWatcher) -> None:

  @dataclass(frozen=True)
  class Histogram:
    writer: SvgWriter | None
    plot: XYPlot = XYPlot()
    bins: int = 10
    data_path: pathlib.Path = pathlib.Path("/dev/stdin")

  config = create_from_json_data(Histogram, config_data)
  watch(config.writer, config.data_path, watcher)
  histogram(
      config.writer,
      config.plot,
      data=read_distributions(config.data_path),
      bins=config.bins)


def _lineplot(config_data: Any, watcher: file_watcher.FileWatcher) -> None:

  @dataclass(frozen=True)
  class LinePlot:
    writer: SvgWriter | None
    plot: XYPlot = XYPlot()
    data_path: pathlib.Path = pathlib.Path("/dev/stdin")

  config = create_from_json_data(LinePlot, config_data)
  watch(config.writer, config.data_path, watcher)
  lineplot(config.writer, config.plot, read_functions(config.data_path))


def _scatterplot(config_data: Any, watcher: file_watcher.FileWatcher) -> None:

  @dataclass(frozen=True)
  class Scatterplot:
    writer: SvgWriter | None
    plot: XYPlot = XYPlot()
    data_path: pathlib.Path = pathlib.Path("/dev/stdin")

  config = create_from_json_data(Scatterplot, config_data)
  scatterplot(config.writer, config.plot, data=read_functions(config.data_path))


def generate(config_path: pathlib.Path,
             watcher: file_watcher.FileWatcher) -> None:
  watcher.add_file(config_path)
  try:
    config_data = json.loads(config_path.read_text())
  except json.JSONDecodeError as e:
    raise RuntimeError(f"{config_path}: Invalid JSON in config: {e}")

  if len(config_data) != 1:
    raise RuntimeError(
        f"{config_path}: Too many entries in config (expected at most 1).")
  plot_type = list(config_data)[0]
  HANDLERS: dict[str, Callable[[Any, file_watcher.FileWatcher], None]] = {
      "boxplot": _boxplot,
      "histogram": _histogram,
      "lineplot": _lineplot,
      "scatterplot": _scatterplot
  }
  HANDLERS[plot_type](config_data[plot_type], watcher)


def main() -> None:
  parser = argparse.ArgumentParser(description="Generate SVG plots.")

  parser.add_argument(
      "--watch", action="store_true", help="Run daemon watching for changes.")
  parser.add_argument("config", type=pathlib.Path, help="Path to JSON config.")

  args = parser.parse_args()

  watcher: file_watcher.FileWatcher = (
      file_watcher.FileWatcherImpl()
      if args.watch else file_watcher.NullFileWatcher())
  generate(args.config, watcher)
  if args.watch:
    print("Will watch\n")
    while True:
      watcher.wait_for_changes()
      generate(args.config, watcher)


if __name__ == "__main__":
  main()
