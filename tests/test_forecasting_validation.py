import unittest

import pandas as pd

from src.validation import rolling_validate_forecast


class TestRollingForecastValidation(unittest.TestCase):

    def setUp(self):
        self.metadata = {
            "time_representation": "Elapsed or numeric time",
            "frequency_value": 1,
            "time_unit": "days",
        }

    def test_rolling_validation_returns_prediction_records(self):
        observations = pd.DataFrame({
            "timestamp": list(range(10)),
            "value": [10, 12, 14, 16, 18, 20, 22, 24, 26, 28],
        })

        result = rolling_validate_forecast(
            observations,
            horizon=1,
            tolerance=1.0,
            metadata=self.metadata,
        )

        self.assertEqual(result.evaluated_prediction_count, 7)
        self.assertEqual(len(result.predictions), 7)
        self.assertGreaterEqual(result.mean_absolute_error, 0.0)
        self.assertGreaterEqual(result.exceedance_proportion, 0.0)
        self.assertLessEqual(result.exceedance_proportion, 1.0)

    def test_tolerance_exceedance_is_reported_as_historical_proportion(self):
        observations = pd.DataFrame({
            "timestamp": list(range(8)),
            "value": [10, 11, 10, 11, 10, 30, 31, 30],
        })

        result = rolling_validate_forecast(
            observations,
            horizon=1,
            tolerance=0.0,
            metadata=self.metadata,
        )

        self.assertEqual(
            result.exceedance_count,
            int(
                result.predictions["exceeded_tolerance"].sum()
            ),
        )
        self.assertAlmostEqual(
            result.exceedance_proportion,
            result.exceedance_count / result.evaluated_prediction_count,
        )

    def test_multi_step_validation_evaluates_each_forecast_step(self):
        observations = pd.DataFrame({
            "timestamp": list(range(9)),
            "value": [5, 6, 7, 8, 9, 10, 11, 12, 13],
        })

        result = rolling_validate_forecast(
            observations,
            horizon=2,
            tolerance=1.0,
            metadata=self.metadata,
        )

        self.assertEqual(result.evaluated_prediction_count, 10)
        self.assertEqual(
            result.predictions["target_timestamp"].tolist(),
            [3, 4, 4, 5, 5, 6, 6, 7, 7, 8],
        )

    def test_calendar_validation_is_supported(self):
        observations = pd.DataFrame({
            "timestamp": pd.date_range(
                "2024-01-07", periods=8, freq="W-SUN"
            ),
            "value": [100, 102, 104, 106, 108, 110, 112, 114],
        })
        metadata = {
            "time_representation": "Calendar date/time",
            "frequency_value": 1,
            "time_unit": "weeks",
        }

        result = rolling_validate_forecast(
            observations,
            horizon=1,
            tolerance=5.0,
            metadata=metadata,
        )

        self.assertGreater(result.evaluated_prediction_count, 0)
        self.assertTrue(
            pd.api.types.is_datetime64_any_dtype(
                result.predictions["target_timestamp"]
            )
        )

    def test_invalid_tolerance_raises_error(self):
        observations = pd.DataFrame({
            "timestamp": [0, 1, 2, 3],
            "value": [1, 2, 3, 4],
        })

        with self.assertRaises(ValueError):
            rolling_validate_forecast(
                observations,
                horizon=1,
                tolerance=-1.0,
                metadata=self.metadata,
            )

    def test_insufficient_history_raises_error(self):
        observations = pd.DataFrame({
            "timestamp": [0, 1, 2],
            "value": [1, 2, 3],
        })

        with self.assertRaises(ValueError):
            rolling_validate_forecast(
                observations,
                horizon=1,
                tolerance=1.0,
                metadata=self.metadata,
            )


if __name__ == "__main__":
    unittest.main()
