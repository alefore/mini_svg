import math
from dataclasses import dataclass
import datetime
from typing import Callable

from meta import value_with_default


@dataclass(frozen=True)
class PlotTicks:
  values: frozenset[float]
  format_function: Callable[[float], str]


@dataclass(frozen=True)
class PlotTicksConfig:
  # List of values where tics should be drawn. If given, all other fields are
  # ignored.
  values: frozenset[float] | None = None

  # Do not draw more than this number of tics.
  max_count: int | None = None

  # Minimum distance between tics.
  min_distance: float | None = None

  time_format: str | None = None
  value_format: str | None = None

  def with_defaults(self, defaults: "PlotTicksConfig") -> "PlotTicksConfig":
    return PlotTicksConfig(
        values=value_with_default(self.values, defaults.values),
        max_count=value_with_default(self.max_count, defaults.max_count),
        min_distance=value_with_default(self.min_distance,
                                        defaults.min_distance),
        value_format=value_with_default(self.value_format,
                                        defaults.value_format),
        time_format=value_with_default(self.time_format, defaults.time_format))

  def _find_base(self, low: float, high: float) -> float:
    """Returns the ideal distance between tics."""
    assert low < high
    max_count = value_with_default(self.max_count, 10)
    assert max_count
    assert max_count > 0
    assert not self.values
    rough_distance = (high - low) / max_count
    if self.min_distance:
      rough_distance = max(rough_distance, self.min_distance)
    power_of_10 = 10**math.floor(math.log10(rough_distance))
    for factor in [1, 2, 5, 10]:
      candidate: float = power_of_10 * factor
      count = (high - max(low, 0)) // candidate  # Positive tics.
      if low <= 0:
        count += 1  # For zero.
        if low < 0:
          count += abs(low) // candidate  # Negative tics.
      if count <= max_count and (not self.min_distance or
                                 candidate >= self.min_distance):
        return candidate
    assert False

  def _get_values(self, low: float, high: float,
                  base: float) -> frozenset[float]:
    """Returns a list with the values where tics should be drawn."""
    assert low < high
    if self.values is not None:
      return self.values
    max_count = value_with_default(self.max_count, 10)
    assert max_count
    if max_count <= 0:
      return frozenset()
    assert base != 0
    first_tic: float = math.ceil(low / base) * base
    if first_tic > high:
      return frozenset()
    return frozenset(
        first_tic + k * base
        for k in range(min(max_count,
                           int((high - first_tic) / base) + 1)))

  def _fmt_time(self, t: float) -> str:
    time = datetime.datetime.fromtimestamp(t)
    assert time
    assert self.time_format
    return time.strftime(self.time_format)

  def _get_fmt(self, base: float) -> Callable[[float], str]:
    assert self.time_format is None or self.value_format is None
    if self.time_format is not None:
      return self._fmt_time

    if self.value_format:
      value_format = self.value_format
    elif base > 1:
      value_format = ".0f"
    else:
      value_format = f".{abs(math.floor(math.log10(base)))}f"
    return lambda v: format(v, value_format)

  def build(self, low: float, high: float) -> PlotTicks:
    max_count = value_with_default(self.max_count, 10)
    assert max_count is not None
    if max_count <= 0:

      def fail(_: float) -> str:
        raise ValueError("Unexpected call to PlotTicks.format_function.")

      return PlotTicks(values=frozenset(), format_function=fail)

    if self.values:
      sorted_values = sorted(self.values)
      base = sorted_values[1] - sorted_values[0]
      return PlotTicks(values=self.values, format_function=self._get_fmt(base))

    base = self._find_base(low, high)
    return PlotTicks(
        values=self._get_values(low, high, base),
        format_function=self._get_fmt(base))
