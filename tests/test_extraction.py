import unittest

import pandas as pd

from src.extraction import (
    ExtractionResult,
    OBSERVATION_COLUMNS,
    PIXEL_POINT_COLUMNS
)


class TestExtractionResult(unittest.TestCase):

    def test_empty_result_has_expected_columns(self):
        result = ExtractionResult(success=False)

        self.assertEqual(
            list(result.pixel_points.columns),
            PIXEL_POINT_COLUMNS
        )

        self.assertEqual(
            list(result.observations.columns),
            OBSERVATION_COLUMNS
        )

        self.assertFalse(result.has_observations())

    def test_result_accepts_valid_data(self):
        pixel_points = pd.DataFrame({
            "x_pixel": [10, 20],
            "y_pixel": [50, 45]
        })

        observations = pd.DataFrame({
            "timestamp": [
                "2024-01-01",
                "2024-02-01"
            ],
            "value": [100.0, 105.0],
            "extraction_error": [0.5, 0.7]
        })

        result = ExtractionResult(
            success=True,
            pixel_points=pixel_points,
            observations=observations,
            estimated_extraction_error=0.6
        )

        self.assertTrue(result.has_observations())
        self.assertEqual(len(result.pixel_points), 2)
        self.assertEqual(len(result.observations), 2)

    def test_missing_pixel_column_raises_error(self):
        pixel_points = pd.DataFrame({
            "x_pixel": [10, 20]
        })

        with self.assertRaises(ValueError):
            ExtractionResult(
                success=False,
                pixel_points=pixel_points
            )

    def test_missing_observation_column_raises_error(self):
        observations = pd.DataFrame({
            "timestamp": [
                "2024-01-01"
            ],
            "value": [100.0]
        })

        with self.assertRaises(ValueError):
            ExtractionResult(
                success=False,
                observations=observations
            )

    def test_negative_extraction_error_raises_error(self):
        with self.assertRaises(ValueError):
            ExtractionResult(
                success=False,
                estimated_extraction_error=-1.0
            )

    def test_warning_can_be_added(self):
        result = ExtractionResult(success=False)

        result.add_warning(
            "The uploaded graph could not be analyzed."
        )

        result.add_warning(
            "The uploaded graph could not be analyzed."
        )

        self.assertEqual(len(result.warnings), 1)


if __name__ == "__main__":
    unittest.main()
    