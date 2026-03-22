# Parameters

## Providing JSON values

* Simple types (`float`, `str`, `bool`, `path`)
  take a corresponding "simple" JSON value
  (path takes a string).

* `list` takes JSON lists of their corresponding values.

* The other values expect a JSON dictionary
  with the parameters described below.

## Plot Parameters

All plot types (e.g., histogram, scatterplot, etc.)
take the following parameters:

| Parameter   | Type               | Notes |
|:------------|:-------------------|:------
| `writer`    | `SvgWriter`        | |
| `plot`      | `XYPlot`           | |
| `data`      | `path`             | Defaults to `/dev/stdin`. The format depends on the plot type. |

Plots may also take additional plot-specific parameters .
They override the logic that computes various defaults.
For example, they will typically set the `XYPlot`'s
`labels` based on their input data.

## SvgWriter Parameters

`SvgWriter` configures the SVG output.

| Parameter   | Type               | Description                                            | Default Value |
|:------------|:-------------------|:-------------------------------------------------------|:--------------|
| `output_path` | `path`     | The path where the SVG output will be written.         | `/dev/stdout`  |
| `width`       | `float`            | The width of the SVG image in pixels.                  | 400           |
| `height`      | `float`            | The height of the SVG image in pixels.                 | 300           |
| `css`         | `list[path]` | CSS files to be included (inline) in the SVG. | `[]`          |

## XYPlot Parameters

`XYPlot` is a dataclass that configures an XY plot.

| Parameter       | Type                       | Notes |
|:----------------|:---------------------------|:-------------------------------------------------------|
| `domain`        | `Box`                      | Defines the data range (min/max x and y) for the plot. If not provided, will be inferred from data. |
| `output_range`  | `Box`                      | Defines the canvas area where the plot is rendered. You'll rarely want to set this: it defaults to the points `(0, height)` and `(width, 0)` (based on the values in the `SvgWriter`). |
| `margins`       | `Margins`                  | Optional margins around the plot. |
| `x_axis_values` | `PlotTicksConfig`        | Configuration for X axis ticks. |
| `y_axis_values` | `PlotTicksConfig`        | Configurations for Y axis ticks. |
| `x_label`       | `str`                      | Optional label for the x-axis. None by default. |
| `y_label`       | `str`                      | Optional label for the y-axis. None by default.          |
| `labels`        | `list[str]`           | Labels (legends) to display on the plot. If not sent, they are inferred from data.  |
| `identity_line` | `bool`              | Whether to draw an identity line (y=x).  Defaults to no line. |

## Box Parameters

`Box` represents a rectangular area.

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `x1` | `float` | X-coordinate of the first corner. |
| `y1` | `float` | Y-coordinate of the first corner. |
| `x2` | `float` | X-coordinate of the second corner. |
| `y2` | `float` | Y-coordinate of the second corner. |

If the JSON file doesn't provide values,
defaults are typically set
by the class containing the box
(depending on the specific box variable).

## Margins Parameters

`Margins` defines the margins around a box.

| Parameter | Type    | Default Value |
|:----------|:--------|:--------------|
| `top`     | `float` | `0` |
| `right`   | `float` | `0` |
| `bottom`  | `float` | `0` |
| `left`    | `float` | `0` |

## Plot Ticks Parameters

`PlotTicksConfig` represents the configuration for plot ticks.

| Parameter | Type | Description | Default Value |
|:----------|:-----|:------------|:--------------|
| `values` | `list[float]` | List of values where ticks should be drawn. If given, `max_count` and `mim__distance` are ignored. |
| `max_count` | `int` | Do not draw more than this number of ticks. Defaults to 10. |
| `min_distance` | `float` | Minimum distance between ticks. By default, no minimum is used. |
| `value_format` | `str` or `None` | Format string for the tick values (e.g., `.4f`). By default, the number of decimal points is inferred from the values. |
