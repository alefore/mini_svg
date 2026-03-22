# Parameters

## SvgWriter Parameters

`SvgWriter` is a dataclass that configures the SVG output.

| Parameter   | Type               | Description                                            | Default Value |
|:------------|:-------------------|:-------------------------------------------------------|:--------------|
| `output_path` | `pathlib.Path`     | The path where the SVG output will be written.         | Required      |
| `width`       | `float`            | The width of the SVG image in pixels.                  | Required      |
| `height`      | `float`            | The height of the SVG image in pixels.                 | Required      |
| `css`         | `tuple[pathlib.Path, ...]` | A tuple of `pathlib.Path` objects pointing to CSS files to be included in the SVG. | `()`          |

## XYPlot Parameters

`XYPlot` is a dataclass that configures an XY plot.

| Parameter       | Type                       | Description                                            | Default Value       |
|:----------------|:---------------------------|:-------------------------------------------------------|:--------------------|
| `domain`        | `Box`                      | The domain of the plot (min, max).                     | Inferred from data  |
| `output_range`  | `Box`                      | The output range of the plot (min, max).               | Set by SvgWriter    |
| `margins`       | `Margins`                  | Margins for the plot.                                  | `Margins()`         |
| `x_axis_values` | `tuple[float, ...]`        | Specific values to mark on the x-axis.                 | `()`                |
| `y_axis_values` | `tuple[float, ...]`        | Specific values to mark on the y-axis.                 | `()`                |
| `x_label`       | `str`                      | Label for the x-axis.                                  | `""`                |
| `y_label`       | `str`                      | Label for the y-axis.                                  | `""`                |
| `labels`        | `tuple[Label, ...]`        | Labels to display on the plot.                         | `()`                |
| `identity_line` | `bool`                     | Whether to draw an identity line (y=x).                | `False`             |

## Box Parameters

`Box` is a dataclass representing a rectangular area.

| Parameter | Type | Description | Default Value |
|:----------|:-----|:------------|:--------------|
| `x1` | `float | None` | The x-coordinate of the first corner. | `None` |
| `y1` | `float | None` | The y-coordinate of the first corner. | `None` |
| `x2` | `float | None` | The x-coordinate of the second corner. | `None` |
| `y2` | `float | None` | The y-coordinate of the second corner. | `None` |

## Margins Parameters

`Margins` is a dataclass defining the margins around a box.

| Parameter | Type | Description | Default Value |
|:----------|:-----|:------------|:--------------|
| `top` | `float` | The top margin. | `0` |
| `right` | `float` | The right margin. | `0` |
| `bottom` | `float` | The bottom margin. | `0` |
| `left` | `float` | The left margin. | `0` |

## Plot Ticks Parameters

`PlotTicksConfig` is a dataclass for configuring plot ticks.

| Parameter | Type | Description | Default Value |
|:----------|:-----|:------------|:--------------|
| `values` | `frozenset[float] | None` | List of values where ticks should be drawn. If given, all other fields are ignored. | `None` |
| `max_count` | `int | None` | Do not draw more than this number of ticks. | `None` |
| `min_distance` | `float | None` | Minimum distance between ticks. | `None` |
| `value_format` | `str | None` | Format string for the tick values. | `None` |

