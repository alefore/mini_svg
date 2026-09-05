export interface PlotTicks {
  values: Set<number>;
  formatFunction: (value: number) => string;
}

export class PlotTicksConfig {
  constructor(
      public values?: Set<number>, public maxCount?: number,
      public minDistance?: number, public timeFormat?: string,
      public valueFormat?: string) {}

  withDefaults(defaults: PlotTicksConfig): PlotTicksConfig {
    return new PlotTicksConfig(
        this.values ?? defaults.values, this.maxCount ?? defaults.maxCount,
        this.minDistance ?? defaults.minDistance,
        this.timeFormat ?? defaults.timeFormat,
        this.valueFormat ?? defaults.valueFormat);
  }

  private findBase(low: number, high: number): number {
    const maxCount = this.maxCount ?? 10;
    let roughDistance = (high - low) / maxCount;
    if (this.minDistance)
      roughDistance = Math.max(roughDistance, this.minDistance);
    const powerOf10 = Math.pow(10, Math.floor(Math.log10(roughDistance)));
    for (const factor of [1, 2, 5, 10]) {
      const candidate = powerOf10 * factor;
      let count = Math.floor((high - Math.max(low, 0)) / candidate);
      if (low <= 0) {
        count += 1;
        if (low < 0) count += Math.floor(Math.abs(low) / candidate);
      }
      if (count <= maxCount &&
          (!this.minDistance || candidate >= this.minDistance))
        return candidate;
    }
    throw new Error('Could not find suitable tick base.');
  }

  private getValues(low: number, high: number, base: number): number[] {
    if (this.values) return Array.from(this.values);
    const firstTic = Math.ceil(low / base) * base;
    if (firstTic > high) return [];
    const count =
        Math.min(this.maxCount ?? 10, Math.floor((high - firstTic) / base) + 1);
    return Array.from({length: count}, (_, k) => firstTic + k * base);
  }

  private fmtTime(t: number): string {
    // Python fromtimestamp uses seconds; JS Date uses milliseconds
    const date = new Date(t * 1000);
    if (!this.timeFormat) throw new Error('Missing timeFormat');
    // Note: A true strftime port requires a library like date-fns.
    // Falling back to a standard string representation here.
    return date.toISOString();
  }

  private getFmt(base: number): (v: number) => string {
    if (this.timeFormat !== undefined && this.valueFormat !== undefined) {
      throw new Error('Cannot specify both timeFormat and valueFormat');
    }

    if (this.timeFormat !== undefined) {
      return (t: number) => this.fmtTime(t);
    }

    let valueFormat = this.valueFormat;
    if (valueFormat) {
      // If a custom string format is provided, return a simple interpolation
      // (a full port of Python's format() would require a utility like
      // d3-format)
      return (v: number) => `${v}`;
    } else if (base > 1) {
      return (v: number) => v.toFixed(0);
    } else {
      const decimals = Math.abs(Math.floor(Math.log10(base)));
      return (v: number) => v.toFixed(decimals);
    }
  }

  build(low: number, high: number): PlotTicks {
    const maxCount = this.maxCount ?? 10;

    if (maxCount <= 0) {
      return {
        values: new Set(),
        formatFunction: (_: number) => {
          throw new Error('Unexpected call to PlotTicks.formatFunction.');
        }
      };
    }

    if (this.values && this.values.size > 0) {
      const sortedValues = Array.from(this.values).sort((a, b) => a - b);
      const base =
          sortedValues.length > 1 ? sortedValues[1] - sortedValues[0] : 1;
      return {values: this.values, formatFunction: this.getFmt(base)};
    }

    const base = this.findBase(low, high);
    return {
      values: new Set(this.getValues(low, high, base)),
      formatFunction: this.getFmt(base)
    };
  }
}
