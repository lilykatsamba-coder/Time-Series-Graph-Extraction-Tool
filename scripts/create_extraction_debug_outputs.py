import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)


import cv2
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

OUTPUT_DIRECTORY = (
    PROJECT_ROOT
    / "debug_outputs"
)

DEBUG_CASES = [
    "machine_vibration",
    "electricity_demand",
    "room_temperature"
]


def build_extraction_metadata(case_metadata):
    """Convert generator metadata to extractor metadata."""

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


def convert_timestamps_to_numeric(
    timestamps,
    time_representation
):
    """Convert numeric or calendar timestamps to floats."""

    timestamp_series = pd.Series(
        timestamps
    )

    if time_representation == (
        "Elapsed or numeric time"
    ):
        return timestamp_series.astype(
            float
        ).to_numpy()

    datetime_values = pd.to_datetime(
        timestamp_series
    )

    return (
        datetime_values.astype("int64")
        .to_numpy()
        / 1_000_000_000
    )


def draw_ground_truth_curve(
    image,
    ground_truth,
    metadata,
    plot_bounds
):
    """Draw the ground-truth curve in magenta."""

    time_representation = metadata[
        "time_representation"
    ]

    ground_truth_time = (
        convert_timestamps_to_numeric(
            ground_truth["timestamp"],
            time_representation
        )
    )

    axis_start = convert_timestamps_to_numeric(
        [metadata["time_axis_start"]],
        time_representation
    )[0]

    axis_end = convert_timestamps_to_numeric(
        [metadata["time_axis_end"]],
        time_representation
    )[0]

    value_axis_min = float(
        metadata["value_axis_min"]
    )

    value_axis_max = float(
        metadata["value_axis_max"]
    )

    valid_mask = (
        (ground_truth_time >= axis_start)
        & (ground_truth_time <= axis_end)
        & (
            ground_truth["value"].to_numpy()
            >= value_axis_min
        )
        & (
            ground_truth["value"].to_numpy()
            <= value_axis_max
        )
    )

    if not np.any(valid_mask):
        return image

    valid_times = ground_truth_time[
        valid_mask
    ]

    valid_values = ground_truth.loc[
        valid_mask,
        "value"
    ].astype(float).to_numpy()

    time_fraction = (
        valid_times - axis_start
    ) / (
        axis_end - axis_start
    )

    value_fraction = (
        valid_values - value_axis_min
    ) / (
        value_axis_max - value_axis_min
    )

    x_pixels = (
        plot_bounds["left"]
        + time_fraction
        * (
            plot_bounds["right"]
            - plot_bounds["left"]
        )
    )

    y_pixels = (
        plot_bounds["bottom"]
        - value_fraction
        * (
            plot_bounds["bottom"]
            - plot_bounds["top"]
        )
    )

    points = [
        (
            int(round(x_pixel)),
            int(round(y_pixel))
        )
        for x_pixel, y_pixel in zip(
            x_pixels,
            y_pixels
        )
    ]

    if len(points) >= 2:
        cv2.polylines(
            image,
            [np.array(points, dtype=np.int32)],
            isClosed=False,
            color=(255, 0, 255),
            thickness=2
        )

    return image


def add_legend(image):
    """Add a small color legend to the image."""

    height, width = image.shape[:2]

    legend_x = 20
    legend_y = 25

    cv2.putText(
        image,
        "Red: extracted line",
        (legend_x, legend_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 0, 255),
        2,
        cv2.LINE_AA
    )

    cv2.putText(
        image,
        "Magenta: ground truth",
        (legend_x, legend_y + 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 0, 255),
        2,
        cv2.LINE_AA
    )

    cv2.putText(
        image,
        "Green: detected plot bounds",
        (legend_x, legend_y + 56),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2,
        cv2.LINE_AA
    )

    return image


def create_debug_output(
    case_id,
    case_metadata
):
    """Create one annotated diagnostic image."""

    image_path = (
        IMAGES_DIRECTORY
        / case_metadata["image_file"]
    )

    ground_truth_path = (
        GROUND_TRUTH_DIRECTORY
        / case_metadata["ground_truth_file"]
    )

    metadata = build_extraction_metadata(
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
            print(
                f"  {warning}"
            )

        return

    ground_truth = pd.read_csv(
        ground_truth_path
    )

    annotated_image = (
        extraction_result.annotated_image.copy()
    )

    plot_bounds = (
        extraction_result.diagnostics[
            "plot_bounds"
        ]
    )

    annotated_image = draw_ground_truth_curve(
        annotated_image,
        ground_truth,
        metadata,
        plot_bounds
    )

    annotated_image = add_legend(
        annotated_image
    )

    output_path = (
        OUTPUT_DIRECTORY
        / f"{case_id}_debug.png"
    )

    cv2.imwrite(
        str(output_path),
        annotated_image
    )

    print(
        f"{case_id}: saved {output_path}"
    )


def main():
    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )

    with METADATA_PATH.open(
        "r",
        encoding="utf-8"
    ) as file:
        all_metadata = json.load(file)

    for case_id in DEBUG_CASES:
        if case_id not in all_metadata:
            print(
                f"{case_id}: metadata not found"
            )
            continue

        create_debug_output(
            case_id,
            all_metadata[case_id]
        )


if __name__ == "__main__":
    main()
    