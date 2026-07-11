"""Pure classification functions for drilling analytics.

This module is the parity-critical boundary between the Python UI and the
future TypeScript port. It MUST NOT pull in pandas, Streamlit, Plotly, or
the stdlib logging module — those side-effecting frameworks live in the
adapter layers (`data_processor.py`, `streamlit_app.py`). Only primitive
numeric arguments and primitive return values flow through these functions.

The contracts exported here are the canonical parity surface:

    - `Thresholds` / `MetricThresholds` TypedDict (numeric, no logic).
    - `penetration_rate(depth_m, duration_min) -> float | None`.
    - `classify_with_metric(value, thresholds, metric) -> str | None`.
    - `hardness_index_with_metric(value, thresholds, metric) -> float | None`.
    - `rig_mean_penetration(rates: list[float]) -> float | None`.
    - `rig_normalized_penetration(rate, rig_avg, rig_std) -> float`.

The legacy helpers `classify_duracion` and `hardness_index` are kept
unchanged so existing callers (tests, fixtures, downstream UI) keep
working. The byte-for-byte parity requirement for
`classify_with_metric(v, defaults, "duration") == classify_duracion(v)`
is preserved by using the same strict `<` boundaries inside the
duration branch.
"""

from typing import Literal, TypedDict

import math


class MetricThresholds(TypedDict):
    """Three-cutoff threshold set for a single metric.

    `soft` is the gentlest cutoff, `hard` is the strictest. For duration
    metrics, larger values are harder; for rate metrics, smaller values
    are harder (see `classify_with_metric`).
    """

    soft: float
    medium: float
    hard: float


class Thresholds(TypedDict):
    """Threshold set covering both duration and rate metrics.

    Both sub-dicts are required so UI code can construct one struct and
    pass it everywhere without a separate per-metric configuration.
    """

    duration: MetricThresholds
    rate: MetricThresholds


Metric = Literal["duration", "penetration_rate", "rig_normalized_penetration"]


# Default thresholds — preserve pre-change behaviour for the duration metric.
DEFAULT_DURATION_THRESHOLDS: MetricThresholds = {
    "soft": 16.0,
    "medium": 24.0,
    "hard": 40.0,
}
DEFAULT_RATE_THRESHOLDS: MetricThresholds = {
    "soft": 1.0,
    "medium": 0.7,
    "hard": 0.4,
}
DEFAULT_THRESHOLDS: Thresholds = {
    "duration": DEFAULT_DURATION_THRESHOLDS,
    "rate": DEFAULT_RATE_THRESHOLDS,
}

# Hardness-index upper saturation for the duration metric. Matches the
# legacy `hardness_index` formula's 60-minute cap.
DURATION_INDEX_UPPER_SATURATION: float = 60.0

# Hardness-index upper saturation for the rate metric. Mirrors the
# duration 60-minute cap in m/min units (default 2x the rate soft
# threshold). Rate values above this saturate at index 0 (softest rock).
RATE_INDEX_UPPER_SATURATION: float = 2.0

# Epsilon used to guard against zero-variance rigs in z-score
# normalization. Matches the 1e-9 boundary asserted by the parity
# fixture.
STD_EPSILON: float = 1e-9


def classify_duracion(minutos):
    """Classify hardness category from a duration value (legacy helper).

    Kept byte-for-byte identical to the pre-change function so the
    parity fixture in `classification_cases.json` keeps validating
    against this exact implementation.
    """
    if minutos < 16:
        return "roca suave"
    elif minutos < 24:
        return "roca media"
    elif minutos < 40:
        return "roca dura"
    else:
        return "roca muy dura"


def hardness_index(T):
    """Piecewise-linear hardness index from a duration value (legacy helper).

    Kept byte-for-byte identical to the pre-change function. The
    saturation at `60` minutes defines the `DURATION_INDEX_UPPER_SATURATION`
    constant that `hardness_index_with_metric` reuses.
    """
    if T < 0:
        return 0.0
    elif T <= 16:
        return 25.0 * (T / 16.0)
    elif T <= 24:
        return 25.0 + 25.0 * ((T - 16.0) / 8.0)
    elif T <= 40:
        return 50.0 + 25.0 * ((T - 24.0) / 16.0)
    elif T <= 60:
        return 75.0 + 25.0 * ((T - 40.0) / 20.0)
    else:
        return 100.0


def penetration_rate(depth_m, duration_min):
    """Compute the penetration rate in meters per minute.

    Returns `None` for any non-finite depth, non-finite duration, or a
    non-positive duration. The pandas adapter in `data_processor.py`
    stores `None` cells as `NaN` and the Streamlit UI renders them as
    the em-dash placeholder.

    Args:
        depth_m: Drilled depth in meters (must be finite).
        duration_min: Drilling duration in minutes (must be finite and > 0).

    Returns:
        The penetration rate `depth_m / duration_min` as a float, or
        `None` when the inputs are not usable.
    """
    if depth_m is None or duration_min is None:
        return None
    if not math.isfinite(depth_m) or not math.isfinite(duration_min):
        return None
    if duration_min <= 0:
        return None
    return depth_m / duration_min


