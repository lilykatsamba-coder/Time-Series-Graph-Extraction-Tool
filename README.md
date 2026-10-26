# Time-Series Graph Extraction and Forecasting Tool

A desktop Streamlit application that reconstructs approximate time-series data from a digital graph image and forecasts future values from the extracted series.

The tool is intended for situations where the original numerical dataset is unavailable but a plotted visualization still exists.

## Project overview

This project is a desktop-only Streamlit web application that extracts time-series data from a digital 2D line graph.
The application combines:

1. **Computer vision** to detect a plotted line and the plot region in an uploaded graph image.
2. **User-confirmed metadata** to map image pixels to timestamps and values.
3. **An editable observation table** so the user can inspect and correct extracted data.
4. **Holt linear exponential smoothing** to forecast future observations.
5. **Expanding-window rolling validation** to evaluate historical forecast performance.

The application is deliberately scoped as a focused MVP. It prioritizes transparency and user correction over attempting to support every chart type.

## Current capabilities

The current version supports:

- Digital 2D line-graph images in PNG, JPG, or JPEG format.
- One continuous, clearly colored time-series line.
- Clearly colored lines such as blue, red, green, or orange.
- Numeric or elapsed time axes.
- Calendar date and date-time axes.
- User-confirmed axis ranges, units, series name, and sampling frequency.
- Frequency-aligned extracted observations.
- Editable extracted timestamps and values.
- CSV download of confirmed observations.
- Holt linear exponential-smoothing forecasts.
- User-selected forecast horizon.
- User-selected absolute error tolerance.
- Forecast visualization with Plotly.
- Rolling historical validation using the same forecast horizon.
- Mean absolute error reporting.
- Historical tolerance-exceedance reporting.
- Forecast CSV download.
- Warnings for unrecognizable graphs, multiple plotted lines, and relatively low-resolution images.

## Supported input and current limitations

The current version is designed for a **digital 2D graph containing one continuous, clearly colored time-series line**.

The following limitations apply:

- Multiple plotted lines are detected and rejected because the current version supports one series only.
- Black, gray, or very low-saturation plotted lines are not reliably supported.
- The chart should contain a continuous line. Obscured, fragmented, or heavily degraded lines may be rejected or produce less accurate values.
- Low-resolution images may be processed, but the application warns the user to confirm the axis metadata carefully.
- The application expects a digital chart image, not a photograph of a paper chart.
- Bar charts, pie charts, scatter plots, 3D plots, and hand-drawn charts are outside the current scope.
- OCR is not included. The user confirms the axis metadata manually.
- Extracted values are approximate because they are reconstructed from pixels.
- Forecast quality depends on the behavior of the series, the amount of historical data, and the selected forecast horizon.
- The application does not claim that the historical exceedance proportion is an exact probability of future error.

## User workflow

### 1. Upload a graph

Upload a PNG, JPG, or JPEG graph image.

Uploading only displays the image. Graph recognition starts when the user runs extraction after confirming metadata.

### 2. Confirm graph metadata

The user confirms or edits:

- Series name.
- Values-axis unit.
- Values-axis minimum and maximum.
- Time-axis representation.
- Time-axis frequency.
- Time-axis unit.
- Time-axis start and end.

This metadata is required to convert pixel positions into meaningful observations.

### 3. Extract and inspect data

The computer-vision pipeline detects the plotted line and plot boundaries, then reconstructs observations at the confirmed frequency.

The application displays:

- The annotated graph.
- Detected line points and plot boundaries.
- The extracted observation table.
- Any extraction warnings.

### 4. Edit and confirm observations

The user can edit timestamps and values. The observations must pass validation before they can be confirmed for forecasting.

The application checks that:

- Required timestamp and value columns exist.
- Timestamps are valid.
- Values are numeric.
- Timestamps are unique.
- Timestamps are in increasing order.

### 5. Configure and run forecasting

After the observations are confirmed, the user selects:

- **Forecast horizon:** the number of future frequency-aligned observations to generate.
- **Error tolerance:** an absolute threshold in the same units as the series values.

