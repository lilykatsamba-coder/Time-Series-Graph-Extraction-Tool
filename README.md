# Time Series Graph Extraction and Forecasting Tool

## Project Overview

This project is a desktop-only web application that extracts approximate time-series data from a digital 2D line graph image and uses the extracted data to generate a forecast.

The tool is designed for situations where the original historical data is unavailable, but a graph image still exists.

The workflow is:

1. Upload a graph image.
2. Confirm or edit the graph metadata.
3. Extract the plotted data.
4. Estimate and display the extraction error.
5. Inspect or edit the extracted data.
6. Download the data or continue to forecasting.
7. Choose the forecast horizon and error tolerance.
8. Generate a forecast.
9. Evaluate the forecasting process using rolling forecast validation.
10. View the forecast, error baseline, reliability information, and warnings.

## Problem Statement

Historical data may become unavailable while visualizations of that data remain accessible in reports, presentations, screenshots, or documents.

This tool reconstructs approximate numerical data from a graph image and makes the reconstructed data available for inspection, download, and forecasting.

## MVP Scope

The MVP is a desktop-only website supporting:

- Digital 2D graphs
- One single-series line graph
- Up to 1,000 measurements
- Clearly labeled linear axes
- One forecasting model
- Rolling forecast validation
- One mean historical forecast error baseline
- User-selected forecast horizon
- User-selected forecast error tolerance
- CSV and JSON data export
- Estimated extraction error reporting
- Plain-English forecast interpretation
- Extraction and forecasting warnings

## Supported Input

The input must be:

- A digital graph image
- A 2D line graph
- A single plotted series
- A graph with labeled axes
- A graph with linear scales
- A graph containing up to 1,000 measurements

The MVP does not support:

- Hand-drawn graphs
- Bar charts
- Multiple plotted lines
- 3D graphs
- Logarithmic axes
- Mobile or tablet layouts
- Multiple forecasting models
- OCR-based metadata extraction

Before extraction, the user can confirm or edit:

- Time-axis range
- Time frequency
- Values-axis range
- Measurement units
- Series name

## User Workflow

### Stage 1: Upload and Configure

1. The user uploads a graph image.
2. The system displays the original image.
3. The user confirms or edits:
   - Time-axis range
   - Time frequency
   - Values-axis range
   - Units
   - Series name

### Stage 2: Extract and Review

1. The system extracts the plotted time-series data.
2. The system estimates the extraction error.
3. The system displays the extracted points over the original graph.
4. The system displays the extracted data in an editable table.
5. The user can:
   - Correct values
   - Download the data
   - Stop after extraction
   - Continue to forecasting

### Stage 3: Configure Forecasting

Before forecasting, the user chooses:

- Forecast horizon
- Error tolerance

The error tolerance defines when a forecast is considered incorrect. For example, a user may define an incorrect forecast as one with an absolute error greater than 10 units or 10%.

### Stage 4: Forecast and Validate

1. The system uses the user-approved data.
2. The system generates a future forecast.
3. The system performs rolling forecast validation.
4. The system calculates:
   - Individual historical forecast errors
   - Mean historical forecast error
   - Estimated historical probability of exceeding the selected error tolerance

### Stage 5: View and Download Results

The system displays:

- Historical data and future forecast together
- Forecast-only view, if available
- Rolling-validation results
- Extraction reliability
- Forecasting reliability
- Plain-English interpretation
- Warnings

The user can download the forecast data.

## Outputs

The tool provides:

- Original uploaded graph image
- Annotated graph showing extracted points
- Extracted historical data
- Editable data table
- Estimated extraction error
- Downloadable extracted data file
- Forecast graph
- Downloadable forecast data file
- Mean historical forecast error baseline
- Estimated historical probability of exceeding the selected error tolerance
- Extraction reliability information
- Forecasting reliability information
- Plain-English forecast interpretation
- Warnings and limitations

## Technical Approach

### Programming Language

The project uses Python as the single primary programming language.

