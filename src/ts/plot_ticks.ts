import {formatDuration, getLargestUnit, MS_PER_DAY, MS_PER_HOUR, MS_PER_MINUTE, MS_PER_SECOND, MS_PER_WEEK, MS_PER_YEAR} from './time_formats.js';

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
  // Input values are milliseconds since epoch. We'll display ticks by
  // subtracting the lowest value from the tick values. In other words,
  // the values are all relative to the beginning of the graph.
  isDuration?: boolean;
}

const DURATION_BASES = [
  ...[1, 2, 5, 10, 20, 50, 100, 200, 500],
  ...[1, 2, 5, 10, 15, 20, 30].map(v => v * MS_PER_SECOND),
  ...[1, 2, 5, 10, 15, 20, 30].map(v => v * MS_PER_MINUTE),
  ...[1, 2, 3, 4, 6, 12].map(v => v * MS_PER_HOUR),
  ...[1, 2, 3, 4, 5, 6].map(v => v * MS_PER_DAY),
  ...[1, 2, 4, 8, 13, 26].map(
      v => v * MS_PER_WEEK),  // 13w = ~1/4 year, 26w = ~1/2 year
  ...[1, 2, 5, 10, 20, 50, 100].map(v => v * MS_PER_YEAR)
];

function findBase(config: PlotTicksConfig, low: number, high: number): number {
  const maxCount = config.maxCount ?? 10;
  let roughDistance = (high - low) / maxCount;
  if (config.minDistance)
    roughDistance = Math.max(roughDistance, config.minDistance);
  if (config.isDuration) {
    for (const candidate of DURATION_BASES) {
      // Since ticks are anchored to low, the total ticks is simply the span
      // divided by the candidate interval
      const count = Math.floor((high - low) / candidate) + 1;
      if (count <= maxCount &&
          (!config.minDistance || candidate >= config.minDistance)) {
        return candidate;
      }
    }

    // Fallback for spans larger than ~30 days, grouping by years
    const MS_PER_YEAR = 31536000000;
    const powerOf10Years =
        Math.pow(10, Math.floor(Math.log10(roughDistance / MS_PER_YEAR)));
    for (const factor of [1, 2, 5, 10]) {
      const candidate = powerOf10Years * factor * MS_PER_YEAR;
      if (Math.floor((high - low) / candidate) + 1 <= maxCount)
        return candidate;
    }
  }
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
  const firstTic = config.isDuration ? low : Math.ceil(low / base) * base;
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

function getFmt(
    config: PlotTicksConfig, base: number, low: number,
    high: number): (v: number) => string {
  const definedFormats = [
    config.timeFormat, config.valueFormat, config.isDuration ? true : undefined
  ].filter(f => f !== undefined);

  if (definedFormats.length > 1) {
    throw new Error(
        'At most one of timeFormat, valueFormat, or isDuration may be specified.');
  }

  if (config.isDuration) {
    const topUnit = getLargestUnit(high - low);
    return (v: number) => formatDuration(v - low, topUnit);
  }

  if (config.timeFormat !== undefined) return (t: number) => fmtTime(config, t);

  let valueFormat = config.valueFormat;
  if (valueFormat) {
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
    return {
      values: config.values,
      formatFunction: getFmt(config, base, low, high)
    };
  }

  const base = findBase(config, low, high);
  return {
    values: new Set(getValues(config, low, high, base)),
    formatFunction: getFmt(config, base, low, high)
  };
}