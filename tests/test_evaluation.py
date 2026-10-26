import json
import unittest
from pathlib import Path

import pandas as pd

from src.evaluation import evaluate_extraction
from src.extractor import extract_chart_data


class TestExtractionEvaluation(unittest.TestCase):

    def test_numeric_evaluation(self):
        extracted = pd.DataFrame({
            "timestamp": [0, 5, 10],
            "value": [10.0, 19.0, 31.0]
        })

        ground_truth = pd.DataFrame({
            "timestamp": [0, 5, 10],
            "value": [10.0, 20.0, 30.0]
        })

        evaluation = evaluate_extraction(
            extracted,
            ground_truth
        )

        self.assertEqual(
            evaluation.evaluated_point_count,
            3
        )

        self.assertAlmostEqual(
            evaluation.mean_absolute_error,
            2 / 3
        )

        self.assertAlmostEqual(
            evaluation.median_absolute_error,
            1.0
        )

        self.assertAlmostEqual(
            evaluation.maximum_absolute_error,
            1.0
        )

    def test_calendar_evaluation(self):
        extracted = pd.DataFrame({
            "timestamp": pd.to_datetime([
                "2024-01-01",
                "2024-01-15",
                "2024-02-01"
            ]),
            "value": [10.0, 15.0, 20.0]
        })

        ground_truth = pd.DataFrame({
            "timestamp": pd.to_datetime([
                "2024-01-01",
                "2024-02-01"
            ]),
            "value": [10.0, 20.0]
        })

        evaluation = evaluate_extraction(
            extracted,
            ground_truth
        )

        self.assertEqual(
            evaluation.evaluated_point_count,
            3
        )

        self.assertAlmostEqual(
            evaluation.mean_absolute_error,
            0.1612903226,
            places=6
        )

    def test_empty_extracted_data_raises_error(self):
        extracted = pd.DataFrame({
            "timestamp": [],
            "value": []
        })

        ground_truth = pd.DataFrame({
            "timestamp": [0, 1],
            "value": [10, 20]
        })

        with self.assertRaises(ValueError):
            evaluate_extraction(
                extracted,
                ground_truth
            )

    def test_missing_required_column_raises_error(self):
        extracted = pd.DataFrame({
            "timestamp": [0, 1, 2]
        })

        ground_truth = pd.DataFrame({
            "timestamp": [0, 1, 2],
            "value": [10, 20, 30]
        })

        with self.assertRaises(ValueError):
            evaluate_extraction(
                extracted,
                ground_truth
            )

    def test_product_sales_extraction_can_be_evaluated(self):
        image_path = Path(
            "test_data",
            "images",
            "product_sales.png"
        )

        metadata_path = Path(
            "test_data",
            "test_cases_metadata.json"
        )

        ground_truth_path = Path(
            "test_data",
            "ground_truth",
            "product_sales_ground_truth.csv"
        )

        with metadata_path.open(
            "r",
            encoding="utf-8"
        ) as file:
            all_metadata = json.load(file)

        case_metadata = all_metadata[
            "product_sales"
        ]

        metadata = {
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
            ),
            "frequency_value": (
                case_metadata[
                    "frequency_value"
                ]
            ),
            "time_unit": case_metadata[
                "time_unit"
            ]
        }

        extraction_result = extract_chart_data(
            image_path,
            metadata
        )

        self.assertTrue(
            extraction_result.success,
            msg=extraction_result.warnings
        )

        ground_truth = pd.read_csv(
            ground_truth_path
        )

        evaluation = evaluate_extraction(
            extraction_result.observations,
            ground_truth
        )

        self.assertGreater(
            evaluation.evaluated_point_count,
            0
        )

        self.assertGreaterEqual(
            evaluation.mean_absolute_error,
            0.0
        )

        self.assertGreaterEqual(
            evaluation.maximum_absolute_error,
            evaluation.mean_absolute_error
        )


if __name__ == "__main__":
    unittest.main()
