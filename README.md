# Time Series Graph Extraction and Forecasting Tool

## Project overview

This project is a desktop-only Streamlit web application that extracts time-series data from a digital 2D line graph.

The application is intended for situations where the original numerical dataset is unavailable but a graph image remains available. The user uploads a graph, confirms its metadata, and receives frequency-aligned observations that can be inspected and downloaded as CSV.

Forecasting is planned for a later implementation stage and is not yet part of the current application workflow.

## Current implementation status

The following functionality is currently implemented:

- Streamlit web application.
- PNG, JPG, and JPEG image upload.
- Uploaded-image preview.
- Manual metadata confirmation.
- Calendar date/time axes.
- Elapsed or numeric time axes.
- Supported time units:
  - seconds
  - minutes
  - hours
  - days
  - weeks
  - months
  - years
- Automatic plotted-line detection using OpenCV.
- Plot-boundary detection.
- Pixel-to-time-series calibration.
- Frequency-aligned observation generation.
- Annotated-image display showing the detected line and plot boundaries.
- Extracted-observation table.
- Application-controlled CSV download with formatted timestamps.
- Streamlit dataframe CSV download remains available as a secondary option.
- Clear extraction warnings and failure messages.
- Metadata editing and extraction-state reset.

## Supported input

The current MVP supports:

- Digital 2D line graphs.
- One plotted data series.
- Clearly visible linear axes.
- Calendar date/time axes.
- Elapsed or numeric time axes.
- PNG, JPG, and JPEG images.

The current MVP does not support:

- Hand-drawn graphs.
- Bar charts.
- Multiple plotted lines.
- 3D graphs.
- Logarithmic axes.
- OCR-based automatic metadata detection.
- Mobile or tablet-specific layouts.
- Multiple forecasting models.
- Forecasting and rolling validation in the Streamlit workflow.

The user confirms the graph metadata manually because OCR is intentionally excluded from the current MVP.

## Current user workflow

1. Launch the Streamlit application.
2. Upload a supported graph image.
3. Confirm the series name, value unit, value-axis range, time-axis representation, frequency, time unit, and time-axis range.
4. Review the locked metadata.
5. Select **Extract data**.
6. Review the annotated graph and frequency-aligned observations.
7. Download the observations as CSV.
8. Edit the metadata or upload another graph if needed.

The confirmed series name is used to label the extraction result. The uploaded graph image is preserved unchanged, including its original title.

## Frequency-aligned observations

The extractor initially detects the plotted line at pixel resolution. Those pixel-level samples are used internally to reconstruct the curve but are not presented as the final dataset.

The reconstructed curve is resampled at the frequency confirmed by the user. For example, a monthly graph produces observations such as:

```text
2023-01-01 00:00:00
2023-02-01 00:00:00
2023-03-01 00:00:00
```

This prevents the application from presenting artificial timestamps generated from individual image pixels.

### Calendar-aware frequencies

Calendar-month and calendar-year frequencies use calendar-aware offsets rather than fixed durations. A monthly series advances from January 1 to February 1 to March 1, regardless of whether the previous month had 28, 29, 30, or 31 days.

Weekly frequencies use fixed seven-day intervals. Therefore, four weeks means a fixed 28-day interval and is not equivalent to one calendar month.

## CSV download behavior

The extracted table provides two CSV download options:

- **Streamlit dataframe download icon:** Exports the table using Streamlit's built-in dataframe behavior. This may represent calendar timestamps in full ISO format, for example `2023-05-21T00:00:00.000`.
- **Application-controlled Download CSV button:** Formats timestamps for external use and is the recommended option.

The application-controlled CSV export uses:

- `YYYY-MM-DD` for date-based calendar frequencies such as days, weeks, months, and years.
- `YYYY-MM-DD HH:MM:SS` for frequencies involving hours, minutes, or seconds.
- Numeric values for elapsed or numeric time axes.

The user-facing CSV contains:

```csv
timestamp,value
2023-01-01,12076.18
2023-02-01,12248.53
```

The internal extraction error field is not displayed or included in the user-facing table because it is not informative during normal extraction. It remains available internally for future diagnostics and evaluation work.