The user then runs the forecast.

### 6. Review and download results

The application displays:

- Confirmed historical observations.
- Future forecast values.
- A Plotly forecast chart.
- Forecast values in a table.
- A forecast CSV download.
- Rolling-validation metrics and prediction details.

## Computer-vision extraction

The extraction pipeline uses classical computer vision with OpenCV:

1. Load the image.
2. Convert the image into color and grayscale representations.
3. Segment strongly colored pixels to identify the plotted line.
4. Use connected-component analysis to identify usable line regions.
5. Detect dominant color groups to reject multiple colored series.
6. Detect long horizontal and vertical chart structures to estimate plot boundaries.
7. Extract pixel coordinates from the detected line.
8. Convert pixel coordinates into timestamps and values using confirmed metadata.
9. Resample the reconstructed curve to the requested frequency.

This is a traditional image-processing approach. It does not use OCR, neural networks, or a deep-learning model.

## Forecasting

The current forecasting model is **Holt's linear exponential smoothing**, implemented with `statsmodels`.

Holt's method is suitable for an ordered numeric series with a changing level and trend. It does not require seasonal configuration in the current MVP.

The forecasting backend validates:

- Required input columns.
- Timestamp validity.
- Numeric finite values.
- Timestamp ordering and uniqueness.
- Positive forecast horizons.
- Numeric and supported time frequencies.

## Rolling validation

The application uses expanding-window rolling-origin validation.

For each rolling origin:

1. Fit Holt's model using observations available before the origin.
2. Forecast the selected horizon.
3. Compare the forecast with the next historical observations.
4. Expand the training window by one observation.
5. Repeat while a complete historical forecast window remains.

For each prediction, the absolute error is:

$$
 e_i = |y_i - \hat{y}_i|
$$

The reported mean absolute error is:

$$
\mathrm{MAE} = \frac{1}{N}\sum_{i=1}^{N}|y_i - \hat{y}_i|
$$

The historical tolerance-exceedance proportion is:

$$
\hat{p}_{\mathrm{exceed}} =
\frac{1}{N}\sum_{i=1}^{N}
\mathbf{1}(|y_i - \hat{y}_i| > \tau)
$$

where \(\tau\) is the user-selected absolute error tolerance.

This value is an observed historical proportion, not an exact probability of future exceedance. The tolerance uses the same units as the series values. For example, a tolerance of `1` means that a prediction is considered within tolerance only when its absolute error is no greater than one value unit.

## Outputs

### Confirmed observation CSV

Contains the user-approved reconstructed series:

```csv
timestamp,value
2024-01-01,123.4
2024-02-01,127.8
```

### Forecast CSV

Contains future forecast values:

```csv
timestamp,forecast_value
2025-01-01,245.1
2025-02-01,249.7
```

The application currently provides CSV downloads. JSON export is reserved for future development.

## Technical approach

### Language and framework

- **Python** as the primary language.
- **Streamlit** for the desktop web interface.

### Image processing and data handling

- **OpenCV** for image processing, color segmentation, connected components, morphological operations, line detection, and plot-boundary detection.
- **Pillow** for image support where needed.
- **NumPy** for numeric calculations.
- **pandas** for observation tables, validation, and time-series preparation.

### Visualization and forecasting

- **Plotly** for extracted-data, forecast, and validation charts.
- **statsmodels** for Holt linear exponential smoothing.

## Project structure

```text
project/
├── .gitignore
├── README.md
├── requirements.txt
├── app.py
├── src/
│   ├── calibration.py
│   ├── evaluation.py
│   ├── extraction.py
│   ├── extractor.py
│   ├── forecasting.py
│   ├── line_extraction.py
│   ├── plot_detection.py
│   └── validation.py
├── tests/
│   ├── test_calibration.py
│   ├── test_evaluation.py
│   ├── test_extraction.py
│   ├── test_extractor.py
│   ├── test_forecasting.py
│   ├── test_forecasting_validation.py
│   ├── test_line_extraction.py
│   └── test_plot_detection.py
├── test_data/
│   ├── images/
│   └── test_cases_metadata.json
└── scripts/
    └── generate_test_charts.py
```

