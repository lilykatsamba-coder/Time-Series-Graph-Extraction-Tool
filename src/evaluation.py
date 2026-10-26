from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class ExtractionEvaluation:
    """Accuracy results for an extraction against ground truth."""

    point_results: pd.DataFrame
    mean_absolute_error: float
    median_absolute_error: float
    maximum_absolute_error: float
    evaluated_point_count: int


def _convert_time_to_numeric(
    timestamps
):
    """
    Convert timestamps to seconds from the Unix epoch.

    Numeric elapsed-time values remain numeric.
    Calendar timestamps are converted using timedelta
    arithmetic so the result is independent of Pandas' internal
    datetime resolution.
    """

    series = pd.Series(timestamps)

    if pd.api.types.is_numeric_dtype(series):
        return series.astype(float).to_numpy()

    datetime_values = pd.to_datetime(series)

    epoch = pd.Timestamp(
        "1970-01-01T00:00:00"
    )

    return (
        (
            datetime_values - epoch
        )
        / pd.Timedelta(seconds=1)
    ).to_numpy(dtype=float)


def evaluate_extraction(
    extracted_observations: pd.DataFrame,
    ground_truth: pd.DataFrame
) -> ExtractionEvaluation:
    """
    Compare extracted observations with ground-truth values.

    Ground-truth columns:
    - timestamp
    - value

    Extracted columns:
    - timestamp
    - value
    """

    required_columns = [
        "timestamp",
        "value"
    ]

    for column in required_columns:
        if column not in extracted_observations.columns:
            raise ValueError(
                "Extracted observations are missing the "
                f"'{column}' column."
            )

        if column not in ground_truth.columns:
            raise ValueError(
                "Ground-truth data is missing the "
                f"'{column}' column."
            )

    if extracted_observations.empty:
        raise ValueError(
            "Extracted observations cannot be empty."
        )

    if ground_truth.empty:
        raise ValueError(
            "Ground-truth data cannot be empty."
        )

    extracted_axis = _convert_time_to_numeric(
        extracted_observations["timestamp"]
    )

    ground_truth_axis = _convert_time_to_numeric(
        ground_truth["timestamp"]
    )

    extracted_values = (
        extracted_observations["value"]
        .astype(float)
        .to_numpy()
    )

    ground_truth_values = (
        ground_truth["value"]
        .astype(float)
        .to_numpy()
    )

    sort_order = np.argsort(ground_truth_axis)

    ground_truth_axis = ground_truth_axis[
        sort_order
    ]

    ground_truth_values = ground_truth_values[
        sort_order
    ]

    valid_mask = (
        (extracted_axis >= ground_truth_axis[0])
        & (extracted_axis <= ground_truth_axis[-1])
    )

    if not np.any(valid_mask):
        raise ValueError(
            "No extracted timestamps overlap the "
            "ground-truth time range."
        )

    valid_extracted_axis = extracted_axis[
        valid_mask
    ]

    valid_extracted_values = extracted_values[
        valid_mask
    ]

    interpolated_true_values = np.interp(
        valid_extracted_axis,
        ground_truth_axis,
        ground_truth_values
    )

    extraction_errors = np.abs(
        valid_extracted_values
        - interpolated_true_values
    )

    valid_timestamps = (
        extracted_observations.loc[
            valid_mask,
            "timestamp"
        ]
        .reset_index(drop=True)
    )

    point_results = pd.DataFrame({
        "timestamp": valid_timestamps,
        "extracted_value": valid_extracted_values,
        "true_value": interpolated_true_values,
        "extraction_error": extraction_errors
    })

    return ExtractionEvaluation(
        point_results=point_results,
        mean_absolute_error=float(
            np.mean(extraction_errors)
        ),
        median_absolute_error=float(
            np.median(extraction_errors)
        ),
        maximum_absolute_error=float(
            np.max(extraction_errors)
        ),
        evaluated_point_count=len(point_results)
    )