### Website Framework

The user interface is built with Streamlit.

### Image Processing

The project uses:

- OpenCV for chart-region, axis, gridline, and plotted-line detection
- Pillow for image loading and basic preprocessing
- NumPy for numerical pixel and array operations

OCR is not included in the MVP because the user manually confirms the graph metadata.

### Charting

The project uses Plotly for interactive charts, including:

- Extracted data visualization
- Extraction-point overlays
- Historical data visualization
- Forecast visualization
- Rolling-validation results

### Forecasting

The project uses `statsmodels` for forecasting.

Pandas is used for time-series data preparation and NumPy is used for numerical calculations.

## Forecasting Model

The MVP uses:

> Holt's linear exponential smoothing

This model is implemented with `statsmodels` and models the level and trend of the time series.

The forecasting code is designed around a common model interface so that additional models can be added later without changing the user interface, validation process, or download logic.

Possible future models include:

- Seasonal Holt-Winters exponential smoothing
- AutoReg

## Rolling Forecast Validation

Rolling forecast validation evaluates the forecasting process while preserving the time order of the data.

The model repeatedly:

1. Uses earlier historical observations as training data.
2. Predicts a later historical observation.
3. Compares the prediction with the actual value.
4. Moves forward through the historical series.
5. Repeats the process.

Historical actual values are the user-approved data values.

Historical predictions are generated by the model during the validation process. They are used to evaluate the model and do not replace the user-approved data.

## Forecast Error Calculation

For each rolling-validation prediction, the absolute forecast error is:

\[
e_i^{\mathrm{forecast}} =
\left|y_i^{\mathrm{actual}} -
\hat{y}_i^{\mathrm{predicted}}\right|
\]

The mean historical forecast error baseline is:

\[
E_{\mathrm{mean}} =
\frac{1}{n}
\sum_{i=1}^{n}
e_i^{\mathrm{forecast}}
\]

This is technically a mean absolute error calculation, but it is presented in the application as the mean historical forecast error baseline.

## Estimated Historical Probability of Exceeding the Error Tolerance

The user selects an error tolerance before forecasting.

A validation forecast is considered to exceed the tolerance when:

\[
e_i^{\mathrm{forecast}} > T
\]

where \(T\) is the selected error tolerance.

The estimated historical exceedance probability is:

\[
\hat{p} =
\frac{
\text{number of validation errors exceeding } T
}{
\text{total number of validation forecasts}
}
\]

For example:

```text
Error tolerance: 10%
Validation forecasts: 20
Forecasts exceeding tolerance: 3
Estimated historical exceedance probability: 15%
```

This value is an estimate based on historical validation. It is not an exact guarantee about future forecast performance.

## Extraction Error

For test images where the original data is known, the extraction error for an individual value is:

\[
e_i^{\mathrm{extraction}} =
\left|y_i^{\mathrm{true}} -
y_i^{\mathrm{extracted}}\right|
\]

For a real uploaded graph, the original values are usually unknown. Therefore, the tool can only provide an estimated extraction error based on the graph's pixel resolution, calibration, and detected point positions.

The tool distinguishes between:

- **Measured extraction error:** calculated when ground-truth data is available
- **Estimated extraction error:** calculated for user-uploaded graphs without known original data

## Reliability Information

The tool reports two separate types of reliability.

### Extraction Reliability

This describes how confidently the system converted the graph image into numerical data.

It may be based on:

- Pixel resolution
- Axis calibration
- Detected point positions
- Point visibility
- Estimated extraction error

### Forecasting Reliability

This describes how the selected forecasting method performed during historical rolling validation.

It may be based on:

- Mean historical forecast error
- Number of validation forecasts
- Number of errors exceeding the selected tolerance
- Estimated historical exceedance probability

The two reliability concepts are kept separate because inaccurate extraction and inaccurate forecasting are different sources of uncertainty.

## Data Formats

The MVP supports:

- CSV
- JSON

