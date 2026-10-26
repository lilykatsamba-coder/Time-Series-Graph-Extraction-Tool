import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)


import numpy as np
import pandas as pd

from src.extractor import extract_chart_data


METADATA_PATH = (
    PROJECT_ROOT
    / "test_data"
    / "test_cases_metadata.json"
)

IMAGES_DIRECTORY = (
    PROJECT_ROOT
    / "test_data"
    / "images"
)

GROUND_TRUTH_DIRECTORY = (
    PROJECT_ROOT
    / "test_data"
    / "ground_truth"
)


CASES_TO_DIAGNOSE = [
    "electricity_demand",
    "machine_vibration",
    "room_temperature"
]


def build_metadata(case_metadata):
    return {
        "time_representation": (
            case_metadata[
                "time_representation"
            ]
        ),
        "time_axis_start": (
            case_metadata[
                "time_axis_range"
            ][0]
        ),
        "time_axis_end": (
            case_metadata[
                "time_axis_range"
            ][1]
        ),
        "value_axis_min": (
            case_metadata[
                "value_axis_range"
            ][0]
        ),
        "value_axis_max": (
            case_metadata[
                "value_axis_range"
            ][1]
        )
    }


def time_to_fraction(
    timestamps,
    start,
    end,
    time_representation
):
    if time_representation == (
        "Elapsed or numeric time"
    ):
        values = np.asarray(
            timestamps,
            dtype=float
        )

        start_value = float(start)
        end_value = float(end)

    else:
        epoch = pd.Timestamp(
            "1970-01-01T00:00:00"
        )

        values = (
            (
                pd.to_datetime(timestamps)
                - epoch
            )
            / pd.Timedelta(seconds=1)
        ).to_numpy(dtype=float)

        start_value = (
            pd.Timestamp(start) - epoch
        ) / pd.Timedelta(seconds=1)

        end_value = (
            pd.Timestamp(end) - epoch
        ) / pd.Timedelta(seconds=1)

    return (
        values - start_value
    ) / (
        end_value - start_value
    )


def diagnose_case(case_id, case_metadata):
    image_path = (
        IMAGES_DIRECTORY
        / case_metadata["image_file"]
    )

    ground_truth_path = (
        GROUND_TRUTH_DIRECTORY
        / case_metadata["ground_truth_file"]
    )

    metadata = build_metadata(
        case_metadata
    )

    extraction_result = extract_chart_data(
        image_path,
        metadata
    )

    if not extraction_result.success:
        print(
            f"{case_id}: extraction failed"
        )

        for warning in extraction_result.warnings:
            print(f"  {warning}")

        return

    ground_truth = pd.read_csv(
        ground_truth_path
    )

    bounds = extraction_result.diagnostics[
        "plot_bounds"
    ]

    detected_points = (
        extraction_result.pixel_points
        .sort_values("x_pixel")
    )

    detected_x = (
        detected_points["x_pixel"]
        .to_numpy(dtype=float)
    )

    detected_y = (
        detected_points["y_pixel"]
        .to_numpy(dtype=float)
    )

    time_fraction = time_to_fraction(
        ground_truth["timestamp"],
        metadata["time_axis_start"],
        metadata["time_axis_end"],
        metadata["time_representation"]
    )

    expected_x = (
        bounds["left"]
        + time_fraction
        * (
            bounds["right"]
            - bounds["left"]
        )
    )

    value_fraction = (
        metadata["value_axis_max"]
        - ground_truth["value"].to_numpy(
            dtype=float
        )
    ) / (
        metadata["value_axis_max"]
        - metadata["value_axis_min"]
    )

    expected_y = (
        bounds["top"]
        + value_fraction
        * (
            bounds["bottom"]
            - bounds["top"]
        )
    )

    print(
        "Raw expected x range:",
        expected_x.min(),
        "to",
        expected_x.max()
    )

    valid_expected_x = (
        (expected_x >= detected_x.min())
        & (expected_x <= detected_x.max())
    )

    if not np.any(valid_expected_x):
        print(
            "No expected ground-truth x-coordinates "
            "overlap the detected line range."
        )

        print(
            "Expected time fraction range:",
            time_fraction.min(),
            "to",
            time_fraction.max()
        )

        print(
            "Metadata time range:",
            metadata["time_axis_start"],
            "to",
            metadata["time_axis_end"]
        )

        return

    expected_x = expected_x[
        valid_expected_x
    ]

    expected_y = expected_y[
        valid_expected_x
    ]

    ground_truth_values = ground_truth[
        "value"
    ].to_numpy(dtype=float)[
        valid_expected_x
    ]

    detected_y_at_expected_x = np.interp(
        expected_x,
        detected_x,
        detected_y
    )

    expected_y_error = np.abs(
        detected_y_at_expected_x
        - expected_y
    )

    detected_value_at_expected_x = (
        metadata["value_axis_max"]
        - (
            (
                detected_y_at_expected_x
                - bounds["top"]
            )
            / (
                bounds["bottom"]
                - bounds["top"]
            )
        )
        * (
            metadata["value_axis_max"]
            - metadata["value_axis_min"]
        )
    )

    value_error = np.abs(
        detected_value_at_expected_x
        - ground_truth_values
    )

    print()
    print(case_id)
    print("-" * len(case_id))
    print(
        "Plot bounds:",
        bounds
    )
    print(
        "Detected x range:",
        detected_x.min(),
        "to",
        detected_x.max()
    )
    print(
        "Expected x range:",
        expected_x.min(),
        "to",
        expected_x.max()
    )
    print(
        "Mean pixel y error:",
        float(np.mean(expected_y_error))
    )
    print(
        "Maximum pixel y error:",
        float(np.max(expected_y_error))
    )
    print(
        "Mean value error:",
        float(np.mean(value_error))
    )
    print(
        "Maximum value error:",
        float(np.max(value_error))
    )


def main():
    with METADATA_PATH.open(
        "r",
        encoding="utf-8"
    ) as file:
        all_metadata = json.load(file)

    for case_id in CASES_TO_DIAGNOSE:
        diagnose_case(
            case_id,
            all_metadata[case_id]
        )


if __name__ == "__main__":
    main()
