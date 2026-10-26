"""Rolling-origin validation for the forecasting backend."""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral, Real

import numpy as np
import pandas as pd

from src.forecasting import forecast_time_series


@dataclass(frozen=True)
class RollingValidationResult:
    """Summary and point-level results from rolling validation."""

    evaluated_prediction_count: int
    mean_absolute_error: float
    tolerance: float
    exceedance_count: int
    exceedance_proportion: float
    predictions: pd.DataFrame


def _validate_positive_integer(value, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, Integral) or value <= 0:
        raise ValueError(f"{name} must be a positive integer.")


def _validate_tolerance(tolerance: float) -> None:
    if isinstance(tolerance, bool) or not isinstance(tolerance, Real):
        raise ValueError("Tolerance must be a non-negative number.")

    if not np.isfinite(float(tolerance)) or tolerance < 0:
        raise ValueError("Tolerance must be a non-negative finite number.")


def rolling_validate_forecast(
    observations: pd.DataFrame,
    horizon: int,
    tolerance: float,
    metadata: dict,
    min_train_size: int = 3,
) -> RollingValidationResult:
    """Evaluate Holt forecasts with expanding-window rolling origins.

    At each origin, the model is fitted only on observations before that
    origin and forecasts the next ``horizon`` historical observations. Any
    forecast window that would extend beyond the available history is not
    evaluated. Multi-step windows may overlap, which measures performance at
    the requested forecasting horizon.

    The exceedance proportion is an estimated historical proportion of
    predictions whose absolute error exceeded the selected tolerance. It is
    not an exact probability of future exceedance.
    """

    _validate_positive_integer(horizon, "Forecast horizon")
    _validate_positive_integer(min_train_size, "Minimum training size")
    _validate_tolerance(tolerance)

    if not isinstance(observations, pd.DataFrame):
        raise ValueError("Observations must be provided as a pandas DataFrame.")

    required_columns = {"timestamp", "value"}
    missing_columns = required_columns.difference(observations.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Observations are missing required columns: {missing}.")

    values = observations[["timestamp", "value"]].reset_index(drop=True).copy()

    if len(values) < min_train_size + 1:
        raise ValueError(
            "Not enough observations for rolling validation. At least one "
            "historical target is required after the initial training window."
        )

    records = []
    last_origin = len(values) - horizon

    for origin in range(min_train_size, last_origin + 1):
        training = values.iloc[:origin].copy()
        actual = values.iloc[origin:origin + horizon].copy()

        if len(actual) < horizon:
            continue

        forecast = forecast_time_series(
            training,
            horizon,
            metadata,
        )

        actual_values = pd.to_numeric(
            actual["value"], errors="coerce"
        ).to_numpy(dtype=float)
        predicted_values = pd.to_numeric(
            forecast["forecast_value"], errors="coerce"
        ).to_numpy(dtype=float)

        if not np.isfinite(actual_values).all():
            raise ValueError("Observation values must be numeric and finite.")

        if not np.isfinite(predicted_values).all():
            raise ValueError("Forecast values must be finite.")

        for step, (actual_value, predicted_value) in enumerate(
            zip(actual_values, predicted_values), start=1
        ):
            absolute_error = abs(actual_value - predicted_value)
            records.append(
                {
                    "origin_timestamp": training["timestamp"].iloc[-1],
                    "target_timestamp": actual["timestamp"].iloc[step - 1],
                    "actual_value": actual_value,
                    "predicted_value": predicted_value,
                    "absolute_error": absolute_error,
                    "exceeded_tolerance": absolute_error > tolerance,
                }
            )

    if not records:
        raise ValueError(
            "No rolling-validation predictions could be generated. "
            "Provide more observations or reduce the forecast horizon."
        )

    prediction_table = pd.DataFrame(records)
    absolute_errors = prediction_table["absolute_error"]
    exceedances = prediction_table["exceeded_tolerance"]

    return RollingValidationResult(
        evaluated_prediction_count=len(prediction_table),
        mean_absolute_error=float(absolute_errors.mean()),
        tolerance=float(tolerance),
        exceedance_count=int(exceedances.sum()),
        exceedance_proportion=float(exceedances.mean()),
        predictions=prediction_table,
    )
