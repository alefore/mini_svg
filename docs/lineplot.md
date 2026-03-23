# LinePlot

## Introduction

Creates a chart plotting various functions.
Does linear extrapolation across all samples.

Input data format:
[XY samples](data_formats.md#xy-samples)

## Examples

![LinePlot example](/examples/lineplot.svg?raw=true "LinePlot example")

[source](/examples/lineplot.json)

![Timeseries example](/examples/timeseries.svg?raw=true "TimeSeries example")

[source](/examples/timeseries.json)

## Default values

* `domain`: Set directly from the sample data (min and max values).

## CSS

* Each path (line) has `class` set to
  `lineplot-{name}` (where `name` is the name of the set of samples).
