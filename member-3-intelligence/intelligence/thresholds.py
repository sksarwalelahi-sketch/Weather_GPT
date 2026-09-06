"""
WeatherGPT - Member 3
Risk Threshold Configuration

This module contains configurable baseline thresholds used by
the Weather Intelligence risk engine.

IMPORTANT:
These values are engineering baseline values for development.
They are NOT represented as official IMD warning thresholds.

Official meteorological thresholds can be incorporated later
without changing the risk-engine implementation.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskThresholds:
    """
    Defines the boundaries used to classify a weather variable.

    Values represent the beginning of each risk category.

    Example:

        low=10
        moderate=35
        high=65

    means:

        value < 10      → LOW
        10 <= value <35 → MODERATE
        35 <= value <65 → HIGH
        value >= 65     → SEVERE
    """

    low: float
    moderate: float
    high: float
    severe: float

    def __post_init__(self) -> None:
        """
        Validate threshold ordering.
        """

        if self.low < 0:
            raise ValueError("Low threshold cannot be negative.")

        if not (
            self.low
            < self.moderate
            < self.high
            < self.severe
        ):
            raise ValueError(
                "Thresholds must satisfy: "
                "low < moderate < high < severe."
            )


# ---------------------------------------------------------------------------
# Baseline weather thresholds
# ---------------------------------------------------------------------------

RAINFALL = RiskThresholds(
    low=10.0,
    moderate=35.0,
    high=65.0,
    severe=100.0,
)

WIND_SPEED = RiskThresholds(
    low=20.0,
    moderate=40.0,
    high=60.0,
    severe=90.0,
)

TEMPERATURE = RiskThresholds(
    low=32.0,
    moderate=37.0,
    high=40.0,
    severe=45.0,
)