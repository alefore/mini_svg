import argparse
import collections
import sys

from meta import extend_argparse, create_from_args
from mini_svg import SvgWriter, boxplot
from xyplot import XYPlot


def main():
  parser = argparse.ArgumentParser(description="Generate SVG plots.")

  subparsers = parser.add_subparsers(
      dest="command", required=True, help="Type of plot")

  boxplot_parser = subparsers.add_parser("boxplot", help="Generate a boxplot")
  extend_argparse(SvgWriter, boxplot_parser)
  extend_argparse(XYPlot, boxplot_parser)

  args = parser.parse_args()

  if args.command == "boxplot":
    data = collections.defaultdict(list)
    for line in sys.stdin:
      parts = line.split()
      assert len(parts) == 2
      data[parts[0]].append(float(parts[1]))
    writer = create_from_args(args, SvgWriter)
    plot = create_from_args(args, XYPlot)
    boxplot(writer, plot, data)


if __name__ == "__main__":
  main()
