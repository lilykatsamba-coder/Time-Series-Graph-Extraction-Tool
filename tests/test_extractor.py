import json
import unittest
from pathlib import Path

from src.extractor import extract_chart_data


class TestExtractor(unittest.TestCase):

    def setUp(self):
        self.image_path = Path(
            "test_data",
            "images",
            "product_sales.png"
        )

        metadata_path = Path(
            "test_data",
            "test_cases_metadata.json"
        )

        with metadata_path.open(
            "r",
            encoding="utf-8"
        ) as file:
            all_metadata = json.load(file)

        case_metadata = all_metadata[
            "product_sales"
        ]

        self.metadata = {
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

    def test_product_sales_complete_extraction(self):
        result = extract_chart_data(
            self.image_path,
            self.metadata
        )

        self.assertTrue(
            result.success,
            msg=result.warnings
        )

        self.assertIsNotNone(
            result.annotated_image
        )

        self.assertFalse(
            result.pixel_points.empty
        )

        self.assertFalse(
            result.observations.empty
        )

        self.assertIn(
            "timestamp",
            result.observations.columns
        )

        self.assertIn(
            "value",
            result.observations.columns
        )

        self.assertIn(
            "extraction_error",
            result.observations.columns
        )

    def test_extracted_timestamps_are_monotonic(self):
        result = extract_chart_data(
            self.image_path,
            self.metadata
        )

        self.assertTrue(result.success)

        timestamps = result.observations[
            "timestamp"
        ]

        self.assertTrue(
            timestamps.is_monotonic_increasing
        )

    def test_extracted_values_are_within_axis_range(self):
        result = extract_chart_data(
            self.image_path,
            self.metadata
        )

        self.assertTrue(result.success)

        values = result.observations[
            "value"
        ]

        self.assertGreaterEqual(
            values.min(),
            self.metadata["value_axis_min"]
        )

        self.assertLessEqual(
            values.max(),
            self.metadata["value_axis_max"]
        )

    def test_missing_image_returns_failure(self):
        result = extract_chart_data(
            "test_data/images/does_not_exist.png",
            self.metadata
        )

        self.assertFalse(result.success)

        self.assertTrue(
            len(result.warnings) > 0
        )


if __name__ == "__main__":
    unittest.main()
    