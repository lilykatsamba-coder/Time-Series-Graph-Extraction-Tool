import unittest

import pandas as pd

from src.forecasting import forecast_time_series


class TestHoltForecasting(unittest.TestCase):

    def test_numeric_forecast_returns_requested_horizon(self):
        observations = pd.DataFrame({
            "timestamp": [0, 1, 2, 3, 4, 5],
            "value": [10, 12, 14, 16, 18, 20],
        })
        metadata = {
            "time_representation": "Elapsed or numeric time",
            "frequency_value": 1,
            "time_unit": "days",
        }

        result = forecast_time_series(observations, 3, metadata)

        self.assertEqual(len(result), 3)
        self.assertEqual(
            result["timestamp"].tolist(),
            [6.0, 7.0, 8.0],
        )
        self.assertEqual(
            result.columns.tolist(),
            ["timestamp", "forecast_value"],
        )
        self.assertTrue(result["forecast_value"].notna().all())

    def test_calendar_forecast_uses_confirmed_frequency(self):
        observations = pd.DataFrame({
            "timestamp": pd.to_datetime([
                "2024-01-07",
                "2024-01-14",
                "2024-01-21",
                "2024-01-28",
            ]),
            "value": [100, 110, 120, 130],
        })
        metadata = {
            "time_representation": "Calendar date/time",
            "frequency_value": 1,
            "time_unit": "weeks",
        }

        result = forecast_time_series(observations, 2, metadata)

        self.assertEqual(
            result["timestamp"].tolist(),
            [
                pd.Timestamp("2024-02-04"),
                pd.Timestamp("2024-02-11"),
            ],
        )

    def test_empty_observations_raise_error(self):
        observations = pd.DataFrame({
            "timestamp": [],
            "value": [],
        })
        metadata = {
            "time_representation": "Elapsed or numeric time",
            "frequency_value": 1,
            "time_unit": "days",
        }

        with self.assertRaises(ValueError):
            forecast_time_series(observations, 2, metadata)

    def test_too_few_observations_raise_error(self):
        observations = pd.DataFrame({
            "timestamp": [0, 1],
            "value": [10, 12],
        })
        metadata = {
            "time_representation": "Elapsed or numeric time",
            "frequency_value": 1,
            "time_unit": "days",
        }

        with self.assertRaises(ValueError):
            forecast_time_series(observations, 2, metadata)

    def test_duplicate_timestamps_raise_error(self):
        observations = pd.DataFrame({
            "timestamp": [0, 1, 1, 2],
            "value": [10, 12, 13, 14],
        })
        metadata = {
            "time_representation": "Elapsed or numeric time",
            "frequency_value": 1,
            "time_unit": "days",
        }

        with self.assertRaises(ValueError):
            forecast_time_series(observations, 2, metadata)

    def test_non_positive_horizon_raises_error(self):
        observations = pd.DataFrame({
            "timestamp": [0, 1, 2],
            "value": [10, 12, 14],
        })
        metadata = {
            "time_representation": "Elapsed or numeric time",
            "frequency_value": 1,
            "time_unit": "days",
        }

        with self.assertRaises(ValueError):
            forecast_time_series(observations, 0, metadata)


if __name__ == "__main__":
    unittest.main()
