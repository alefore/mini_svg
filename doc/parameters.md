# SvgWriter Parameters

`SvgWriter` is a dataclass that configures the SVG output.

| Parameter   | Type               | Description                                            | Default Value |
|:------------|:-------------------|:-------------------------------------------------------|:--------------|
| `output_path` | `pathlib.Path`     | The path where the SVG output will be written.         | Required      |
| `width`       | `float`            | The width of the SVG image in pixels.                  | Required      |
| `height`      | `float`            | The height of the SVG image in pixels.                 | Required      |
| `css`         | `tuple[pathlib.Path, ...]` | A tuple of `pathlib.Path` objects pointing to CSS files to be included in the SVG. | `()`          |
