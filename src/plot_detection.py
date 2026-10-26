from pathlib import Path
from typing import Union

import cv2
import numpy as np

from src.calibration import PlotBounds


ImageSource = Union[str, Path]


def _find_long_horizontal_rows(
    binary_image,
    minimum_length
):
    """
    Find rows containing long horizontal chart lines.
    """

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (minimum_length, 1)
    )

    horizontal_lines = cv2.morphologyEx(
        binary_image,
        cv2.MORPH_OPEN,
        kernel
    )

    row_counts = np.count_nonzero(
        horizontal_lines,
        axis=1
    )

    minimum_count = max(
        10,
        int(minimum_length * 0.5)
    )

    return np.where(
        row_counts >= minimum_count
    )[0]


def _find_long_vertical_columns(
    binary_image,
    minimum_length
):
    """
    Find columns containing long vertical chart lines.
    """

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (1, minimum_length)
    )

    vertical_lines = cv2.morphologyEx(
        binary_image,
        cv2.MORPH_OPEN,
        kernel
    )

    column_counts = np.count_nonzero(
        vertical_lines,
        axis=0
    )

    minimum_count = max(
        10,
        int(minimum_length * 0.5)
    )

    return np.where(
        column_counts >= minimum_count
    )[0]


def _find_colored_line_x_extent(image):
    """Find the horizontal extent of a clearly colored plotted line."""
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    colored_mask = cv2.inRange(
        hsv_image,
        np.array([0, 70, 45], dtype=np.uint8),
        np.array([179, 255, 255], dtype=np.uint8),
    )
    y_coordinates, x_coordinates = np.where(colored_mask > 0)
    if len(x_coordinates) == 0:
        return None
    return float(np.min(x_coordinates)), float(np.max(x_coordinates))

def detect_plot_bounds(
    image_source: ImageSource
) -> PlotBounds:
    """
    Detect the plotting-area boundaries of a simple digital chart.

    The method searches for long horizontal and vertical dark
    lines, such as chart spines and gridlines.

    If vertical boundaries cannot be detected directly, the
    horizontal extent of the detected plotted line is used as
    a fallback.
    """

    image_path = Path(image_source)

    image = cv2.imread(str(image_path))

    if image is None:
        raise FileNotFoundError(
            f"Could not load image: {image_path}"
        )

    image_height, image_width = image.shape[:2]

    grayscale = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    binary_image = cv2.threshold(
        grayscale,
        210,
        255,
        cv2.THRESH_BINARY_INV
    )[1]

    horizontal_kernel_length = max(
        20,
        image_width // 8
    )

    vertical_kernel_length = max(
        20,
        image_height // 8
    )

    horizontal_rows = _find_long_horizontal_rows(
        binary_image,
        horizontal_kernel_length
    )

    vertical_columns = _find_long_vertical_columns(
        binary_image,
        vertical_kernel_length
    )

    horizontal_rows = horizontal_rows[
    (horizontal_rows > image_height * 0.02)
    & (horizontal_rows < image_height * 0.98)
    ]

    vertical_columns = vertical_columns[
        (vertical_columns > image_width * 0.02)
        & (vertical_columns < image_width * 0.98)
    ]

    if len(horizontal_rows) < 2:
        raise ValueError(
            "Could not detect the horizontal plot boundaries."
        )

    top = float(np.min(horizontal_rows))
    bottom = float(np.max(horizontal_rows))

    # Two adjacent pixels are one detected spine, not two plot boundaries.
    # Require substantial horizontal separation before treating columns as
    # the left and right boundaries. Otherwise use the colored-line fallback.
    has_separate_vertical_boundaries = (
        len(vertical_columns) >= 2
        and (
            float(np.max(vertical_columns))
            - float(np.min(vertical_columns))
        ) > image_width * 0.5
    )

    if has_separate_vertical_boundaries:
        left = float(np.min(vertical_columns))
        right = float(np.max(vertical_columns))
        detection_method = "chart_lines"

    else:
        colored_line_extent = _find_colored_line_x_extent(
            image
        )

        if colored_line_extent is None:
            raise ValueError(
                "Could not detect the vertical plot boundaries "
                "or the plotted line extent."
            )

        left, right = colored_line_extent
        detection_method = "plotted_line_extent"

    if left >= right:
        raise ValueError(
            "Detected horizontal plot boundaries are invalid."
        )

    if top >= bottom:
        raise ValueError(
            "Detected vertical plot boundaries are invalid."
        )

    return PlotBounds(
        left=left,
        right=right,
        top=top,
        bottom=bottom
    )
