# Histogram

## Introduction

Creates a histogram, visualizing distributions at a glance:

![Histogram example](/examples/histogram.svg?raw=true "Histogram example")

[source](/examples/histogram.json)

* Input data format:
  distributions ([details](data_formats.md#Distributions))

## Custom Parameters

Histogram plots support the following custom parameters:

| Parameter   | Type               | Notes |
|:------------|:-------------------|:------
| `bins`    | `int`        | Specifies the number of bins. Defaults to 10. |

## Default values

* `domain.x1` and `domain.x2`:
  Inferred directly from the data (min and max values across all samples).

* `domain.y1`: 0 (no elements in bucket)

* `domain.y2`: Size of the bucket with the most elements.

* `x_axis_values.values`:
  Computed dynamically setting one tick around every bucket.

* `y_axis_values.min_distance`: 1

* `labels`: Inferred from the data (names of the distributions).

## CSS

* Each rectangle corresponding to a bucket
  sets its `class` to the name of the distribution it represents
  (from the input data).
