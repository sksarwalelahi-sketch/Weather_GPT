"""
WeatherGPT - Member 3
Climate Analysis Schemas

Defines standardized structures for historical weather,
climate trends, anomalies, and baseline comparisons.
"""

from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class ClimateMetric(str, Enum):
    """
    Weather variables that can be analysed for climate trends.
    """

    TEMPERATURE = "TEMPERATURE"
    RAINFALL = "RAINFALL"
    HUMIDITY = "HUMIDITY"
    WIND_SPEED = "WIND_SPEED"


class TrendDirection(str, Enum):
    """
    Direction of the observed long-term trend.
    """

    INCREASING = "INCREASING"
    DECREASING = "DECREASING"
    STABLE = "STABLE"


class ClimateAnalysis(BaseModel):
    """
    Represents a historical climate analysis result.

    The model supports trend analysis, anomaly detection,
    and comparison against a historical baseline.
    """

    model_config = ConfigDict(
        validate_assignment=True
    )

    metric: ClimateMetric = Field(
        ...,
        description="Weather variable being analysed."
    )

    period: str = Field(
        ...,
        min_length=1,
        description="Analysis period, such as 2010-2025 or January 2026."
    )

    average_value: float = Field(
        ...,
        description="Average value of the metric during the analysis period."
    )

    baseline_value: float = Field(
        ...,
        description="Historical baseline value used for comparison."
    )

    anomaly: float = Field(
        ...,
        description="Difference between the observed average and historical baseline."
    )

    trend: TrendDirection = Field(
        ...,
        description="Observed direction of the historical trend."
    )

    trend_percentage: float | None = Field(
        default=None,
        description="Percentage change relative to the baseline."
    )

    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence in the climate analysis, from 0 to 1."
    )

    location_name: str = Field(
        ...,
        min_length=1,
        description="Location associated with the climate analysis."
    )

    data_points: int | None = Field(
        default=None,
        ge=1,
        description="Number of historical observations used in the analysis."
    )