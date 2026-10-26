from pathlib import Path
from typing import Union

import cv2
import numpy as np
import pandas as pd

from src.calibration import convert_pixels_to_observations
from src.extraction import ExtractionResult
from src.line_extraction import extract_line_pixels
from src.plot_detection import detect_plot_bounds


ImageSource = Union[str, Path]


def _numeric_time(values):
    """Convert numeric or calendar times to comparable float values."""

    series = pd.Series(values)

    if pd.api.types.is_numeric_dtype(series):
        return series.astype(float).to_numpy()

    epoch = pd.Timestamp("1970-01-01T00:00:00")

    return (
        (pd.to_datetime(series) - epoch)
        / pd.Timedelta(seconds=1)
    ).to_numpy(dtype=float)


def _build_target_times(metadata):
    """Build timestamps at the user-confirmed extraction frequency."""

    representation = metadata["time_representation"]
    frequency = float(metadata["frequency_value"])
    time_unit = str(metadata["time_unit"]).lower().strip()
    start = metadata["time_axis_start"]
    end = metadata["time_axis_end"]

    if representation == "Elapsed or numeric time":
        start_value = float(start)
        end_value = float(end)

        target_times = np.arange(
            start_value,
            end_value + frequency * 0.5,
            frequency
        )

        return target_times[
            target_times <= end_value + 1e-12
        ]

    start_timestamp = pd.Timestamp(start)
    end_timestamp = pd.Timestamp(end)

    if time_unit in {"seconds", "second"}:
        offset = pd.Timedelta(seconds=frequency)
    elif time_unit in {"minutes", "minute"}:
        offset = pd.Timedelta(minutes=frequency)
    elif time_unit in {"hours", "hour"}:
        offset = pd.Timedelta(hours=frequency)
    elif time_unit in {"days", "day"}:
        offset = pd.Timedelta(days=frequency)
    elif time_unit in {"weeks", "week"}:
        offset = pd.Timedelta(weeks=frequency)
    elif time_unit in {"months", "month"}:
        if not frequency.is_integer():
            raise ValueError(
                "Monthly frequency must be a whole number."
            )

        offset = pd.DateOffset(
            months=int(frequency)
        )
    elif time_unit in {"years", "year"}:
        if not frequency.is_integer():
            raise ValueError(
                "Yearly frequency must be a whole number."
            )

        offset = pd.DateOffset(
            years=int(frequency)
        )
    else:
        raise ValueError(
            "Calendar resampling requires a supported time unit: "
            "seconds, minutes, hours, days, weeks, months, or years."
        )

    target_times = []
    current = start_timestamp

    while current <= end_timestamp:
        target_times.append(current)
        current = current + offset

    return pd.DatetimeIndex(target_times)


def _resample_observations(observations, metadata):
    """Return observations aligned to the confirmed time frequency."""

    if observations.empty:
        return observations.copy()

    target_times = _build_target_times(metadata)

    source_times = _numeric_time(
        observations["timestamp"]
    )
    target_numeric_times = _numeric_time(
        target_times
    )

    source_values = observations["value"].to_numpy(
        dtype=float
    )

    order = np.argsort(source_times)
    source_times = source_times[order]
    source_values = source_values[order]

    unique_times, unique_indices = np.unique(
        source_times,
        return_index=True
    )

    unique_values = source_values[unique_indices]

    target_values = np.interp(
        target_numeric_times,
        unique_times,
        unique_values
    )

    return pd.DataFrame(
        {
            "timestamp": target_times,
            "value": target_values,
            "extraction_error": np.nan
        }
    )


def extract_chart_data(
    image_source: ImageSource,
    metadata: dict
) -> ExtractionResult:
    """
    Run the extraction pipeline and return observations at the
    user-confirmed time frequency.
    """

    line_result = extract_line_pixels(
        image_source
    )

    if not line_result.success:
        return line_result

    try:
        plot_bounds = detect_plot_bounds(
            image_source
        )

    except (FileNotFoundError, ValueError) as error:
        return ExtractionResult(
            success=False,
            annotated_image=line_result.annotated_image,
            pixel_points=line_result.pixel_points,
            warnings=[str(error)],
            diagnostics={
                "line_detection": line_result.diagnostics
            }
        )

    try:
        pixel_observations = convert_pixels_to_observations(
            line_result.pixel_points,
            metadata,
            plot_bounds
        )

        observations = _resample_observations(
            pixel_observations,
            metadata
        )

    except (KeyError, TypeError, ValueError) as error:
        return ExtractionResult(
            success=False,
            annotated_image=line_result.annotated_image,
            pixel_points=line_result.pixel_points,
            warnings=[
                f"Could not calibrate or resample extracted pixels: {error}"
            ],
            diagnostics={
                "line_detection": line_result.diagnostics,
                "plot_bounds": {
                    "left": plot_bounds.left,
                    "right": plot_bounds.right,
                    "top": plot_bounds.top,
                    "bottom": plot_bounds.bottom
                }
            }
        )

    annotated_image = line_result.annotated_image.copy()

    cv2.rectangle(
        annotated_image,
        pt1=(
            int(plot_bounds.left),
            int(plot_bounds.top)
        ),
        pt2=(
            int(plot_bounds.right),
            int(plot_bounds.bottom)
        ),
        color=(0, 255, 0),
        thickness=2
    )

    diagnostics = {
        "line_detection": line_result.diagnostics,
        "plot_bounds": {
            "left": plot_bounds.left,
            "right": plot_bounds.right,
            "top": plot_bounds.top,
            "bottom": plot_bounds.bottom
        },
        "pixel_observation_count": len(
            pixel_observations
        ),
        "observation_count": len(observations)
    }

    return ExtractionResult(
        success=True,
        annotated_image=annotated_image,
        pixel_points=line_result.pixel_points,
        observations=observations,
        diagnostics=diagnostics
    )
