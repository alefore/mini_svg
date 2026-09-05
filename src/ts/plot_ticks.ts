export interface PlotTicks {
  values: Set<number>;
  formatFunction: (value: number) => string;
}

export interface PlotTicksConfig {
  values?: Set<number>;
  maxCount?: number;
  minDistance?: number;
  timeFormat?: Intl.DateTimeFormatOptions;
  valueFormat?: string;
  formatFunction?: (value: number) => string;
}

function findBase(config: PlotTicksConfig, low: number, high: number): number {
  const maxCount = config.maxCount ?? 10;
  let roughDistance = (high - low) / maxCount;
  if (config.minDistance)
    roughDistance = Math.max(roughDistance, config.minDistance);
  const powerOf10 = Math.pow(10, Math.floor(Math.log10(roughDistance)));
  for (const factor of [1, 2, 5, 10]) {
    const candidate = powerOf10 * factor;
    let count = Math.floor((high - Math.max(low, 0)) / candidate);
    if (low <= 0) {
      count += 1;
      if (low < 0) count += Math.floor(Math.abs(low) / candidate);
    }
    if (count <= maxCount &&
        (!config.minDistance || candidate >= config.minDistance))
      return candidate;
  }
  throw new Error('Could not find suitable tick base.');
}

function getValues(
    config: PlotTicksConfig, low: number, high: number,
    base: number): number[] {
  if (config.values) return Array.from(config.values);
  const firstTic = Math.ceil(low / base) * base;
  if (firstTic > high) return [];
  const count =
      Math.min(config.maxCount ?? 10, Math.floor((high - firstTic) / base) + 1);
  return Array.from({length: count}, (_, k) => firstTic + k * base);
}

function fmtTime(config: PlotTicksConfig, t: number): string {
  // Python fromtimestamp uses seconds; JS Date uses milliseconds
  const date = new Date(t * 1000);
  if (!config.timeFormat) throw new Error('Missing timeFormat');
  return new Intl.DateTimeFormat(undefined, config.timeFormat).format(date);
}

function getFmt(config: PlotTicksConfig, base: number): (v: number) => string {
  const definedFormats = [
    config.timeFormat, config.valueFormat, config.formatFunction
  ].filter(f => f !== undefined);
  if (definedFormats.length > 1) {
    throw new Error(
        'At most one of timeFormat, valueFormat, or formatFunction may be specified.');
  }

  if (config.formatFunction !== undefined) return config.formatFunction;
  if (config.timeFormat !== undefined) return (t: number) => fmtTime(config, t);

  let valueFormat = config.valueFormat;
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

export function getPlotTicks(
    config: PlotTicksConfig, low: number, high: number): PlotTicks {
  const maxCount = config.maxCount ?? 10;

  if (maxCount <= 0) {
    return {
      values: new Set(),
      formatFunction: (_: number) => {
        throw new Error('Unexpected call to PlotTicks.formatFunction.');
      }
    };
  }

  if (config.values && config.values.size > 0) {
    const sortedValues = Array.from(config.values).sort((a, b) => a - b);
    const base =
        sortedValues.length > 1 ? sortedValues[1] - sortedValues[0] : 1;
    return {values: config.values, formatFunction: getFmt(config, base)};
  }

  const base = findBase(config, low, high);
  return {
    values: new Set(getValues(config, low, high, base)),
    formatFunction: getFmt(config, base)
  };
}
