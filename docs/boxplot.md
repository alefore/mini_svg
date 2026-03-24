# BoxPlot

## Introduction

Creates a series of BoxPlot graphs, visualizing distributions at a glance:

Input data format:
[distributions](data_formats.md#Distributions)

## Examples

![BoxPlot example](/examples/boxplot.svg?raw=true "BoxPlot example")

[source](/examples/boxplot.json)

## Default values

* `x_axis_values.max_count`: Defaults to 0 (don't show any ticks on X).
* `domain.x1` and `domain.x2`:
  Computed from the number of distributions.
  You probably won't want to set these parameters.
* `domain.y1` and `domain.y2`:
  Computed from the distributions' min and max values.
  Set them if you want a different Y axis.

## CSS

The following objects use the following classes:

* Main box (rectangle): `boxplot`.
* Line representing the median: `boxplot-median`.
* Text labels (under each box): `boxplot-label`.
* The whiskers (lines): `boxplot-whisker`,
  `boxplot-whisker-span` (for the vertical line),
  `boxplot-whisker-end` (for the horizontal lines at the top and bottom).