### CSV Historical Data

CSV is intended for simple inspection and editing.

```csv
timestamp,value,extraction_error
2024-01-01,103.5,0.8
2024-01-02,106.2,0.6
2024-01-03,104.8,0.7
```

### CSV Forecast Data

The actual error of a future forecast cannot be calculated until the future actual values become available.

```csv
timestamp,forecast_value
2024-01-04,107.1
2024-01-05,108.3
```

### CSV Validation Data

Historical validation results can include actual values, predicted values, and errors.

```csv
timestamp,actual_value,predicted_value,forecast_error
2024-01-04,106.8,107.1,0.3
2024-01-05,108.7,108.3,0.4
```

### JSON Data

JSON is intended for metadata-rich storage and future extensibility.

```json
{
  "metadata": {
    "series_name": "Sales",
    "unit": "units",
    "frequency": "daily",
    "time_axis_range": [
      "2024-01-01",
      "2024-01-03"
    ],
    "value_axis_range": [
      0,
      200
    ],
    "source_file": "sales_chart.png"
  },
  "observations": [
    {
      "timestamp": "2024-01-01",
      "value": 103.5,
      "extraction_error": 0.8
    },
    {
      "timestamp": "2024-01-02",
      "value": 106.2,
      "extraction_error": 0.6
    }
  ]
}
```

## Forecast Interpretation

The tool provides a plain-English summary of the forecast, such as:

- Whether the forecast shows an increasing or decreasing trend
- Whether the forecast appears stable
- Whether the forecast changes direction
- Whether the historical validation error is relatively large
- Whether the estimated historical exceedance probability is high
- Whether uncertainty increases with the forecast horizon

The interpretation is a summary of calculated results. It is not a guarantee about the future.

## Forecast Horizon

The user chooses the forecast horizon before forecasting.

The horizon is expressed in the time units of the input series, such as:

- Next 7 days
- Next 3 months
- Next 12 observations

The application will define a maximum forecast horizon relative to the amount of historical data available.

Longer forecast horizons generally involve greater uncertainty.

## Warnings and Limitations

The tool may warn the user when:

- The graph image is unclear.
- Axis labels are missing or difficult to read.
- The graph is not supported.
- The extracted values are approximate.
- The estimated extraction error is high.
- Data points may be missing.
- There are too few observations for reliable forecasting.
- The selected forecast horizon is long relative to the available history.
- The selected error tolerance is very small.
- The historical validation sample is small.
- Historical validation does not guarantee future accuracy.
- The graph contains unsupported features.

The tool does not calculate the exact probability that a future forecast will be incorrect. It calculates an estimated historical probability of exceeding a user-selected error tolerance.

## Installation

`[Add installation instructions here.]`

## Usage

`[Add instructions for running and using the application here.]`

## Technology Stack

- Python
- Streamlit
- OpenCV
- Pillow
- NumPy
- Pandas
- Plotly
- statsmodels

## Project Structure

`[Add the repository folder structure here.]`

## Testing Data

`[Describe the sample graph images and ground-truth data used for testing.]`

## Evaluation Results

`[Add extraction accuracy, extraction error, forecasting results, processing time, and other evaluation results here.]`

## Benchmark Comparison

`[Add comparison with open-source extraction or forecasting implementations here, if completed.]`

## Video Demonstration

`[Add the link to the demonstration video here.]`

## Sample Images

`[Describe and link to the sample test images here.]`

## Known Issues

`[Add known bugs and unresolved issues here.]`

## Future Improvements

Possible future improvements include:

- Multiple plotted lines
- Bar chart support
- Hand-drawn graph support
- Mobile and tablet layouts
- Logarithmic-axis support
- Seasonal Holt-Winters forecasting
- AutoReg forecasting
- Additional export formats
- Improved uncertainty estimation
- Agent or LLM-tool integration
- OCR-assisted metadata extraction

## License

`[Add license information here.]`

## Author

`[Add your name and relevant project information here.]`