The exact contents may evolve as the project grows.

## Installation and execution

Create a virtual environment from the project root:

```powershell
python -m venv .venv
```

Activate it in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the application:

```powershell
python -m streamlit run app.py
```

The application opens in a browser, normally at:

```text
http://localhost:8501
```

## Testing

Run the complete automated test suite from the repository root:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

The tests cover:

- Pixel-to-value calibration.
- Numeric and calendar time conversion.
- Extraction result structure and warnings.
- Plot-boundary detection.
- Line extraction.
- Extraction evaluation.
- Holt forecasting.
- Calendar-aware forecasting.
- Forecast horizon validation.
- Rolling validation.
- Error-tolerance exceedance calculations.

The missing-image tests intentionally cause OpenCV to print a file-loading warning. This is expected test behavior.

## Test data

The project uses reproducible synthetic digital charts as ground-truth test data. These charts allow the extracted pixel data to be compared with known source values.

The test set includes representative cases such as:

- Increasing series.
- Decreasing series.
- Stable series.
- Noisy series.
- Seasonal-looking series.
- Different time frequencies.
- Different axis ranges.
- Low-resolution charts.
- Obscured or difficult charts.
- Unsupported multiple-line charts.

The test data is intended for reproducibility and regression testing rather than as a claim that the extractor supports every chart image.

## Design decisions

### User-confirmed metadata instead of OCR

The MVP requires the user to confirm axis ranges, units, frequency, and time representation. This avoids adding OCR complexity and makes the calibration assumptions visible.

### Editable observations before forecasting

Image extraction is approximate. Requiring the user to inspect and confirm the observation table prevents unreviewed pixel estimates from being sent directly into forecasting.

### One-series scope

A single continuous line keeps the extraction, editing, forecasting, and validation workflow understandable and demonstrable. Multiple plotted lines are explicitly rejected rather than silently mixing or selecting one series.

### Separate extraction and forecasting stages

The extracted historical data is visible independently from the forecast. This makes it possible to evaluate whether an issue came from image reconstruction or from the forecasting model.

## Future scope

The following features were considered but are outside the current version:

### Broader chart support

- Multiple same-color plotted lines.
- Multiple-series extraction with legend association.
- Bar charts.
- Scatter plots.
- Area charts.
- Hand-drawn charts.
- Photographs of charts.
- 3D charts.

### Better image understanding

- OCR for automatic axis labels, units, and ranges.
- Automatic detection of chart type.
- More robust line detection for black, gray, faint, overlapping, or heavily fragmented lines.
- Improved quality scoring for blur, occlusion, and resolution.
- Confidence maps and per-point extraction reliability.

### Forecasting improvements

- Seasonal Holt-Winters models.
- AutoReg and other model candidates.
- Automatic model selection.
- Baseline-model comparisons.
- Additional error metrics such as normalized MAE, RMSE, and percentage-based metrics.
- Prediction intervals and uncertainty bands.
- Automatic forecast-horizon recommendations.
- Plain-English forecast interpretation and warnings.

### Data and interface improvements

- JSON export containing metadata and observations.
- Combined historical, forecast, and validation exports.
- Mobile-responsive layout.
- Batch processing of several images.
- More interactive correction of extracted points.
- Reusable project sessions and saved metadata.

## Known interpretation notes

- A low absolute tolerance can produce a high exceedance proportion when the series values are large. Tolerance should be selected in the units of the data.
- A five-step forecast is more difficult to validate than a one-step forecast.
- Rolling validation windows can overlap, so individual predictions are not independent observations.
- Forecasting results should be interpreted together with the chart, MAE, selected horizon, tolerance, and the quality of the confirmed historical data.

## License and authorship

No separate open-source license is currently specified. Add a license before distributing the project outside its intended evaluation context.
