"""
WeatherGPT - Member 3
Climate Intelligence Engine Tests
"""

import pytest

from intelligence.climate import (
    analyze_climate,
    analyze_temperature,
    analyze_rainfall,
    analyze_humidity,
    analyze_wind_speed,
)
from schemas.climate import (
    ClimateMetric,
    TrendDirection,
)


# ---------------------------------------------------------------------
# Basic climate analysis
# ---------------------------------------------------------------------


def test_climate_analysis_basic():
    """Climate analysis should calculate average and anomaly."""

    result = analyze_climate(
        values=[100, 120, 140],
        metric=ClimateMetric.RAINFALL,
        baseline_value=100,
        period="2023-2025",
        location_name="Sambalpur",
    )

    assert result.metric == ClimateMetric.RAINFALL
    assert result.average_value == 120
    assert result.baseline_value == 100
    assert result.anomaly == 20
    assert result.location_name == "Sambalpur"
    assert result.data_points == 3


# ---------------------------------------------------------------------
# Trend detection
# ---------------------------------------------------------------------


def test_increasing_trend():
    """Increasing historical values should produce an increasing trend."""

    result = analyze_climate(
        values=[100, 110, 120, 130],
        metric=ClimateMetric.RAINFALL,
        baseline_value=100,
        period="2022-2025",
        location_name="Bhubaneswar",
    )

    assert result.trend == TrendDirection.INCREASING


def test_decreasing_trend():
    """Decreasing historical values should produce a decreasing trend."""

    result = analyze_climate(
        values=[130, 120, 110, 100],
        metric=ClimateMetric.TEMPERATURE,
        baseline_value=120,
        period="2022-2025",
        location_name="Delhi",
    )

    assert result.trend == TrendDirection.DECREASING


def test_stable_trend():
    """Small changes should be classified as stable."""

    result = analyze_climate(
        values=[100, 100.2, 100.5, 100.8],
        metric=ClimateMetric.HUMIDITY,
        baseline_value=100,
        period="2022-2025",
        location_name="Cuttack",
    )

    assert result.trend == TrendDirection.STABLE


def test_single_observation_is_stable():
    """A single observation cannot establish a direction."""

    result = analyze_climate(
        values=[35],
        metric=ClimateMetric.TEMPERATURE,
        baseline_value=30,
        period="2025",
        location_name="Bhubaneswar",
    )

    assert result.trend == TrendDirection.STABLE


# ---------------------------------------------------------------------
# Trend percentage
# ---------------------------------------------------------------------


def test_trend_percentage():
    """Trend percentage should be calculated relative to baseline."""

    result = analyze_climate(
        values=[100, 120, 140],
        metric=ClimateMetric.RAINFALL,
        baseline_value=100,
        period="2023-2025",
        location_name="Sambalpur",
    )

    assert result.trend_percentage == pytest.approx(20.0)


def test_negative_trend_percentage():
    """Negative anomaly should produce a negative percentage."""

    result = analyze_climate(
        values=[80, 90, 100],
        metric=ClimateMetric.RAINFALL,
        baseline_value=120,
        period="2023-2025",
        location_name="Puri",
    )

    assert result.trend_percentage == pytest.approx(-25.0)


def test_zero_baseline_percentage():
    """Percentage should be None when baseline is zero."""

    result = analyze_climate(
        values=[10, 20, 30],
        metric=ClimateMetric.RAINFALL,
        baseline_value=0,
        period="2023-2025",
        location_name="Puri",
    )

    assert result.trend_percentage is None


# ---------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------


def test_confidence_increases_with_data():
    """More observations should provide higher data-coverage confidence."""

    result_small = analyze_climate(
        values=[10, 20],
        metric=ClimateMetric.RAINFALL,
        baseline_value=10,
        period="2024-2025",
        location_name="Bhubaneswar",
    )

    result_large = analyze_climate(
        values=list(range(1, 31)),
        metric=ClimateMetric.RAINFALL,
        baseline_value=15,
        period="1996-2025",
        location_name="Bhubaneswar",
    )

    assert result_large.confidence > result_small.confidence


# ---------------------------------------------------------------------
# Empty input
# ---------------------------------------------------------------------


def test_empty_values_rejected():
    """Climate analysis should reject an empty observation list."""

    with pytest.raises(ValueError):
        analyze_climate(
            values=[],
            metric=ClimateMetric.RAINFALL,
            baseline_value=100,
            period="2023-2025",
            location_name="Bhubaneswar",
        )


# ---------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------


def test_temperature_analysis():
    result = analyze_temperature(
        values=[30, 32, 34],
        baseline_value=30,
        period="2023-2025",
        location_name="Bhubaneswar",
    )

    assert result.metric == ClimateMetric.TEMPERATURE
    assert result.average_value == pytest.approx(32.0)


def test_rainfall_analysis():
    result = analyze_rainfall(
        values=[100, 120, 140],
        baseline_value=100,
        period="2023-2025",
        location_name="Sambalpur",
    )

    assert result.metric == ClimateMetric.RAINFALL
    assert result.average_value == pytest.approx(120.0)


def test_humidity_analysis():
    result = analyze_humidity(
        values=[60, 70, 80],
        baseline_value=65,
        period="2023-2025",
        location_name="Cuttack",
    )

    assert result.metric == ClimateMetric.HUMIDITY
    assert result.average_value == pytest.approx(70.0)


def test_wind_speed_analysis():
    result = analyze_wind_speed(
        values=[20, 30, 40],
        baseline_value=25,
        period="2023-2025",
        location_name="Puri",
    )

    assert result.metric == ClimateMetric.WIND_SPEED
    assert result.average_value == pytest.approx(30.0)


# ---------------------------------------------------------------------
# Data point count
# ---------------------------------------------------------------------


def test_data_point_count():
    """Number of observations should be recorded."""

    values = [10, 20, 30, 40, 50]

    result = analyze_climate(
        values=values,
        metric=ClimateMetric.RAINFALL,
        baseline_value=25,
        period="2021-2025",
        location_name="Bhubaneswar",
    )

    assert result.data_points == 5