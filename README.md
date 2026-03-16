# mini_svg

Py library to generate SVG visualizations of scientific data

# Examples

I've generated the images in http://alejo.ch/3jj with:

```
mini_svg.scatterplot(
    data={
        m: [(t.actual, t.estimated) for t in tasks if t.method == m]
        for m in methods
    },
    margins=mini_svg.Margins(10, 20, 40, 50),
    x_label="Actual",
    y_label="Estimate",
    identity_line=True,
    output_path=pathlib.Path('images/063.svg'),
    width=400,
    height=300,
    css=productivity_tasks.SVG_STYLES)

data = {
    m: [math.log(t.actual / t.estimated) for t in tasks if t.method == m]
    for m in set(t.method for t in tasks)
}

mini_svg.histogram(
    bins=10,
    data=data,
    margins=mini_svg.Margins(top=10, bottom=40, left=50),
    x_label="ln(actual / estimate)",
    output_path=pathlib.Path('images/064.svg'),
    width=400,
    height=300,
    css=productivity_tasks.SVG_STYLES)

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

(`SVG_STYLES` are just local paths containing the styles you can see
in the SVG sources.)
