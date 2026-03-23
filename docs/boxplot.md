# BoxPlot

## Introduction

Creates a series of BoxPlot graphs, visualizing distributions at a glance:

![BoxPlot example](/examples/boxplot.svg?raw=true "BoxPlot example")

[source](/examples/boxplot.json)

Input data format:
distributions ([details](data_formats.md#Distributions))

## Default values

* `x_axis_values.max_count`: Defaults to 0 (don't show any ticks on X).
* `domain.x1` and `domain.x2`:
  Computed from the number of distributions.
  You probably won't want to set these parameters.
* `domain.y1` and `domain.y2`:
  Computed from the distributions' min and max values.
  Set them if you want a different Y axis.

## CSS

* The main box (rectangle) uses `class=boxplot`.
* The line representing the median uses `class=boxplot-median`.
* The text labels (under each box) use `class=boxplot-label`.
