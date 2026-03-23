# Histogram

## Introduction

Creates a histogram, visualizing distributions at a glance:

Input data format:
[distributions](data_formats.md#Distributions)

## Examples

![Histogram example](/examples/histogram.svg?raw=true "Histogram example")

[source](/examples/histogram.json)

## Custom Parameters

Histogram plots support the following custom parameters:

| Parameter   | Type               | Notes |
|:------------|:-------------------|:------
| `bins`    | `int`        | Specifies the number of bins. Defaults to 10. |

## Default values

* `domain.x1` and `domain.x2`:
  Inferred directly from the data (min and max values across all samples).
* `domain.y1`: 0 (no elements in bin)
* `domain.y2`: Size of the tallest bin.
* `x_axis_values.values`:
  Computed dynamically, setting ticks around each bin.
* `y_axis_values.min_distance`: 1

## CSS

* Each rectangle corresponding to a bin
  has `class` set to the name of the distribution it represents
  (from the input data).
