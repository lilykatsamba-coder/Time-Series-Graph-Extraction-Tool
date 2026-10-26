import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)


import pandas as pd

from src.evaluation import evaluate_extraction
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


def benchmark_case(case_id, case_metadata):
    """Run extraction and evaluation for one supported case."""

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
        return {
            "case": case_id,
            "status": "FAILED",
            "mean_error": None,
            "median_error": None,
            "maximum_error": None,
            "normalized_error_percent": None,
            "value_range": None,
            "points": 0,
            "message": "; ".join(
                extraction_result.warnings
            )
        }

    ground_truth = pd.read_csv(
        ground_truth_path
    )

    evaluation = evaluate_extraction(
        extraction_result.observations,
        ground_truth
    )

    ground_truth_value_range = (
        ground_truth["value"].max()
        - ground_truth["value"].min()
    )

    if ground_truth_value_range > 0:
        normalized_error_percent = (
            evaluation.mean_absolute_error
            / ground_truth_value_range
            * 100
        )
    else:
        normalized_error_percent = None

    return {
        "case": case_id,
        "status": "OK",
        "mean_error": evaluation.mean_absolute_error,
        "median_error": evaluation.median_absolute_error,
        "maximum_error": evaluation.maximum_absolute_error,
        "normalized_error_percent": normalized_error_percent,
        "value_range": ground_truth_value_range,
        "points": evaluation.evaluated_point_count,
        "message": ""
    }


def main():
    with METADATA_PATH.open(
        "r",
        encoding="utf-8"
    ) as file:
        all_metadata = json.load(file)

    results = []

    for case_id, case_metadata in all_metadata.items():
        if not case_metadata.get(
            "supported_by_mvp",
            False
        ):
            continue

        results.append(
            benchmark_case(
                case_id,
                case_metadata
            )
        )

    print(
        "Extraction benchmark"
    )
    print(
        "=" * 90
    )

    for result in results:
        print(
            f"{result['case']}: "
            f"{result['status']}"
        )

        if result["status"] == "OK":
            print(
                f"  Mean absolute error: "
                f"{result['mean_error']:.4f}"
            )

            print(
                f"  Median absolute error: "
                f"{result['median_error']:.4f}"
            )

            print(
                f"  Maximum absolute error: "
                f"{result['maximum_error']:.4f}"
            )

            print(
                f"  Ground-truth value range: "
                f"{result['value_range']:.4f}"
            )

            print(
                f"  Normalized mean error: "
                f"{result['normalized_error_percent']:.4f}%"
            )

            print(
                f"  Evaluated points: "
                f"{result['points']}"
            )

        else:
            print(
                f"  Message: "
                f"{result['message']}"
            )


if __name__ == "__main__":
    main()
    