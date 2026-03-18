import argparse
import collections
from dataclasses import dataclass
import json
import pathlib
import sys
from typing import Any, cast

from meta import create_from_json_data
from mini_svg import SvgWriter, boxplot
from xyplot import XYPlot


@dataclass(frozen=True)
class WriterAndPlot:
  writer: SvgWriter
  plot: XYPlot = XYPlot()
  data_path: pathlib.Path = pathlib.Path("/dev/stdin")


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


def main() -> None:
  parser = argparse.ArgumentParser(description="Generate SVG plots.")

  subparsers = parser.add_subparsers(
      dest="command", required=True, help="Type of plot")

  boxplot_parser = subparsers.add_parser("boxplot", help="Generate a boxplot")
  boxplot_parser.add_argument(
      '--config', type=json_file, help="Path to JSON config.", required=True)

  args = parser.parse_args()

  if args.command == "boxplot":
    plot = create_from_json_data(WriterAndPlot, args.config)
    boxplot(plot.writer, plot.plot, data=read_distributions(plot.data_path))


if __name__ == "__main__":
  main()
