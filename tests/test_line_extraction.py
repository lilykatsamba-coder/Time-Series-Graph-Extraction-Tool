import unittest
from pathlib import Path

from src.line_extraction import extract_line_pixels


class TestLineExtraction(unittest.TestCase):

    def setUp(self):
        self.image_path = Path(
            "test_data",
            "images",
            "product_sales.png"
        )

    def test_product_sales_line_is_detected(self):
        result = extract_line_pixels(
            self.image_path
        )

        self.assertTrue(result.success)

        self.assertIsNotNone(
            result.annotated_image
        )

        self.assertFalse(
            result.pixel_points.empty
        )

        self.assertGreater(
            len(result.pixel_points),
            50
        )

        self.assertIn(
            "x_pixel",
            result.pixel_points.columns
        )

        self.assertIn(
            "y_pixel",
            result.pixel_points.columns
        )

    def test_detected_x_coordinates_are_sorted(self):
        result = extract_line_pixels(
            self.image_path
        )

        x_coordinates = (
            result.pixel_points["x_pixel"]
            .tolist()
        )

        self.assertEqual(
            x_coordinates,
            sorted(x_coordinates)
        )

    def test_missing_image_returns_failure(self):
        result = extract_line_pixels(
            "test_data/images/does_not_exist.png"
        )

        self.assertFalse(result.success)

        self.assertTrue(
            len(result.warnings) > 0
        )


if __name__ == "__main__":
    unittest.main()
    