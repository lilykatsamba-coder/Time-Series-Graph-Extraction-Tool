from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
import pandas as pd


PIXEL_POINT_COLUMNS = [
    "x_pixel",
    "y_pixel"
]

OBSERVATION_COLUMNS = [
    "timestamp",
    "value",
    "extraction_error"
]


@dataclass
class ExtractionResult:
    """
    Standard result returned by the graph-extraction engine.

    The extraction engine will populate these fields later.
    The Streamlit interface will consume this structure.
    """

    success: bool

    annotated_image: Optional[np.ndarray] = None

    pixel_points: pd.DataFrame = field(
        default_factory=lambda: pd.DataFrame(
            columns=PIXEL_POINT_COLUMNS
        )
    )

    observations: pd.DataFrame = field(
        default_factory=lambda: pd.DataFrame(
            columns=OBSERVATION_COLUMNS
        )
    )

    estimated_extraction_error: Optional[float] = None

    warnings: list[str] = field(
        default_factory=list
    )

    diagnostics: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self):
        """Validate the result structure."""

        missing_pixel_columns = [
            column
            for column in PIXEL_POINT_COLUMNS
            if column not in self.pixel_points.columns
        ]

        if missing_pixel_columns:
            raise ValueError(
                "Pixel-point data is missing required columns: "
                f"{missing_pixel_columns}"
            )

        missing_observation_columns = [
            column
            for column in OBSERVATION_COLUMNS
            if column not in self.observations.columns
        ]

        if missing_observation_columns:
            raise ValueError(
                "Observation data is missing required columns: "
                f"{missing_observation_columns}"
            )

        if self.estimated_extraction_error is not None:
            if self.estimated_extraction_error < 0:
                raise ValueError(
                    "Estimated extraction error cannot be negative."
                )

    def has_observations(self) -> bool:
        """Return whether extracted observations are available."""

        return not self.observations.empty

    def add_warning(self, warning: str) -> None:
        """Add a user-facing warning to the result."""

        if warning and warning not in self.warnings:
            self.warnings.append(warning)
            