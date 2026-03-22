# Input data

SVG reads data from plain-text (human readable) files
with a data point per line.

## Distributions

A distributions file contains various distributions.
Each distribution is a sample of numbers (which may be repeated).

Each line contains the name of a set and a single value ([example](/examples/distribution.txt)).

Used by:

* [boxplot](boxplot.md)
* [histogram](histogram.md)

## XY samples

A XY-samples file contains various samples of points on the XY plane.

Each line contains the name of a sample
followed by the x and y values
([example](/examples/function_sample.txt)).

Used by:

* [lineplot](lineplot.md)
* [scatterplot](scatterplot.md)
