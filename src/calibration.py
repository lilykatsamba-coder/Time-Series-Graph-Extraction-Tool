from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PlotBounds:
    """
    Pixel boundaries of the graph's plotting area.

    Coordinates follow image convention:
    - x increases from left to right.
    - y increases from top to bottom.
    """

    left: float
    right: float
    top: float
    bottom: float

    def __post_init__(self):
        if self.left >= self.right:
            raise ValueError(
                "Plot left boundary must be smaller than right boundary."
            )

        if self.top >= self.bottom:
            raise ValueError(
                "Plot top boundary must be smaller than bottom boundary."
            )


def _interpolate_time(
    fraction: float,
    start: Any,
    end: Any,
    representation: str
):
    """Convert a normalized x-position into a time value."""

    if representation == "Elapsed or numeric time":
        start_value = float(start)
        end_value = float(end)

        return (
            start_value
            + fraction * (end_value - start_value)
        )

    start_time = pd.Timestamp(start)
    end_time = pd.Timestamp(end)

    return start_time + fraction * (
        end_time - start_time
    )


def convert_pixels_to_observations(
    pixel_points: pd.DataFrame,
    metadata: dict,
    plot_bounds: PlotBounds
) -> pd.DataFrame:
    """
    Convert detected pixel coordinates into observations.

    The x-axis is mapped from left to right.

    The y-axis is mapped from top to bottom because image y
    coordinates increase downwards, while graph values increase
    upwards.
    """

    required_columns = [
        "x_pixel",
        "y_pixel"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in pixel_points.columns
    ]

    if missing_columns:
        raise ValueError(
            "Pixel-point data is missing required columns: "
            f"{missing_columns}"
        )

    if pixel_points.empty:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "value",
                "extraction_error"
            ]
        )

    time_representation = metadata[
        "time_representation"
    ]

    value_axis_min = float(
        metadata["value_axis_min"]
    )

    value_axis_max = float(
        metadata["value_axis_max"]
    )

    time_start = metadata["time_axis_start"]
    time_end = metadata["time_axis_end"]

    x_fraction = (
        pixel_points["x_pixel"] - plot_bounds.left
    ) / (
        plot_bounds.right - plot_bounds.left
    )

    y_fraction = (
        pixel_points["y_pixel"] - plot_bounds.top
    ) / (
        plot_bounds.bottom - plot_bounds.top
    )

    x_fraction = np.clip(x_fraction, 0.0, 1.0)
    y_fraction = np.clip(y_fraction, 0.0, 1.0)

    timestamps = [
        _interpolate_time(
            fraction,
            time_start,
            time_end,
            time_representation
        )
        for fraction in x_fraction
    ]

    values = (
        value_axis_max
        - y_fraction * (
            value_axis_max - value_axis_min
        )
    )

    return pd.DataFrame({
        "timestamp": timestamps,
        "value": values,
        "extraction_error": np.nan
    })
