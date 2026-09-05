import {Box, simpleBox} from './box.js';
import {PlotTicksConfig} from './plot_ticks.js';
import {MoveAndScale, PointTransformer} from './point_transformer.js';
import {PathPoint, Shape, transformShape} from './shape.js';
import {SvgWriter} from './svg_writer.js';
import {XYPlot} from './xyplot.js';

export function scatterplot(
    writer: SvgWriter, plot: XYPlot, data: Record<string, [number, number][]>) {
  const allX = Object.values(data).flat().map(p => p[0]);
  const allY = Object.values(data).flat().map(p => p[1]);
  plot = plot.withDefaults(new XYPlot({
    outputRange: writer.getBox(),
    domain: new Box(
        Math.min(0, ...allX), Math.min(0, ...allY), Math.max(...allX),
        Math.max(...allY)),
    labels: new Set(Object.keys(data))
  }))

  const shapes: Shape[] = [];
  const radius = plot.domain.width() / 60;
  const transformer =
      MoveAndScale(plot.domain, writer.getBox().withYReversed());

  for (const [key, points] of Object.entries(data)) {
    for (const [x, y] of points) {
      shapes.push(transformShape(
          {
            type: 'circle',
            cx: x,
            cy: y,
            r: radius,
            params: {cssClass: key, title: `${key}: (${x}, ${y})`}
          },
          transformer));
    }
  }
  writer.consume(shapes);
}

export function histogram(
    writer: SvgWriter, bins: number, data: Record<string, number[]>) {
  const allValues = Object.values(data).flat();
  const minValue = Math.min(...allValues);
  const maxValue = Math.max(...allValues);
  const binSize = (maxValue - minValue) / bins;

  const binnedData: Record<string, number[]> = {};
  for (const [label, values] of Object.entries(data)) {
    const counts = Array(bins).fill(0);
    for (const v of values) {
      let index = Math.floor((v - minValue) / binSize);
      if (index === bins) index -= 1;
      counts[index]++;
    }
    binnedData[label] = counts;
  }

  const maxCount = Math.max(...Object.values(binnedData).flat());
  const domain = new Box(minValue, 0, maxValue, maxCount);
  const transformer = MoveAndScale(domain, writer.getBox().withYReversed());

  const shapes: Shape[] = [];
  const individualBinWidth = (binSize * 0.8) / Object.keys(binnedData).length;

  Object.entries(binnedData).forEach(([label, counts], groupIndex) => {
    counts.forEach((count, binIndex) => {
      if (count > 0) {
        const x = minValue +
            binSize *
                (binIndex + 0.1 +
                 (0.8 * groupIndex) / Object.keys(binnedData).length);
        shapes.push(transformShape(
            {
              type: 'rect',
              x,
              y: 0,
              w: individualBinWidth,
              h: count,
              params: {cssClass: label.toLowerCase()}
            },
            transformer));
      }
    });
  });

  writer.consume(shapes);
}

export function getDomain(points: [number, number][]): Box {
  const allX = points.map(pt => pt[0]);
  const allY = points.map(pt => pt[1]);
  return new Box(
      Math.min(...allX), Math.min(...allY), Math.max(...allX),
      Math.max(...allY));
}

class LinePlotOne {
  constructor(public label: string, public data: [number, number][]) {}

  draw(plot: XYPlot): Shape[] {
    const countByX = new Map<number, number>();

    // Deduplicate exact (x, y) pairs similar to Python's `set(self.data)`
    const uniqueData =
        Array.from(new Set(this.data.map(p => `${p[0]},${p[1]}`)))
            .map(s => s.split(',').map(Number) as [number, number]);

    for (const [x, _] of uniqueData) {
      countByX.set(x, (countByX.get(x) || 0) + 1);
    }

    const repeatedValues = Array.from(countByX.entries())
                               .filter(([_, count]) => count > 1)
                               .map(([x, _]) => x);

    if (repeatedValues.length > 0) {
      throw new Error(`${this.label}: Multiple y values for x values: ${
          repeatedValues.join(', ')}`);
    }

    const points: PathPoint[] = [];
    points.push({pathType: 'M', x: this.data[0][0], y: this.data[0][1]});

    for (let i = 1; i < this.data.length; i++) {
      points.push({pathType: 'L', x: this.data[i][0], y: this.data[i][1]});
    }

    return [{
      type: 'path',
      points: points,
      params: {cssClass: `lineplot-${this.label}`}
    }];
  }
}

export function lineplot(
    writer: SvgWriter, plot: XYPlot,
    data: Record<string, [number, number][]>): string {
  const lineData: Record<string, LinePlotOne> = {};

  for (const [k, v] of Object.entries(data)) {
    const sortedV =
        [...v].sort((a, b) => a[0] !== b[0] ? a[0] - b[0] : a[1] - b[1]);
    lineData[k] = new LinePlotOne(k, sortedV);
  }

  const allPoints = Object.values(data).flat();

  plot = plot.withDefaults(new XYPlot({
    outputRange: writer.getBox(),
    labels: new Set(Object.keys(lineData)),
    domain: getDomain(allPoints)
  }));

  const baseShapes = plot.produce();

  // Sort the keys to ensure consistent rendering order
  const sortedKeys = Object.keys(lineData).sort();
  const lineShapes =
      sortedKeys.flatMap(key => plot.transformer(lineData[key].draw(plot)));

  return writer.consume([...baseShapes, ...lineShapes]);
}