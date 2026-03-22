# SvgWriter Parameters

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
