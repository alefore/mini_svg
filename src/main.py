import argparse
from dataclasses import dataclass
import collections
import sys
import json

from meta import create_from_json_data
from mini_svg import SvgWriter, boxplot
from xyplot import XYPlot


@dataclass(frozen=True)
class WriterAndPlot:
  writer: SvgWriter
  plot: XYPlot


def json_file(path):
  try:
    with open(path, 'r') as f:
      return json.load(f)
  except json.JSONDecodeError as e:
    raise argparse.ArgumentTypeError(
        f"{path} contains invalid JSON: {e}") from e


def main():
  parser = argparse.ArgumentParser(description="Generate SVG plots.")

  subparsers = parser.add_subparsers(
      dest="command", required=True, help="Type of plot")

  boxplot_parser = subparsers.add_parser("boxplot", help="Generate a boxplot")
  boxplot_parser.add_argument(
      '--config', type=json_file, help="Path to JSON config.", required=True)

  args = parser.parse_args()

  if args.command == "boxplot":
    plot = create_from_json_data(WriterAndPlot, args.config)
    data = collections.defaultdict(list)
    for line in sys.stdin:
      parts = line.split()
      assert len(parts) == 2
      data[parts[0]].append(float(parts[1]))
    boxplot(plot.writer, plot.plot, data)


if __name__ == "__main__":
  main()
