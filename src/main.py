import argparse

from meta import extend_argparse, create_from_args
from mini_svg import SvgWriter
from xyplot import XYPlot


def main():
  parser = argparse.ArgumentParser(description="Generate SVG plots.")
  extend_argparse(SvgWriter, parser)
  extend_argparse(XYPlot, parser)
  args = parser.parse_args()
  print(create_from_args(args, XYPlot))
  print(create_from_args(args, SvgWriter))


if __name__ == "__main__":
  main()
