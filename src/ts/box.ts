export interface Margins {
  readonly top: number;
  readonly right: number;
  readonly bottom: number;
  readonly left: number;
}

export class Box {
  constructor(
      public readonly x1: number|null = null,
      public readonly y1: number|null = null,
      public readonly x2: number|null = null,
      public readonly y2: number|null = null) {}

  withDefaults(defaults: Box): Box {
    return new Box(
        this.x1 ?? defaults.x1, this.y1 ?? defaults.y1, this.x2 ?? defaults.x2,
        this.y2 ?? defaults.y2);
  }

  width(): number {
    if (this.x1 === null || this.x2 === null)
      throw new Error('Missing X bounds');
    return Math.abs(this.x2 - this.x1);
  }

  height(): number {
    if (this.y1 === null || this.y2 === null)
      throw new Error('Missing Y bounds');
    return Math.abs(this.y2 - this.y1);
  }

  withMargins(margins: Margins): Box {
    if (this.x1 === null || this.x2 === null || this.y1 === null ||
        this.y2 === null)
      throw new Error('Missing bounds');
    if (this.y1 < this.y2) {
      return new Box(
          this.x1 + margins.left, this.y1 + margins.bottom,
          this.x2 - margins.right, this.y2 - margins.top);
    }
    return new Box(
        this.x1 + margins.left, this.y1 - margins.bottom,
        this.x2 - margins.right, this.y2 + margins.top);
  }

  withYReversed(): Box {
    if (this.x1 === null || this.x2 === null || this.y1 === null ||
        this.y2 === null)
      throw new Error('Missing bounds');
    return new Box(this.x1, this.y2, this.x2, this.y1);
  }
}

export const simpleBox = (width: number, height: number) =>
    new Box(0, 0, width, height);
