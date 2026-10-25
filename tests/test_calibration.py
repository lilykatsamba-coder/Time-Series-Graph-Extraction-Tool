import unittest

import pandas as pd

from src.calibration import (
    PlotBounds,
    convert_pixels_to_observations
)


class TestPixelCalibration(unittest.TestCase):

    def setUp(self):
        self.plot_bounds = PlotBounds(
            left=100,
            right=300,
            top=50,
            bottom=250
        )

        self.pixel_points = pd.DataFrame({
            "x_pixel": [100, 200, 300],
            "y_pixel": [250, 150, 50]
        })

    def test_numeric_time_conversion(self):
        metadata = {
            "time_representation": (
                "Elapsed or numeric time"
            ),
            "time_axis_start": 0,
            "time_axis_end": 30,
            "value_axis_min": 0,
            "value_axis_max": 100
        }

        observations = convert_pixels_to_observations(
            self.pixel_points,
            metadata,
            self.plot_bounds
        )

        self.assertEqual(
            observations["timestamp"].tolist(),
            [0.0, 15.0, 30.0]
        )

        self.assertEqual(
            observations["value"].tolist(),
            [0.0, 50.0, 100.0]
        )

    def test_calendar_time_conversion(self):
        metadata = {
            "time_representation": (
                "Calendar date/time"
            ),
            "time_axis_start": (
                "2024-01-01T00:00:00"
            ),
            "time_axis_end": (
                "2024-01-01T00:30:00"
            ),
            "value_axis_min": 0,
            "value_axis_max": 100
        }

        observations = convert_pixels_to_observations(
            self.pixel_points,
            metadata,
            self.plot_bounds
        )

        timestamps = pd.to_datetime(
            observations["timestamp"]
        )

        self.assertEqual(
            timestamps[0],
            pd.Timestamp("2024-01-01 00:00:00")
        )

        self.assertEqual(
            timestamps[1],
            pd.Timestamp("2024-01-01 00:15:00")
        )

        self.assertEqual(
            timestamps[2],
            pd.Timestamp("2024-01-01 00:30:00")
        )

    def test_y_axis_is_inverted_correctly(self):
        metadata = {
            "time_representation": (
                "Elapsed or numeric time"
            ),
            "time_axis_start": 0,
            "time_axis_end": 10,
            "value_axis_min": 0,
            "value_axis_max": 100
        }

        pixel_points = pd.DataFrame({
            "x_pixel": [100, 100],
            "y_pixel": [50, 250]
        })

        observations = convert_pixels_to_observations(
            pixel_points,
            metadata,
            self.plot_bounds
        )

        self.assertEqual(
            observations["value"].tolist(),
            [100.0, 0.0]
        )

    def test_invalid_plot_bounds_raise_error(self):
        with self.assertRaises(ValueError):
            PlotBounds(
                left=300,
                right=100,
                top=50,
                bottom=250
            )

    def test_missing_pixel_columns_raise_error(self):
        invalid_points = pd.DataFrame({
            "x_pixel": [100, 200]
        })

        metadata = {
            "time_representation": (
                "Elapsed or numeric time"
            ),
            "time_axis_start": 0,
            "time_axis_end": 30,
            "value_axis_min": 0,
            "value_axis_max": 100
        }

        with self.assertRaises(ValueError):
            convert_pixels_to_observations(
                invalid_points,
                metadata,
                self.plot_bounds
            )


if __name__ == "__main__":
    unittest.main()
    