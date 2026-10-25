# Time Series Graph Extraction and Forecasting Tool

## Project Overview

This project is a desktop-only Streamlit web application for extracting approximate time-series data from digital graph images.

The intended final tool will allow users to:

- Upload a time-series graph image.
- Confirm graph metadata.
- Extract approximate data points from the plotted line.
- Inspect and edit the extracted data.
- Download the extracted data.
- Continue to forecasting using the corrected data.
- Evaluate forecast performance using rolling validation.

The current implementation covers the initial upload and metadata-confirmation workflow. Image analysis, data extraction, forecasting, and validation are not yet implemented.

## Problem Statement

Historical data may no longer be available while visualizations of that data still exist in reports, presentations, dashboards, or publications.

A graph digitization tool can help reconstruct approximate numerical data from these images. However, the extracted values may contain errors, so the user must be able to inspect, correct, and validate the results before using them for forecasting.

## Current Implementation Status

The following functionality is currently implemented:

- Streamlit application page.
- PNG, JPG, and JPEG image upload.
- Display of the uploaded image.
- Display of the uploaded filename.
- Metadata confirmation interface.
- Dynamic time-axis fields.
- Calendar date/time support.
- Elapsed or numeric time support.
- Metadata validation.
- Metadata locking after confirmation.
- Metadata editing after confirmation.
- Resetting metadata when a different image is uploaded.

The following functionality has not yet been implemented:

- Graph detection.
- Chart-region detection.
- Axis detection.
- Plotted-line detection.
- Data-point extraction.
- Multiple-line graph detection.
- Detection of unrelated images without graphs.
- Extracted-point overlays.
- Extracted-data tables.
- Extracted-data editing.
- CSV or JSON downloads from the application.
- Forecasting.
- Rolling forecast validation.
- Forecast reliability reporting.

## Current Supported Input

The current implementation accepts image files with the following extensions:

- PNG
- JPG
- JPEG

The application currently displays any uploaded image with an accepted file extension. It does not yet determine whether the uploaded image contains a supported graph.

The planned graph-input scope is:

- Digital 2D graph images.
- One single-series line graph.
- Clearly labeled, linear axes.
- Up to 1,000 observations.

The following graph types are outside the planned MVP scope:

- Hand-drawn graphs.
- Bar charts.
- Multiple plotted lines.
- 3D graphs.
- Logarithmic axes.
- Mobile and tablet layouts.
- Multiple forecasting models.
- OCR-assisted metadata extraction.

## Current User Workflow

### Stage 1: Upload and Configure

The current implemented workflow is:

1. The user uploads a PNG, JPG, or JPEG image.
2. The application displays the uploaded image.
3. The user enters or confirms graph metadata.
4. The user clicks **Confirm metadata**.
5. The metadata fields become locked.
6. The user can click **Edit metadata** to make corrections.
7. The user can confirm the metadata again.

The current metadata fields are:

- Series name.
- Values-axis unit.
- Values-axis minimum.
- Values-axis maximum.
- Time-axis representation.
- Time-axis frequency.
- Time-axis unit.
- Time-axis start.
- Time-axis end.

### Future Stage 2: Extract and Review

This stage has not yet been implemented.

The planned workflow is for the system to:

1. Analyze the uploaded graph.
2. Detect the chart region and axes.
3. Detect the plotted line.
4. Convert detected pixel coordinates into approximate time-series values.
5. Display the extracted points over the original image.
6. Display the extracted data in an editable table.
7. Report an estimated extraction error.

### Future Stage 3: Configure Forecasting

This stage has not yet been implemented.

The planned workflow is for the user to choose:

- Forecast horizon.
- Error tolerance.

### Future Stage 4: Forecast and Validate

This stage has not yet been implemented.

The planned workflow is for the system to:

1. Use the user-approved data.
2. Apply Holt's linear exponential smoothing.
3. Perform rolling forecast validation.
4. Calculate the mean historical forecast error.
5. Estimate the historical proportion of validation errors exceeding the selected tolerance.

### Future Stage 5: View and Download Results

This stage has not yet been implemented.

The planned results include:

- Historical data and future forecast together.
- Forecast-only visualization.
- Rolling-validation results.
- Forecast reliability information.
- Plain-English forecast interpretation.
- Warnings and limitations.
- Downloadable forecast data.

## Current Metadata Behavior

The current metadata interface supports two time-axis representations.

### Calendar date/time

This representation is intended for graphs whose x-axis uses dates or date-times.

Example:

```text
Time-axis representation: Calendar date/time
Time-axis frequency: 5
Time-axis unit: minutes
Time-axis start: 2024-01-01 00:00:00
Time-axis end: 2024-01-01 00:30:00
