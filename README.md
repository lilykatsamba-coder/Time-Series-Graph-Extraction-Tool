# Time Series Graph Extraction and Forecasting Tool

## Project Overview

This project is a desktop web application that extracts approximate time-series data from a digital 2D line graph image and uses the extracted data to generate a forecast.

The tool is designed for situations where the original historical data is unavailable, but a graph image still exists.

The workflow is:

1. Upload a graph image.
2. Confirm or edit the graph metadata.
3. Extract the plotted data.
4. Inspect or edit the extracted data.
5. Download the data or continue to forecasting.
6. Generate a forecast.
7. Evaluate the forecasting process using rolling forecast validation.
8. View the forecast, historical error baseline, reliability information, and warnings.

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
- One documented mean historical forecast error baseline
- CSV and JSON data export

## Supported Input

The input must be:

- A digital graph image
- A 2D line graph
- A single plotted series
- A graph with labeled axes
- A graph with linear scales
- A graph containing up to 1,000 measurements

Before extraction, the user can confirm or edit:

- Time-axis range
- Time frequency
- Values-axis range
- Measurement units
- Series name

## User Workflow

1. The user uploads a graph image.
2. The system displays the image and requests graph metadata.
3. The user confirms or edits the metadata.
4. The system extracts the plotted time-series data.
5. The user reviews and edits the extracted data if necessary.
6. The user downloads the data or continues to forecasting.
7. The system generates a forecast using one forecasting model.
8. The system performs rolling forecast validation on historical data.
9. The system displays the forecast graph, forecast data, error baseline, reliability information, and warnings.

## Outputs

The tool provides:

- Extracted historical data
- Editable data table
- Downloadable extracted data file
- Forecast graph
- Downloadable forecast data file
- Mean historical forecast error baseline
- Extraction reliability information
- Forecasting reliability information
- Plain-English forecast interpretation
- Warnings and limitations

## Data Formats

The MVP supports:

- CSV
- JSON

The extracted data contains timestamps and values. Metadata such as the series name, units, frequency, and extraction information may also be included.

## Forecasting Method

The tool uses one forecasting model:

`[Document the selected forecasting model here.]`

The model is evaluated using rolling forecast validation.

## Rolling Forecast Validation

Rolling forecast validation evaluates the forecasting process while preserving the time order of the data.

The model repeatedly:

1. Uses earlier historical observations as training data.
2. Predicts a later historical observation.
3. Compares the prediction with the actual value.
4. Moves forward through the historical series.
5. Repeats the process.

## Mean Historical Error Baseline

The tool calculates one mean historical forecast error baseline.

`[Add the exact formula and explanation here.]`

This value describes the average error observed during historical validation. It is not an exact probability that a future forecast will be incorrect.

## Reliability Information

The tool reports two separate types of reliability:

### Extraction reliability

This describes how confidently the system converted the graph image into numerical data.

### Forecasting reliability

This describes how the selected forecasting method performed during historical rolling validation.

The two reliability concepts are kept separate because inaccurate extraction and inaccurate forecasting are different sources of uncertainty.

## Forecast Interpretation

The tool provides a plain-English summary of the forecast, such as:

- Whether the forecast shows an increasing or decreasing trend
- Whether the forecast appears stable
- Whether uncertainty increases over the forecast horizon
- Whether the historical validation error is relatively large

The interpretation is a summary of the calculated results and is not a guarantee about the future.

## Warnings and Limitations

The tool may warn the user when:

- The graph image is unclear.
- Axis labels are missing or difficult to read.
- The graph is not supported.
- The extracted values are approximate.
- Data points may be missing.
- There are too few observations for reliable forecasting.
- The selected forecast horizon is long relative to the available history.
- Historical validation does not guarantee future accuracy.
- The graph contains unsupported features.

## Installation

`[Add installation instructions here.]`

## Usage

`[Add instructions for running and using the application here.]`

## Technology Stack

`[Add programming language, frontend framework, backend framework, libraries, and tools here.]`

## Project Structure

`[Add the repository folder structure here.]`

## Testing Data

`[Describe the sample graph images and ground-truth data used for testing.]`

## Evaluation Results

`[Add extraction accuracy, forecasting results, processing time, and other evaluation results here.]`

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
- Multiple forecasting models
- Additional export formats
- Improved uncertainty estimation
- Agent or LLM-tool integration

## License

`[Add license information here.]`

## Author

`[Add your name and relevant project information here.]`
