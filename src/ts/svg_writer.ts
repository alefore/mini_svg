import {Box, simpleBox} from './box.js';
import {Shape, shapeParamsAsText} from './shape.js';

export interface SvgWriterOptions {
  width?: number;
  height?: number;
  css?: string;
}

export class SvgWriter {
  width: number;
  height: number;
  css: string;

  constructor(
      {width = 400.0, height = 300.0, css = ''}: SvgWriterOptions = {}) {
    this.width = width;
    this.height = height;
    this.css = css;
  }

  getBox(): Box {
    return simpleBox(this.width, this.height);
  }

  writeShape(shape: Shape): string {
    const params = shapeParamsAsText(shape.params);
    switch (shape.type) {
      case 'line':
        return `<line x1="${shape.x1.toFixed(1)}" y1="${
            shape.y1.toFixed(1)}" x2="${shape.x2.toFixed(1)}" y2="${
            shape.y2.toFixed(1)}"${params}/>`;
      case 'rect':
        return `<rect x="${shape.x.toFixed(1)}" y="${
            shape.y.toFixed(1)}" width="${shape.w.toFixed(1)}" height="${
            shape.h.toFixed(1)}"${params}/>`;
      case 'circle':
        const circleBase = `<circle cx="${shape.cx.toFixed(1)}" cy="${
            shape.cy.toFixed(1)}" r="${shape.r.toFixed(1)}"${params}`;
        return shape.params.title ?
            `${circleBase}><title>${shape.params.title}</title></circle>` :
            `${circleBase}/>`;
      case 'text':
        return `<text x="${shape.x.toFixed(1)}" y="${shape.y.toFixed(1)}"${
            params}>${shape.text}</text>`;
      case 'path':
        const d =
            shape.points
                .map((p) => `${p.pathType} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
                .join(' ');
        return `<path d="${d}"${params}/>`;
    }
  }

  consume(shapes: Shape[]): string {
    const lines = [
      '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
      '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">',
      `<svg xmlns:xlink="http://www.w3.org/1999/xlink" width="${
          this.width}" height="${this.height}" viewBox="0 0 ${this.width} ${
          this.height}" xmlns="http://www.w3.org/2000/svg" version="1.1">`
    ];
    if (this.css.length > 0) {
      lines.push('<style>');
      lines.push(this.css);
      lines.push('</style>');
    }
    shapes.forEach((s) => lines.push(this.writeShape(s)));
    lines.push('</svg>');
    return lines.join('\n');
  }
}
