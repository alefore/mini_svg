# mini_svg

Simple py logic to generate SVG visualizations of scientific data
([example graphs](examples/README.md)).

## Plot types

* [BoxPlot](docs/boxplot.md)
* [Scatterplot](docs/scatterplot.md)
* [Histogram](docs/histogram.md)
* [Lineplot](docs/lineplot.md)

## Usage

There's two main interfaces:

* As a command-line which receives parameters from a json file.
  See `.sh` files in [the examples directory](examples/).
* From Python (in-process) through the functions exposed in `mini_svg`.
