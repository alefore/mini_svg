import {Box, Margins, simpleBox} from './box.js';
import {getPlotTicks, PlotTicksConfig} from './plot_ticks.js';
import {MoveAndScale, PointTransformer} from './point_transformer.js';
import {Shape, ShapeParams, transformShape} from './shape.js';

export interface XYPlotOptions {
  domain?: Box;
  outputRange?: Box;
  margins?: Margins;
  xAxisValues?: PlotTicksConfig;
  yAxisValues?: PlotTicksConfig;
  xLabel?: string;
  yLabel?: string;
  labels?: Set<string>;
  identityLine?: boolean;
}

export class XYPlot {
  domain: Box;
  outputRange: Box;
  margins?: Margins;
  xAxisValues: PlotTicksConfig;
  yAxisValues: PlotTicksConfig;
  xLabel?: string;
  yLabel?: string;
  labels: Set<string>;
  identityLine?: boolean;

  constructor({
    domain = new Box(),
    outputRange = new Box(),
    margins,
    xAxisValues = {},
    yAxisValues = {},
    xLabel,
    yLabel,
    labels = new Set(),
    identityLine
  }: XYPlotOptions = {}) {
    this.domain = domain;
    this.outputRange = outputRange;
    this.margins = margins;
    this.xAxisValues = xAxisValues;
    this.yAxisValues = yAxisValues;
    this.xLabel = xLabel;
    this.yLabel = yLabel;
    this.labels = labels;
    this.identityLine = identityLine;
  }

  get transformer(): (shapes: Shape[]) => Shape[] {
    let output = this.outputRange.withYReversed();
    if (this.margins) {
      output = output.withMargins(this.margins);
    }
    const pointTransformer = MoveAndScale(this.domain, output);
    return (shapes: Shape[]) =>
               shapes.map(shape => transformShape(shape, pointTransformer));
  }

  withDefaults(defaults: XYPlot): XYPlot {
    return new XYPlot({
      domain: this.domain.withDefaults(defaults.domain),
      outputRange: this.outputRange.withDefaults(defaults.outputRange),
      margins: this.margins ?? defaults.margins,
      xAxisValues: {...defaults.xAxisValues, ...this.xAxisValues},
      yAxisValues: {...defaults.yAxisValues, ...this.yAxisValues},
      xLabel: this.xLabel ?? defaults.xLabel,
      yLabel: this.yLabel ?? defaults.yLabel,
      labels: this.labels.size > 0 ? this.labels : defaults.labels,
      identityLine: this.identityLine ?? defaults.identityLine,
    });
  }

  produce(): Shape[] {
    const drawnShapes = this.draw();
    const transformedShapes = this.transformer(drawnShapes);
    const legendShapes = this.legend();
    return [...transformedShapes, ...legendShapes];
  }

  private legend(): Shape[] {
    const shapes: Shape[] = [];
    const sortedLabels = Array.from(this.labels).sort();

    sortedLabels.forEach((key, i) => {
      const lx = this.outputRange.width() - 60;
      const ly = 20 + i * 20;
      shapes.push({
        type: 'rect',
        x: lx,
        y: ly,
        w: 10,
        h: 10,
        params: {cssClass: `labels-${key}`}
      });
      shapes.push({
        type: 'text',
        text: key,
        x: lx + 15,
        y: ly + 9,
        params: {cssClass: `labels-${key}`}
      });
    });

    if (this.xLabel) {
      shapes.push({
        type: 'text',
        text: this.xLabel,
        x: this.outputRange.width() / 2,
        y: this.outputRange.height(),
        params: {cssClass: 'label-x'}
      });
    }

    if (this.yLabel) {
      const halfHeight = this.outputRange.height() / 2;
      shapes.push({
        type: 'text',
        text: this.yLabel,
        x: 15,
        y: halfHeight,
        params: {cssClass: 'label-y', transform: `rotate(-90 15,${halfHeight})`}
      });
    }

    return shapes;
  }

  private draw(): Shape[] {
    if (this.domain.x1 === null || this.domain.x2 === null ||
        this.domain.y1 === null || this.domain.y2 === null) {
      throw new Error('Domain bounds must be fully defined');
    }

    const shapes: Shape[] = [];

    // X Axis Ticks
    const xValues =
        getPlotTicks(this.xAxisValues, this.domain.x1, this.domain.x2);
    for (const x of xValues.values) {
      shapes.push({
        type: 'line',
        x1: x,
        y1: this.domain.y1,
        x2: x,
        y2: this.domain.y2,
        params: {cssClass: 'grid-line grid-line-x tick tick-x'}
      });
      const span = (this.domain.height() / 50) *
          (this.outputRange.width() / this.outputRange.height());
      shapes.push({
        type: 'line',
        x1: x,
        y1: this.domain.y1 - span,
        x2: x,
        y2: this.domain.y1,
        params: {cssClass: 'tick tick-x'}
      });
      shapes.push({
        type: 'text',
        text: xValues.formatFunction(x),
        x: x,
        y: this.domain.y1 - 2 * span,
        params: {cssClass: 'tick tick-x'}
      });
    }

    // Y Axis Ticks
    const yValues =
        getPlotTicks(this.yAxisValues, this.domain.y1, this.domain.y2);
    for (const y of yValues.values) {
      shapes.push({
        type: 'line',
        x1: this.domain.x1,
        y1: y,
        x2: this.domain.x2,
        y2: y,
        params: {cssClass: 'grid-line grid-line-y tick tick-y'}
      });
      const span = this.domain.width() / 50;
      shapes.push({
        type: 'line',
        x1: this.domain.x1 - span,
        y1: y,
        x2: this.domain.x1,
        y2: y,
        params: {cssClass: 'tick tick-y'}
      });
      shapes.push({
        type: 'text',
        text: yValues.formatFunction(y),
        x: this.domain.x1 - 2 * span,
        y: y,
        params: {cssClass: 'tick tick-y'}
      });
    }

    // Axis Borders
    shapes.push({
      type: 'line',
      x1: this.domain.x1,
      y1: this.domain.y1,
      x2: this.domain.x1,
      y2: this.domain.y2,
      params: {cssClass: 'axis-border axis-border-y'}
    });
    shapes.push({
      type: 'line',
      x1: this.domain.x1,
      y1: this.domain.y1,
      x2: this.domain.x2,
      y2: this.domain.y1,
      params: {cssClass: 'axis-border axis-border-x'}
    });

    // Identity Line
    if (this.identityLine) {
      const clip = Math.min(this.domain.x2, this.domain.y2);
      shapes.push({
        type: 'line',
        x1: 0,
        y1: 0,
        x2: clip,
        y2: clip,
        params: {cssClass: 'identity-line'}
      });
    }

    return shapes;
  }
}
