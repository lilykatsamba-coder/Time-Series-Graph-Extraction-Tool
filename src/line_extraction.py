from pathlib import Path
from typing import Union

import cv2
import numpy as np
import pandas as pd

from src.extraction import ExtractionResult


ImageSource = Union[str, Path]


def _colored_line_mask(image):
    """Detect strongly colored pixels while ignoring gray axes and gridlines."""
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # Saturation excludes black/gray text, axes, and gridlines. This supports
    # red, blue, green, orange, and other clearly colored plotted lines.
    return cv2.inRange(
        hsv_image,
        np.array([0, 70, 45], dtype=np.uint8),
        np.array([179, 255, 255], dtype=np.uint8),
    )


def _significant_hue_groups(image, colored_mask):
    """Count distinct dominant line colors in a saturated-pixel mask."""
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    colored_pixels = hsv_image[colored_mask > 0]

    if len(colored_pixels) == 0:
        return 0

    hue_histogram = np.bincount(
        colored_pixels[:, 0], minlength=180
    ).astype(float)

    # Smooth anti-aliased shades into one color mode.
    smoothed = np.convolve(
        np.r_[hue_histogram[-2:], hue_histogram, hue_histogram[:2]],
        np.ones(5) / 5,
        mode="same",
    )[2:-2]

    threshold = max(10.0, len(colored_pixels) * 0.01)
    active = smoothed >= threshold
    groups = []
    start = None

    for index, is_active in enumerate(np.r_[active, False]):
        if is_active and start is None:
            start = index
        elif not is_active and start is not None:
            groups.append((start, index - 1))
            start = None

    # Hue wraps around at 0/179, so merge red groups at both ends.
    if len(groups) > 1 and groups[0][0] == 0 and groups[-1][1] == 179:
        groups = [(groups[-1][0], groups[0][1])] + groups[1:-1]

    return len(groups)


def extract_line_pixels(image_source: ImageSource) -> ExtractionResult:
    """Detect one colored plotted line in a simple digital chart.

    The MVP supports one clearly colored series. If two or more substantial
    colored components span the plot horizontally, extraction stops with an
    explicit multiple-line warning rather than silently selecting one series.
    """
    image_path = Path(image_source)
    image = cv2.imread(str(image_path))

    if image is None:
        return ExtractionResult(
            success=False,
            warnings=[f"Could not load image: {image_path}"],
        )

    color_mask = _colored_line_mask(image)

    dominant_color_count = _significant_hue_groups(
        image, color_mask
    )

    if dominant_color_count > 1:
        return ExtractionResult(
            success=False,
            warnings=[
                "Multiple plotted lines were detected. The current version supports "
                "only one time-series line."
            ],
            diagnostics={
                "dominant_color_count": dominant_color_count,
            },
        )

    component_count, labels, statistics, _ = cv2.connectedComponentsWithStats(
        color_mask, connectivity=8
    )

    image_height, image_width = image.shape[:2]
    minimum_area = max(20, int(image_height * image_width * 0.00002))
    minimum_horizontal_extent = max(30, int(image_width * 0.20))
    candidates = []

    for component_index in range(1, component_count):
        area = int(statistics[component_index, cv2.CC_STAT_AREA])
        width = int(statistics[component_index, cv2.CC_STAT_WIDTH])
        if area >= minimum_area and width >= minimum_horizontal_extent:
            candidates.append(component_index)

    if not candidates:
        return ExtractionResult(
            success=False,
            warnings=[
                "No plotted line was detected. Upload a graph with one "
                "clearly colored line."
            ],
            diagnostics={"detected_components": int(component_count - 1)},
        )

    if len(candidates) > 1:
        return ExtractionResult(
            success=False,
            warnings=[
                "Multiple plotted lines were detected. The current version supports "
                "only one continuous time-series line."
            ],
            diagnostics={
                "detected_components": int(component_count - 1),
                "candidate_line_count": len(candidates),
            },
        )

    selected_component_index = candidates[0]
    line_mask = np.where(
        labels == selected_component_index, 255, 0
    ).astype(np.uint8)
    y_coordinates, x_coordinates = np.where(line_mask > 0)

    if len(x_coordinates) == 0:
        return ExtractionResult(
            success=False,
            warnings=["The detected component did not contain usable points."],
        )

    pixel_rows = []
    for x_pixel in sorted(np.unique(x_coordinates)):
        y_values = y_coordinates[x_coordinates == x_pixel]
        pixel_rows.append({
            "x_pixel": int(x_pixel),
            "y_pixel": float(np.median(y_values)),
        })

    pixel_points = pd.DataFrame(pixel_rows)
    annotated_image = image.copy()
    for _, point in pixel_points.iterrows():
        cv2.circle(
            annotated_image,
            (int(point["x_pixel"]), int(point["y_pixel"])),
            2,
            (0, 0, 255),
            -1,
        )

    warnings = []
    if image_width < 800 or image_height < 500:
        warnings.append(
            "This image has relatively low resolution. Confirm the axis "
            "metadata carefully; extracted values may be approximate."
        )

    diagnostics = {
        "detected_components": int(component_count - 1),
        "candidate_line_count": 1,
        "selected_component_area": int(
            statistics[selected_component_index, cv2.CC_STAT_AREA]
        ),
        "detected_pixel_count": int(len(x_coordinates)),
        "detected_point_count": int(len(pixel_points)),
        "image_width": int(image_width),
        "image_height": int(image_height),
    }

    return ExtractionResult(
        success=True,
        annotated_image=annotated_image,
        pixel_points=pixel_points,
        warnings=warnings,
        diagnostics=diagnostics,
    )
