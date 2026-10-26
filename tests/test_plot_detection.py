import unittest
from pathlib import Path

import cv2

from src.plot_detection import detect_plot_bounds


class TestPlotDetection(unittest.TestCase):

    def setUp(self):
        self.image_path = Path(
            "test_data",
            "images",
            "product_sales.png"
        )

        self.image = cv2.imread(
            str(self.image_path)
        )

    def test_product_sales_plot_bounds_are_detected(self):
        bounds = detect_plot_bounds(
            self.image_path
        )

        image_height, image_width = self.image.shape[:2]

        self.assertGreater(
            bounds.left,
            0
        )

        self.assertLess(
            bounds.right,
            image_width
        )

        self.assertGreater(
            bounds.top,
            0
        )

        self.assertLess(
            bounds.bottom,
            image_height
        )

        self.assertLess(
            bounds.left,
            bounds.right
        )

        self.assertLess(
            bounds.top,
            bounds.bottom
        )

        self.assertGreater(
            bounds.bottom - bounds.top,
            image_height * 0.5
        )

        self.assertGreater(
            bounds.right - bounds.left,
            image_width * 0.5
        )

        self.assertLess(
            bounds.left,
            image_width * 0.2
        )

        self.assertGreater(
            bounds.right,
            image_width * 0.8
        )

    def test_missing_image_raises_error(self):
        with self.assertRaises(FileNotFoundError):
            detect_plot_bounds(
                "test_data/images/does_not_exist.png"
            )


if __name__ == "__main__":
    unittest.main()
