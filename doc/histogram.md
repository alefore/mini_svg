# Histogram

## Introduction

Creates a histogram, visualizing distributions at a glance:

![Histogram example](/examples/histogram.svg?raw=true "Histogram example")

[source](/examples/histogram.json)

## Python

```
mini_svg.boxplot(
    data=data,
    margins=mini_svg.Margins(top=10, bottom=10, left=50),
    y_axis_values=mini_svg.PlotTicksConfig(max_count=5),
    y_label="ln(actual / estimate)",
    output_path=pathlib.Path('images/065.svg'),
    width=200,
    height=300,
    css=productivity_tasks.SVG_STYLES)
```
