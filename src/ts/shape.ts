import {PointTransformer} from './point_transformer.js';

export interface ShapeParams {
  cssClass?: string;
  title?: string;
  transform?: string;
  fill?: string;
  stroke?: string;
  strokeWidth?: string;
}

export function shapeParamsAsText(params: ShapeParams): string {
  // Explicitly typing the record ensures strict static checking
  const data: Record<string, string | undefined> = {
    "class": params.cssClass,
    "transform": params.transform,
    "fill": params.fill,
    "stroke": params.stroke,
    "stroke-width": params.strokeWidth,
  };

  return Object.entries(data)
    .filter(([, value]) => value !== undefined)
    .map(([key, value]) => ` ${key}='${value}'`)
    .join("");
}

export type PathPoint = {
  pathType: string; x: number; y: number
};

export type Shape =|{
  type: 'rect';
  x: number;
  y: number;
  w: number;
  h: number;
  params: ShapeParams
}
|{
  type: 'line';
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  params: ShapeParams
}
|{
  type: 'circle';
  cx: number;
  cy: number;
  r: number;
  params: ShapeParams
}
|{
  type: 'text';
  text: string;
  x: number;
  y: number;
  params: ShapeParams
}
|{
  type: 'path';
  points: PathPoint[];
  params: ShapeParams
};

export function transformShape(
    shape: Shape, transformer: PointTransformer): Shape {
  switch (shape.type) {
    case 'line': {
      const [tx1, ty1] = transformer(shape.x1, shape.y1);
      const [tx2, ty2] = transformer(shape.x2, shape.y2);
      return {...shape, x1: tx1, y1: ty1, x2: tx2, y2: ty2};
    }
    case 'rect': {
      const [tx1, ty1] = transformer(shape.x, shape.y);
      const [tx2, ty2] = transformer(shape.x + shape.w, shape.y + shape.h);
      return {
        ...shape,
        x: Math.min(tx1, tx2),
        y: Math.min(ty1, ty2),
        w: Math.abs(tx1 - tx2),
        h: Math.abs(ty1 - ty2)
      };
    }
    case 'circle': {
      const [tx, ty] = transformer(shape.cx, shape.cy);
      const [edgeX] = transformer(shape.cx + shape.r, shape.cy);
      return {...shape, cx: tx, cy: ty, r: Math.abs(edgeX - tx)};
    }
    case 'text': {
      const [tx, ty] = transformer(shape.x, shape.y);
      return {...shape, x: tx, y: ty};
    }
    case 'path': {
      const transformedPoints = shape.points.map((p) => {
        const [px, py] = transformer(p.x, p.y);
        return {pathType: p.pathType, x: px, y: py};
      });
      return {...shape, points: transformedPoints};
    }
  }
}