## Technical approach

The implementation uses Python as the primary language.

### Main libraries

- **Streamlit** for the desktop web application.
- **OpenCV** for image processing, line detection, and plot-boundary detection.
- **Pillow** for image loading and basic preprocessing.
- **NumPy** for numerical pixel and interpolation operations.
- **pandas** for time-series preparation, resampling, and tables.
- **Plotly** for planned interactive result visualizations.
- **statsmodels** for planned forecasting functionality.
- **matplotlib** only for generating reproducible synthetic test charts.

## Project structure

```text
project/
├── .gitignore
├── README.md
├── requirements.txt
├── app.py
├── scripts/
│   ├── generate_test_charts.py
│   ├── benchmark_extraction.py
│   ├── create_extraction_debug_outputs.py
│   └── diagnose_calibration.py
├── test_data/
│   ├── ground_truth/
│   ├── images/
│   └── test_cases_metadata.json
├── src/
│   ├── calibration.py
│   ├── evaluation.py
│   ├── extraction.py
│   ├── extractor.py
│   ├── line_extraction.py
│   └── plot_detection.py
└── tests/
    ├── test_calibration.py
    ├── test_evaluation.py
    ├── test_extraction.py
    ├── test_extractor.py
    ├── test_line_extraction.py
    └── test_plot_detection.py
```

## Installation and execution

Create and activate a local virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the application through Streamlit:

```powershell
python -m streamlit run app.py
```

The application should not be launched by running `python app.py` directly because Streamlit supplies the application execution context.

## Testing

Run the automated tests from the repository root:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

The current extraction test suite contains 26 tests, including explicit coverage for weekly frequency extraction.

The test data can be regenerated with:

```powershell
python scripts/generate_test_charts.py
```

The generator creates 11 reproducible synthetic chart cases, corresponding ground-truth CSV files, and metadata.

The generated cases cover:

- Increasing monthly data.
- Decreasing yearly data.
- Hourly temperature data.
- Noisy machine-vibration data.
- Hourly electricity demand.
- Obscured daily rainfall data.
- Yearly energy consumption.
- Low-resolution daily website visits.
- Elapsed-time battery discharge data.
- Unsupported multiple-line input.
- Weekly customer orders.

## Extraction benchmark

The benchmark evaluates the frequency-aligned observations returned to the user, rather than the internal pixel-level samples.

The normalized mean absolute error is calculated relative to each ground-truth value range.

Current results are:

| Test case | Normalized mean error |
|---|---:|
| Product sales | 0.1343% |
| Manufacturing defect rate | 0.1197% |
| Room temperature | 0.5866% |
| Machine vibration | 16.1582% |
| Electricity demand | 1.4145% |
| Daily rainfall, obscured | 3.9525% |
| Annual energy consumption | 0.3018% |
| Website visits, low resolution | 1.1888% |
| Battery discharge, elapsed time | 0.0788% |
| Weekly customer orders | 0.2236% |

The benchmark now evaluates the same frequency-aligned data that appears in the application table and CSV output. For example, the product-sales case is evaluated at 24 monthly observations, while the weekly customer-orders case is evaluated at 52 weekly observations.

The machine-vibration case remains the main documented limitation. Its noisy, rapidly changing curve is more difficult to recover accurately from raster pixels. The obscured daily-rainfall case also has higher error because part of the plotted line is intentionally hidden.

The results demonstrate strong extraction performance for the supported synthetic cases while preserving the limitations of difficult or degraded input images honestly.

## Forecasting roadmap

Forecasting is planned but not yet connected to the current Streamlit workflow.

The planned MVP forecasting implementation includes:

- Holt's linear exponential smoothing using `statsmodels`.
- A model interface that can later support seasonal Holt-Winters and AutoReg.
- Rolling forecast validation that preserves time order.
- Mean historical absolute forecast error.
- User-selected forecast horizon.
- User-selected error tolerance.
- Estimated historical proportion of validation errors exceeding the tolerance.
- Forecast and validation downloads.

The exceedance result will be presented as an estimated historical proportion, not as a guarantee of future forecast performance.
