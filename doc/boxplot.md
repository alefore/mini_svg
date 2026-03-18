# BoxPlot

Creates a series of BoxPlot graphs, visualizing distributions at a glance:

![BoxPlot example](/examples/boxplot.svg?raw=true "BoxPlot example")

### plot.domain (optional)

Defaults to setting the y-axis to the min/max values in the data.

One can specify it to constrain the y axis;
in this case, x1 should be set to -1 and x2 to 1 + the number of plots.
See [examples/boxplot.sh]

### Python

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

## Scatterplot
