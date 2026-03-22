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
| `domain`        | `Box`                      | Defines the data range (min/max x and y) for the plot. | Inferred from data  |
| `output_range`  | `Box`                      | Defines the canvas area where the plot is rendered.    | Set by SvgWriter    |
| `margins`       | `Margins`                  | Optional margins around the plot.                      | `Margins()`         |
| `x_axis_values` | `tuple[float, ...]`        | Configurations for X axis ticks.                       | `PlotTicksConfig()` |
| `y_axis_values` | `tuple[float, ...]`        | Configurations for Y axis ticks.                       | `PlotTicksConfig()` |
| `x_label`       | `str`                      | Optional label for the x-axis.                         | `None`              |
| `y_label`       | `str`                      | Optional label for the y-axis.                         | `None`              |
| `labels`        | `frozenset[str]`           | Labels to display on the plot.                         | `()`                |
| `identity_line` | `bool | None`              | Whether to draw an identity line (y=x).                | `None`              |

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

| Parameter | Type    | Default Value |
|:----------|:--------|:--------------|
| `top`     | `float` | `0` |
| `right`   | `float` | `0` |
| `bottom`  | `float` | `0` |
| `left`    | `float` | `0` |

## Plot Ticks Parameters

`PlotTicksConfig` is a dataclass for configuring plot ticks.

| Parameter | Type | Description | Default Value |
|:----------|:-----|:------------|:--------------|
| `values` | `frozenset[float] | None` | List of values where ticks should be drawn. If given, all other fields are ignored. | `None` |
| `max_count` | `int | None` | Do not draw more than this number of ticks. | `None` |
| `min_distance` | `float | None` | Minimum distance between ticks. | `None` |
| `value_format` | `str | None` | Format string for the tick values. | `None` |

