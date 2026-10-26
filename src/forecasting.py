"""Holt linear forecasting backend.

This module is deliberately independent of Streamlit. It consumes the
frequency-aligned observations confirmed by the user and returns forecast
observations with future timestamps.
"""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral, Real

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import Holt


@dataclass(frozen=True)
class ForecastConfig:
    """Configuration used by the Holt forecasting model."""

    minimum_observations: int = 3
    damped_trend: bool = False


def _validate_horizon(horizon: int) -> None:
    if isinstance(horizon, bool) or not isinstance(horizon, Integral):
        raise ValueError("Forecast horizon must be a positive integer.")

    if horizon <= 0:
        raise ValueError("Forecast horizon must be a positive integer.")


def _normalise_observations(observations: pd.DataFrame) -> pd.DataFrame:
    required_columns = {"timestamp", "value"}

    if not isinstance(observations, pd.DataFrame):
        raise ValueError("Observations must be provided as a pandas DataFrame.")

    missing_columns = required_columns.difference(observations.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Observations are missing required columns: {missing}.")

    values = observations[["timestamp", "value"]].copy()
    values["value"] = pd.to_numeric(values["value"], errors="coerce")

    if values["value"].isna().any():
        raise ValueError("Observation values must be numeric and non-missing.")

    if not np.isfinite(values["value"].to_numpy(dtype=float)).all():
        raise ValueError("Observation values must be finite.")

    return values.reset_index(drop=True)


def _normalise_timestamps(
    observations: pd.DataFrame,
    metadata: dict,
) -> pd.DataFrame:
    values = observations.copy()
    representation = metadata.get("time_representation")

    if representation == "Calendar date/time":
        values["timestamp"] = pd.to_datetime(
            values["timestamp"], errors="coerce"
        )
    elif representation == "Elapsed or numeric time":
        values["timestamp"] = pd.to_numeric(
            values["timestamp"], errors="coerce"
        )
    else:
        raise ValueError("Unsupported or missing time representation.")

    if values["timestamp"].isna().any():
        raise ValueError("Timestamps must be valid and non-missing.")

    if values["timestamp"].duplicated().any():
        raise ValueError("Timestamps must be unique.")

    if not values["timestamp"].is_monotonic_increasing:
        raise ValueError("Timestamps must be in increasing order.")

    return values


def _time_offset(metadata: dict):
    time_unit = str(metadata.get("time_unit", "")).lower()
    time_unit = {
        "second": "seconds",
        "minute": "minutes",
        "hour": "hours",
        "day": "days",
        "week": "weeks",
        "month": "months",
        "year": "years",
    }.get(time_unit, time_unit)
    frequency_value = metadata.get("frequency_value")

    if not isinstance(frequency_value, Real) or isinstance(
        frequency_value, bool
    ) or frequency_value <= 0:
        raise ValueError("Frequency value must be a positive number.")

    if not float(frequency_value).is_integer():
        raise ValueError(
            "Calendar frequency value must be a positive integer."
        )

    frequency_value = int(frequency_value)

    if time_unit == "seconds":
        return pd.Timedelta(seconds=frequency_value)
    if time_unit == "minutes":
        return pd.Timedelta(minutes=frequency_value)
    if time_unit == "hours":
        return pd.Timedelta(hours=frequency_value)
    if time_unit == "days":
        return pd.Timedelta(days=frequency_value)
    if time_unit == "weeks":
        return pd.Timedelta(weeks=frequency_value)
    if time_unit == "months":
        return pd.DateOffset(months=frequency_value)
    if time_unit == "years":
        return pd.DateOffset(years=frequency_value)

    raise ValueError(f"Unsupported time unit: {metadata.get('time_unit')}")


def _build_future_timestamps(
    timestamps: pd.Series,
    horizon: int,
    metadata: dict,
) -> pd.Series:
    representation = metadata["time_representation"]
    last_timestamp = timestamps.iloc[-1]

    if representation == "Elapsed or numeric time":
        if len(timestamps) < 2:
            raise ValueError(
                "At least two timestamps are required for numeric forecasting."
            )

        differences = np.diff(timestamps.to_numpy(dtype=float))

        if not np.all(differences > 0):
            raise ValueError("Numeric timestamps must be strictly increasing.")

        step = float(np.median(differences))
        future = [last_timestamp + step * index for index in range(1, horizon + 1)]
        return pd.Series(future, name="timestamp")

    offset = _time_offset(metadata)
    future = []
    current = last_timestamp

    for _ in range(horizon):
        current = current + offset
        future.append(current)

    return pd.Series(future, name="timestamp")


def forecast_time_series(
    observations: pd.DataFrame,
    horizon: int,
    metadata: dict,
    config: ForecastConfig | None = None,
) -> pd.DataFrame:
    """Forecast a confirmed time series with Holt's linear trend model.

    Parameters
    ----------
    observations:
        Frequency-aligned DataFrame containing ``timestamp`` and ``value``.
    horizon:
        Number of future observations to forecast.
    metadata:
        Metadata containing ``time_representation``, ``time_unit``, and
        ``frequency_value``.
    config:
        Optional model configuration.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing ``timestamp`` and ``forecast_value``.
    """

    _validate_horizon(horizon)
    config = config or ForecastConfig()

    values = _normalise_observations(observations)
    values = _normalise_timestamps(values, metadata)

    if len(values) < config.minimum_observations:
        raise ValueError(
            f"At least {config.minimum_observations} observations are required "
            "for Holt forecasting."
        )

    model = Holt(
        values["value"].to_numpy(dtype=float),
        damped_trend=config.damped_trend,
        initialization_method="estimated",
    )
    fitted_model = model.fit(optimized=True)
    forecast_values = np.asarray(
        fitted_model.forecast(horizon),
        dtype=float,
    )

    future_timestamps = _build_future_timestamps(
        values["timestamp"],
        horizon,
        metadata,
    )

    return pd.DataFrame(
        {
            "timestamp": future_timestamps,
            "forecast_value": forecast_values,
        }
    )
