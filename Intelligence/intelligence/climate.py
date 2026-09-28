"""
WeatherGPT - Member 3
Climate Intelligence Engine

Provides historical weather trend analysis,
baseline comparison, anomaly detection,
and confidence estimation.
"""

from __future__ import annotations

from statistics import mean
from typing import Iterable

from schemas.climate import (
    ClimateAnalysis,
    ClimateMetric,
    TrendDirection,
)


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

STABLE_TREND_THRESHOLD = 1.0


# ---------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------


def _calculate_trend_percentage(
    average_value: float,
    baseline_value: float,
) -> float | None:
    """
    Calculate percentage difference between the observed average
    and the historical baseline.

    Returns None when the baseline is zero because percentage
    change
    cannot be calculated safely.
    """

    if baseline_value == 0:
        return None

    return (
        (average_value - baseline_value)
        / abs(baseline_value)
    ) * 100


def _determine_trend(
    values: list[float],
) -> TrendDirection:
    """
    Determine the direction of the trend using the first and
    last observations.

    A change within STABLE_TREND_THRESHOLD percent is considered
    stable.
    """

    if len(values) < 2:
        return TrendDirection.STABLE

    first_value = values[0]
    last_value = values[-1]

    if first_value == 0:
        if last_value == 0:
            return TrendDirection.STABLE

        return (
            TrendDirection.INCREASING
            if last_value > 0
            else TrendDirection.DECREASING
        )

    change_percentage = (
        (last_value - first_value)
        / abs(first_value)
    ) * 100

    if abs(change_percentage) <= STABLE_TREND_THRESHOLD:
        return TrendDirection.STABLE

    if change_percentage > 0:
        return TrendDirection.INCREASING

    return TrendDirection.DECREASING


def _calculate_confidence(data_points: int) -> float:
    """
    Estimate confidence from the number of observations.

    This is a simple data-coverage confidence score.
    It is NOT a probability that the detected trend is correct.
    """

    if data_points <= 0:
        return 0.0

    if data_points == 1:
        return 0.25

    if data_points == 2:
        return 0.40

    if data_points == 3:
        return 0.55

    if data_points == 4:
        return 0.70

    if data_points == 5:
        return 0.80

    if data_points < 10:
        return 0.85

    if data_points < 30:
        return 0.90

    if data_points < 100:
        return 0.95

    return 1.0


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------


def analyze_climate(
    values: Iterable[float],
    metric: ClimateMetric,
    baseline_value: float,
    period: str,
    location_name: str,
) -> ClimateAnalysis:
    """
    Analyse historical weather observations.

    Parameters
    ----------
    values:
        Historical observations for one weather metric.

    metric:
        Climate metric being analysed.

    baseline_value:
        Historical/reference baseline used for anomaly calculation.

    period:
        Human-readable analysis period such as "2015-2025".

    location_name:
        Location associated with the observations.

    Returns
    -------
    ClimateAnalysis
        Structured climate analysis result.

    Raises
    ------
    ValueError
        If no observations are provided.
    """

    observations = [float(value) for value in values]

    if not observations:
        raise ValueError(
            "At least one historical observation is required."
        )

    average_value = mean(observations)

    anomaly = average_value - baseline_value

    trend = _determine_trend(observations)

    trend_percentage = _calculate_trend_percentage(
        average_value,
        baseline_value,
    )

    confidence = _calculate_confidence(
        len(observations)
    )

    return ClimateAnalysis(
        metric=metric,
        period=period,
        average_value=average_value,
        baseline_value=baseline_value,
        anomaly=anomaly,
        trend=trend,
        trend_percentage=trend_percentage,
        confidence=confidence,
        location_name=location_name,
        data_points=len(observations),
    )


# ---------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------


def analyze_temperature(
    values: Iterable[float],
    baseline_value: float,
    period: str,
    location_name: str,
) -> ClimateAnalysis:
    """Analyse historical temperature observations."""

    return analyze_climate(
        values=values,
        metric=ClimateMetric.TEMPERATURE,
        baseline_value=baseline_value,
        period=period,
        location_name=location_name,
    )


def analyze_rainfall(
    values: Iterable[float],
    baseline_value: float,
    period: str,
    location_name: str,
) -> ClimateAnalysis:
    """Analyse historical rainfall observations."""

    return analyze_climate(
        values=values,
        metric=ClimateMetric.RAINFALL,
        baseline_value=baseline_value,
        period=period,
        location_name=location_name,
    )


def analyze_humidity(
    values: Iterable[float],
    baseline_value: float,
    period: str,
    location_name: str,
) -> ClimateAnalysis:
    """Analyse historical humidity observations."""

    return analyze_climate(
        values=values,
        metric=ClimateMetric.HUMIDITY,
        baseline_value=baseline_value,
        period=period,
        location_name=location_name,
    )


def analyze_wind_speed(
    values: Iterable[float],
    baseline_value: float,
    period: str,
    location_name: str,
) -> ClimateAnalysis:
    """Analyse historical wind-speed observations."""

    return analyze_climate(
        values=values,
        metric=ClimateMetric.WIND_SPEED,
        baseline_value=baseline_value,
        period=period,
        location_name=location_name,
    )