# LinePlot

## Introduction

Creates a chart plotting various functions.
Does linear extrapolation across all samples.

![LinePlot example](/examples/lineplot.svg?raw=true "LinePlot example")

[source](/examples/lineplot.json)

* Input data format:
  XY samples ([details](data_formats.md#xy-samples))

## Default values

* `domain`: Set directly from the sample data (min and max values).

## CSS

* Each path (line) has `class` set to
  `lineplot-{name}` (where `name` is the name of the set of samples).
