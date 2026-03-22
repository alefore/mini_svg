# BoxPlot

## Introduction

Creates a series of BoxPlot graphs, visualizing distributions at a glance:

![BoxPlot example](/examples/boxplot.svg?raw=true "BoxPlot example")

[source](/examples/boxplot.json)

## Parameters

### Common Parameters

Parameters for `SvgWriter` and `XYPlot` are documented in [Common Parameters](../docs/parameters.md).

### plot.domain (optional)

Optional parameter that can be used to control the y-axis setting.
If absent, y-axis values are inferred from the data.

## Python

```
mini_svg.boxplot(
    data=data,
    margins=mini_svg.Margins(top=10, bottom=10, left=50),
    y_axis_values=mini_svg.PlotTicksConfig(max_count=5),
    y_label="ln(actual / estimate)",
    output_path=pathlib.Path("images/065.svg"),
    width=200,
    height=300,
    css=productivity_tasks.SVG_STYLES)
```
