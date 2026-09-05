export const MS_PER_SECOND = 1000;
export const MS_PER_MINUTE = 60 * MS_PER_SECOND;
export const MS_PER_HOUR = 60 * MS_PER_MINUTE;
export const MS_PER_DAY = 24 * MS_PER_HOUR;
export const MS_PER_WEEK = MS_PER_DAY * 7;
export const MS_PER_YEAR = MS_PER_DAY * 365;

export interface DurationUnit {
  unit: string;
  val: number;
  padTo2: boolean;
}

// Extracted unit calculation to allow examining the whole range's magnitude
export function getDurationUnits(durationMs: number): DurationUnit[] {
  const absMs = Math.abs(durationMs);

  const years = Math.floor(absMs / MS_PER_YEAR);
  let rem = absMs % MS_PER_YEAR;
  const weeks = Math.floor(rem / MS_PER_WEEK);
  rem %= MS_PER_WEEK;
  const days = Math.floor(rem / MS_PER_DAY);
  rem %= MS_PER_DAY;
  const hours = Math.floor(rem / MS_PER_HOUR);
  rem %= MS_PER_HOUR;
  const minutes = Math.floor(rem / MS_PER_MINUTE);
  rem %= MS_PER_MINUTE;
  const seconds = Math.floor(rem / MS_PER_SECOND);
  const milliseconds = rem % MS_PER_SECOND;

  return [
    {unit: 'y', val: years, padTo2: false},
    {unit: 'w', val: weeks, padTo2: true},
    {unit: 'd', val: days, padTo2: false},
    {unit: 'h', val: hours, padTo2: true},
    {unit: 'm', val: minutes, padTo2: true},
    {unit: 's', val: seconds, padTo2: true},
    {unit: 'ms', val: milliseconds, padTo2: false}
  ];
}

export function getLargestUnit(durationMs: number): string|undefined {
  const units = getDurationUnits(durationMs);
  const firstNonZero = units.find(u => u.val > 0);
  return firstNonZero?.unit;
}

export function formatDuration(
    durationMs: number, fixedTopUnit?: string): string {
  if (durationMs === 0 && !fixedTopUnit) return '0s';

  const isNegative = durationMs < 0;
  const units = getDurationUnits(durationMs);

  let first: DurationUnit|undefined;
  let second: DurationUnit|undefined;

  if (fixedTopUnit) {
    const topIndex = units.findIndex(u => u.unit === fixedTopUnit);
    if (topIndex !== -1) {
      first = units[topIndex];
      second = units[topIndex + 1];  // May be undefined if first is 'ms'
    }
  }

  // Fallback to dynamic evaluation.
  if (!first) {
    const nonZero = units.filter(u => u.val > 0);
    if (nonZero.length === 0) return '0s';
    first = nonZero[0];
    second = nonZero[1];
  }

  let result = '';
  const isSubsecondMode = ['s', 'ms'].includes(first.unit);

  if (isSubsecondMode) {
    const sUnit = units.find(u => u.unit === 's')!;
    const msUnit = units.find(u => u.unit === 'ms')!;
    const decimalsMap: Record<string, number> = {s: 0, ms: 3};
    const maxDecimals =
        second ? decimalsMap[second.unit] : decimalsMap[first.unit];

    if (maxDecimals === 0) {
      result = `${sUnit.val}s`;
    } else {
      let str = `${sUnit.val}.`;
      if (maxDecimals >= 3) str += msUnit.val.toString().padStart(3, '0');
      result = `${str}s`;
    }
  } else {
    result = `${first.val}${first.unit}`;

    if (second) {
      let valStr = second.val.toString();
      if (valStr.length === 1 && second.padTo2) {
        valStr = `0${valStr}`;
      }
      result += `${valStr}${second.unit}`;
    }
  }

  return isNegative ? `-${result}` : result;
}
