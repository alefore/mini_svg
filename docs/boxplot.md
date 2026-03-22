# BoxPlot

## Introduction

Creates a series of BoxPlot graphs, visualizing distributions at a glance:

![BoxPlot example](/examples/boxplot.svg?raw=true "BoxPlot example")

[source](/examples/boxplot.json)

* Input data format:
  distributions ([details](data_formats.md#Distributions))

## Default values

* `x_axis_values.max_count`: Defaults to 0 (don't show any ticks on X).
* `domain.x1` and `domain.x2`: Will be set dynamically based on the number
  of distributions. You probably won't want to set them.
* `domain.y1` and `domain.y2`: Will be inferred from the data
  (min and max sample values).
  You may want to overule them to pin the Y axis.

## CSS

* The main box (rectangle) uses `class=boxplot`.
* The line representing the median uses `class=boxplot-median`.
* The text labels (under each box) use `class=boxplot-label`.