def classify_with_metric(value, thresholds, metric):
    """Classify a numeric value into a hardness category using tunable cutoffs.

    Duration metric uses strict `<` boundaries — exact cutoffs fall into
    the harder bucket (e.g. `T == 16` returns `"roca media"`). Rate and
    rig-normalized-penetration metrics are reversed because higher rate
    means softer rock; exact cutoffs also fall into the harder bucket
    (e.g. `rate == 1.0` with defaults returns `"roca media"`).

    Args:
        value: Numeric value to classify. `None` propagates as `None`.
        thresholds: A `Thresholds` TypedDict (both `duration` and `rate`
            sub-dicts must be present).
        metric: One of `"duration"`, `"penetration_rate"`, or
            `"rig_normalized_penetration"`.

    Returns:
        The hardness category as one of `"roca suave"`, `"roca media"`,
        `"roca dura"`, `"roca muy dura"`, or `None` when the value is
        not classifiable.

    Raises:
        ValueError: When `metric` is not one of the three supported
            values. Surfacing this here keeps the function honest about
            its contract without swallowing programmer errors.
    """
    if value is None:
        return None
    if metric == "duration":
        soft = thresholds["duration"]["soft"]
        medium = thresholds["duration"]["medium"]
        hard = thresholds["duration"]["hard"]
        if value < soft:
            return "roca suave"
        if value < medium:
            return "roca media"
        if value < hard:
            return "roca dura"
        return "roca muy dura"
    if metric in ("penetration_rate", "rig_normalized_penetration"):
        soft = thresholds["rate"]["soft"]
        medium = thresholds["rate"]["medium"]
        hard = thresholds["rate"]["hard"]
        if value > soft:
            return "roca suave"
        if value > medium:
            return "roca media"
        if value > hard:
            return "roca dura"
        return "roca muy dura"
    raise ValueError(
        f"Unknown metric {metric!r}; expected one of "
        "'duration', 'penetration_rate', 'rig_normalized_penetration'."
    )


def hardness_index_with_metric(value, thresholds, metric):
    """Compute the piecewise-linear hardness index using tunable cutoffs.

    The duration metric mirrors the legacy `hardness_index` formula but
    reuses the supplied thresholds instead of hardcoded constants.
    Exact cutoffs map to the higher index of the adjacent segment, which
    keeps `classify_with_metric` and `hardness_index_with_metric`
    consistent at boundaries.

    The rate metric is inverted: a higher rate is softer rock, so the
    index decreases as rate grows. The `RATE_INDEX_UPPER_SATURATION`
    constant defines the saturation cap that maps to index `0`.

    Args:
        value: Numeric value to map. `None` propagates as `None`.
        thresholds: A `Thresholds` TypedDict.
        metric: One of the three `Metric` literals.

    Returns:
        A `float` in `[0, 100]` or `None` when the value is not
        indexable.

    Raises:
        ValueError: When `metric` is not supported.
    """
    if value is None:
        return None
    if metric == "duration":
        soft = thresholds["duration"]["soft"]
        medium = thresholds["duration"]["medium"]
        hard = thresholds["duration"]["hard"]
        if value <= 0:
            return 0.0
        if value <= soft:
            return 25.0 * (value / soft)
        if value <= medium:
            return 25.0 + 25.0 * ((value - soft) / (medium - soft))
        if value <= hard:
            return 50.0 + 25.0 * ((value - medium) / (hard - medium))
        if value <= DURATION_INDEX_UPPER_SATURATION:
            return 75.0 + 25.0 * (
                (value - hard)
                / (DURATION_INDEX_UPPER_SATURATION - hard)
            )
        return 100.0
    if metric in ("penetration_rate", "rig_normalized_penetration"):
        soft = thresholds["rate"]["soft"]
        medium = thresholds["rate"]["medium"]
        hard = thresholds["rate"]["hard"]
        upper = RATE_INDEX_UPPER_SATURATION
        if value > upper:
            return 0.0
        if value > soft:
            # [soft, upper] -> [25, 0]: faster = softer.
            return 25.0 * (upper - value) / (upper - soft)
        if value > medium:
            # [medium, soft] -> [50, 25].
            return 25.0 + 25.0 * (soft - value) / (soft - medium)
        if value > hard:
            # [hard, medium] -> [75, 50].
            return 50.0 + 25.0 * (medium - value) / (medium - hard)
        # [0, hard] -> [100, 75]: slow = very hard.
        return 75.0 + 25.0 * (hard - value) / hard
    raise ValueError(
        f"Unknown metric {metric!r}; expected one of "
        "'duration', 'penetration_rate', 'rig_normalized_penetration'."
    )


def rig_mean_penetration(rates):
    """Compute the arithmetic mean of a list of penetration rates.

    Skips `None` and non-finite entries silently so a partially populated
    rig column does not crash the UI. Returns `None` when the input is
    empty or every entry is unusable.

    Args:
        rates: Iterable of numeric rate values.

    Returns:
        The mean as a float, or `None` when no finite value is present.
    """
    if not rates:
        return None
    total = 0.0
    count = 0
    for rate in rates:
        if rate is None:
            continue
        if not math.isfinite(rate):
            continue
        total += rate
        count += 1
    if count == 0:
        return None
    return total / count


def rig_normalized_penetration(rate, rig_avg, rig_std):
    """Z-score a single rate against a rig's mean and standard deviation.

    Returns `0.0` when the standard deviation is at or below the
    `STD_EPSILON` epsilon (single-sample or zero-variance rigs) so the
    UI never raises `ZeroDivisionError`. Also returns `0.0` for `None`
    or non-finite inputs.

    Args:
        rate: A penetration rate in m/min.
        rig_avg: The rig's mean penetration rate.
        rig_std: The rig's standard deviation.

    Returns:
        The standardized z-score as a float.
    """
    if rate is None:
        return 0.0
    if not math.isfinite(rate):
        return 0.0
    if rig_std is None or rig_std <= STD_EPSILON:
        return 0.0
    if not math.isfinite(rig_avg) or not math.isfinite(rig_std):
        return 0.0
    return (rate - rig_avg) / rig_std