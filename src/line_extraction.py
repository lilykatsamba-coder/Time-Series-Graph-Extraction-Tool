from pathlib import Path
from typing import Union

import cv2
import numpy as np
import pandas as pd

from src.extraction import ExtractionResult


ImageSource = Union[str, Path]


def extract_line_pixels(
    image_source: ImageSource
) -> ExtractionResult:
    """
    Detect the plotted blue line in a simple digital chart.

    This first baseline supports the generated charts whose plotted
    line uses Matplotlib's royalblue color.

    It returns pixel coordinates only. Time/value calibration will be
    added in a later commit.
    """

    image_path = Path(image_source)

    image = cv2.imread(str(image_path))

    if image is None:
        return ExtractionResult(
            success=False,
            warnings=[
                f"Could not load image: {image_path}"
            ]
        )

    hsv_image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2HSV
    )

    # Matplotlib royalblue is approximately HSV:
    # hue around 110-120 in OpenCV's 0-179 hue scale.
    lower_blue = np.array(
        [90, 50, 40],
        dtype=np.uint8
    )

    upper_blue = np.array(
        [140, 255, 255],
        dtype=np.uint8
    )

    color_mask = cv2.inRange(
        hsv_image,
        lower_blue,
        upper_blue
    )

    # Remove very small isolated detections.
    connected_components = cv2.connectedComponentsWithStats(
        color_mask,
        connectivity=8
    )

    component_count, labels, statistics, _ = (
        connected_components
    )

    if component_count <= 1:
        return ExtractionResult(
            success=False,
            warnings=[
                "No plotted line was detected."
            ],
            diagnostics={
                "detected_components": 0
            }
        )

    component_areas = statistics[1:, cv2.CC_STAT_AREA]

    largest_component_index = (
        int(np.argmax(component_areas)) + 1
    )

    largest_component_area = component_areas[
        largest_component_index - 1
    ]

    line_mask = np.where(
        labels == largest_component_index,
        255,
        0
    ).astype(np.uint8)

    y_coordinates, x_coordinates = np.where(
        line_mask > 0
    )

    if len(x_coordinates) == 0:
        return ExtractionResult(
            success=False,
            warnings=[
                "The detected component did not contain usable points."
            ]
        )

    # Collapse detected pixels into one point per x-coordinate.
    # The median y-coordinate reduces the effect of line thickness.
    pixel_rows = []

    for x_pixel in sorted(np.unique(x_coordinates)):
        y_values = y_coordinates[
            x_coordinates == x_pixel
        ]

        pixel_rows.append({
            "x_pixel": int(x_pixel),
            "y_pixel": float(np.median(y_values))
        })

    pixel_points = pd.DataFrame(pixel_rows)

    annotated_image = image.copy()

    for _, point in pixel_points.iterrows():
        center = (
            int(point["x_pixel"]),
            int(point["y_pixel"])
        )

        cv2.circle(
            annotated_image,
            center=center,
            radius=2,
            color=(0, 0, 255),
            thickness=-1
        )

    diagnostics = {
        "detected_components": int(component_count - 1),
        "selected_component_area": int(
            largest_component_area
        ),
        "detected_pixel_count": int(
            len(x_coordinates)
        ),
        "detected_point_count": int(
            len(pixel_points)
        ),
        "image_width": int(image.shape[1]),
        "image_height": int(image.shape[0])
    }

    return ExtractionResult(
        success=True,
        annotated_image=annotated_image,
        pixel_points=pixel_points,
        diagnostics=diagnostics
    )
