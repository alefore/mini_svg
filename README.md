# mini_svg

Simple py/ts logic to generate SVG visualizations of scientific data
([example graphs](examples/README.md)).

The generated images tend to be significantly leaner
than what general (non-SVG specific) plotting software generates.
For example, a simple histogram is:

| Tool | Size | bzip2 Size |
| :--- | ---: | ---: |
| gnuplot | 48K | 4.5K |
| matplotlib.pyplot | 49K | 7.9K |
| **mini_svg** | 4.6K | 1.3K |

## Plot types

* [BoxPlot](docs/boxplot.md)
* [Scatterplot](docs/scatterplot.md)
* [Histogram](docs/histogram.md)
* [Lineplot](docs/lineplot.md)

## Usage

There's two main interfaces.

### Command-line

As a command-line which receives parameters from a json file.
See `.sh` files in [the examples directory](examples/).

### Python (in-process)

Call the functions exposed in module `mini_svg`.

### TypeScript (in-browser)

Install:

    npm install git+https://github.com/alefore/mini_svg.git

TODO: More information is missing here.

## Caveats

Type TypeScript implementation is experimental.
