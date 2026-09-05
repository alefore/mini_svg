import {Box} from './box.js';

export type PointTransformer = (x: number, y: number) => [number, number];

function translate(dx: number, dy: number): PointTransformer {
  return (x: number, y: number) => [x + dx, y + dy];
}

function scale(sx: number, sy: number): PointTransformer {
  return (x: number, y: number) => [x * sx, y * sy];
}

function compose(transformers: PointTransformer[]): PointTransformer {
  return (x: number, y: number) => {
    let currentX = x;
    let currentY = y;

    for (const t of transformers) {
      const [nextX, nextY] = t(currentX, currentY);
      currentX = nextX;
      currentY = nextY;
    }

    return [currentX, currentY];
  };
}

/** Returns a new delegate where drawing is constrained to the box given. */
export function MoveAndScale(domain: Box, outputRange: Box): PointTransformer {
  if (domain.x1 === null || domain.x2 === null || domain.y1 === null ||
      domain.y2 === null) {
    throw new Error('Missing domain bounds');
  }
  if (outputRange.x1 === null || outputRange.x2 === null ||
      outputRange.y1 === null || outputRange.y2 === null) {
    throw new Error('Missing output bounds');
  }

  const toOrigin = translate(-domain.x1, -domain.y1);

  const sx = (outputRange.x2 - outputRange.x1) / (domain.x2 - domain.x1);
  const sy = (outputRange.y2 - outputRange.y1) / (domain.y2 - domain.y1);
  const scaleTransform = scale(sx, sy);

  const toOutput = translate(outputRange.x1, outputRange.y1);

  return compose([toOrigin, scaleTransform, toOutput]);
}
