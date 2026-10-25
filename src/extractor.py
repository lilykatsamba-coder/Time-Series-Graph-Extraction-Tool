from pathlib import Path
from typing import Union

import cv2

from src.calibration import convert_pixels_to_observations
from src.extraction import ExtractionResult
from src.line_extraction import extract_line_pixels
from src.plot_detection import detect_plot_bounds


ImageSource = Union[str, Path]


def extract_chart_data(
    image_source: ImageSource,
    metadata: dict
) -> ExtractionResult:
    """
    Run the complete current extraction pipeline.

    The pipeline:
    1. Detects the plotted line.
    2. Detects the plotting-area boundaries.
    3. Converts pixel coordinates into observations.
    4. Annotates the detected plotting area and points.
    """

    line_result = extract_line_pixels(
        image_source
    )

    if not line_result.success:
        return line_result

    try:
        plot_bounds = detect_plot_bounds(
            image_source
        )

    except (FileNotFoundError, ValueError) as error:
        return ExtractionResult(
            success=False,
            annotated_image=line_result.annotated_image,
            pixel_points=line_result.pixel_points,
            warnings=[
                str(error)
            ],
            diagnostics={
                "line_detection": line_result.diagnostics
            }
        )

    try:
        observations = convert_pixels_to_observations(
            line_result.pixel_points,
            metadata,
            plot_bounds
        )

    except (KeyError, TypeError, ValueError) as error:
        return ExtractionResult(
            success=False,
            annotated_image=line_result.annotated_image,
            pixel_points=line_result.pixel_points,
            warnings=[
                f"Could not calibrate extracted pixels: {error}"
            ],
            diagnostics={
                "line_detection": line_result.diagnostics,
                "plot_bounds": {
                    "left": plot_bounds.left,
                    "right": plot_bounds.right,
                    "top": plot_bounds.top,
                    "bottom": plot_bounds.bottom
                }
            }
        )

    annotated_image = line_result.annotated_image.copy()

    cv2.rectangle(
        annotated_image,
        pt1=(
            int(plot_bounds.left),
            int(plot_bounds.top)
        ),
        pt2=(
            int(plot_bounds.right),
            int(plot_bounds.bottom)
        ),
        color=(0, 255, 0),
        thickness=2
    )

    diagnostics = {
        "line_detection": line_result.diagnostics,
        "plot_bounds": {
            "left": plot_bounds.left,
            "right": plot_bounds.right,
            "top": plot_bounds.top,
            "bottom": plot_bounds.bottom
        },
        "observation_count": len(observations)
    }

    return ExtractionResult(
        success=True,
        annotated_image=annotated_image,
        pixel_points=line_result.pixel_points,
        observations=observations,
        diagnostics=diagnostics
    )
