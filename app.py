import datetime
import os
import tempfile
import pandas as pd
import cv2
import streamlit as st
import plotly.graph_objects as go

from src.extractor import extract_chart_data
from src.forecasting import forecast_time_series
from src.validation import rolling_validate_forecast


st.set_page_config(
    page_title="Time Series Graph Extraction Tool",
    layout="wide"
)


def parse_calendar_value(value, mode):
    """Parse a calendar date or date-time value."""

    value = value.strip()

    if not value:
        return None

    try:
        if mode == "datetime":
            return datetime.datetime.fromisoformat(value)

        if mode == "date":
            return datetime.date.fromisoformat(value)

        try:
            return datetime.datetime.fromisoformat(value)
        except ValueError:
            return datetime.date.fromisoformat(value)

    except ValueError:
        return None


def parse_numeric_value(value):
    """Parse a numeric value."""

    value = value.strip()

    if not value:
        return None

    try:
        return float(value)

    except ValueError:
        return None

def prepare_csv_download(
    observations,
    metadata
):
    """Format extracted observations for CSV download."""

    csv_observations = observations.copy()

    if "timestamp" not in csv_observations.columns:
        return csv_observations.to_csv(
            index=False
        )

    if metadata["time_representation"] == (
        "Calendar date/time"
    ):
        timestamps = pd.to_datetime(
            csv_observations["timestamp"]
        )

        if metadata["time_unit"] in [
            "days",
            "weeks",
            "months",
            "years"
        ]:
            csv_observations["timestamp"] = (
                timestamps.dt.strftime(
                    "%Y-%m-%d"
                )
            )

        else:
            csv_observations["timestamp"] = (
                timestamps.dt.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

    return csv_observations.to_csv(
        index=False
    )

def observations_are_equal(left, right, metadata):
    """Compare observations after normalizing editor type changes."""

    required_columns = ["timestamp", "value"]

    if any(
        column not in left.columns
        or column not in right.columns
        for column in required_columns
    ):
        return False

    left_values = left[required_columns].reset_index(drop=True).copy()
    right_values = right[required_columns].reset_index(drop=True).copy()

    if len(left_values) != len(right_values):
        return False

    if metadata["time_representation"] == "Calendar date/time":
        left_values["timestamp"] = pd.to_datetime(
            left_values["timestamp"], errors="coerce"
        )
        right_values["timestamp"] = pd.to_datetime(
            right_values["timestamp"], errors="coerce"
        )
    else:
        left_values["timestamp"] = pd.to_numeric(
            left_values["timestamp"], errors="coerce"
        )
        right_values["timestamp"] = pd.to_numeric(
            right_values["timestamp"], errors="coerce"
        )

    left_values["value"] = pd.to_numeric(
        left_values["value"], errors="coerce"
    )
    right_values["value"] = pd.to_numeric(
        right_values["value"], errors="coerce"
    )

    return left_values.equals(right_values)


def validate_observations(observations, metadata):
    """Validate observations before accepting them for forecasting."""

    required_columns = ["timestamp", "value"]

    if any(column not in observations.columns for column in required_columns):
        return ["The table must contain timestamp and value columns."]

    values = observations[required_columns].copy()

    if metadata["time_representation"] == "Calendar date/time":
        values["timestamp"] = pd.to_datetime(
            values["timestamp"], errors="coerce"
        )
    else:
        values["timestamp"] = pd.to_numeric(
            values["timestamp"], errors="coerce"
        )

    values["value"] = pd.to_numeric(
        values["value"], errors="coerce"
    )

    validation_errors = []

    if values.empty:
        validation_errors.append("The table must contain at least one observation.")
        return validation_errors

    if values["timestamp"].isna().any():
        validation_errors.append("Every timestamp must contain a valid value.")

    if values["value"].isna().any():
        validation_errors.append("Every observation value must be numeric.")

    if values["timestamp"].duplicated().any():
        validation_errors.append("Timestamps must be unique.")

    if not values["timestamp"].isna().any() and not values["timestamp"].is_monotonic_increasing:
        validation_errors.append("Timestamps must be in increasing order.")

    return validation_errors


def reset_observation_editing_state():
    """Clear the editable-observations workflow state."""

    st.session_state["observations_locked"] = False
    st.session_state["confirmed_observations"] = None
    st.session_state["current_observations"] = None
    st.session_state.pop("observations_editor", None)
    st.session_state["observations_editor_revision"] = (
        st.session_state.get("observations_editor_revision", 0) + 1
    )


def reset_forecasting_state():
    """Clear forecast and validation results."""

    st.session_state["forecast_result"] = None
    st.session_state["validation_result"] = None
    st.session_state["forecast_error"] = None
    st.session_state["validation_error"] = None


def build_forecast_figure(observations, forecast):
    """Build a Plotly figure containing actuals and forecasts."""

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=observations["timestamp"],
            y=observations["value"],
            mode="lines+markers",
            name="Confirmed observations",
        )
    )

    figure.add_trace(
        go.Scatter(
            x=forecast["timestamp"],
            y=forecast["forecast_value"],
            mode="lines+markers",
            name="Forecast",
            line={"dash": "dash"},
        )
    )

    figure.update_layout(
        xaxis_title="Time",
        yaxis_title="Value",
        legend_title="Series",
        hovermode="x unified",
    )

    return figure


def build_validation_figure(predictions):
    """Build a Plotly figure for rolling-validation predictions."""

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=predictions["target_timestamp"],
            y=predictions["actual_value"],
            mode="lines+markers",
            name="Actual historical value",
        )
    )

    figure.add_trace(
        go.Scatter(
            x=predictions["target_timestamp"],
            y=predictions["predicted_value"],
            mode="lines+markers",
            name="Rolling prediction",
        )
    )

    figure.update_layout(
        xaxis_title="Time",
        yaxis_title="Value",
        legend_title="Series",
        hovermode="x unified",
    )

    return figure


st.title("Time Series Graph Extraction Tool")

st.write(
    "Upload a digital 2D time-series graph to extract, inspect, "
    "and forecast its data."
)

uploaded_file = st.file_uploader(
    "Upload a digital 2D line graph",
    type=["png", "jpg", "jpeg"]
)

if uploaded_file is None:
    st.info("Please upload a PNG or JPG graph image to continue.")

else:
    current_file_id = (
        f"{uploaded_file.name}_{uploaded_file.size}"
    )

    previous_file_id = st.session_state.get(
        "uploaded_file_id"
    )

    if previous_file_id != current_file_id:
        st.session_state["uploaded_file_id"] = current_file_id
        st.session_state["metadata"] = {}
        st.session_state["metadata_confirmed"] = False
        st.session_state["extraction"] = None
        reset_observation_editing_state()
        reset_forecasting_state()

    st.success(f"Uploaded file: {uploaded_file.name}")

    st.image(
        uploaded_file,
        caption="Uploaded graph",
        width="stretch"
    )

    st.divider()

    st.subheader("Confirm graph metadata")

    st.write(
        "Confirm or edit the graph metadata before data extraction."
    )

    metadata_confirmed = st.session_state.get(
        "metadata_confirmed",
        False
    )

    saved_metadata = st.session_state.get(
        "metadata",
        {}
    )

    if not metadata_confirmed:

        with st.container(border=True):

            # Series name
            series_name = st.text_input(
                "Series name",
                value=saved_metadata.get(
                    "series_name",
                    ""
                ),
                placeholder="For example: Electricity demand"
            )

            # Values-axis unit
            unit = st.text_input(
                "Values-axis unit",
                value=saved_metadata.get(
                    "unit",
                    ""
                ),
                placeholder="For example: kW, EUR, mm, or degrees C"
            )

            # Values-axis range
            col1, col2 = st.columns(2)

            with col1:
                value_min = st.text_input(
                    "Values-axis minimum",
                    value=str(
                        saved_metadata.get(
                            "value_axis_min",
                            ""
                        )
                    ),
                    placeholder="For example: 0"
                )

            with col2:
                value_max = st.text_input(
                    "Values-axis maximum",
                    value=str(
                        saved_metadata.get(
                            "value_axis_max",
                            ""
                        )
                    ),
                    placeholder="For example: 100"
                )

            # Time-axis representation
            representation_options = [
                "Select a time-axis representation",
                "Calendar date/time",
                "Elapsed or numeric time"
            ]

            saved_representation = saved_metadata.get(
                "time_representation",
                ""
            )

            if saved_representation in representation_options:
                representation_selection = saved_representation
            else:
                representation_selection = (
                    "Select a time-axis representation"
                )

            time_representation = st.selectbox(
                "Time-axis representation",
                options=representation_options,
                index=representation_options.index(
                    representation_selection
                )
            )

            # Time-axis frequency
            frequency_value = st.text_input(
                "Time-axis frequency",
                value=str(
                    saved_metadata.get(
                        "frequency_value",
                        ""
                    )
                ),
                placeholder="For example: 5"
            )

            # Time-axis unit
            time_unit_options = [
                "Select a time unit",
                "seconds",
                "minutes",
                "hours",
                "days",
                "weeks",
                "months",
                "years"
            ]

            saved_time_unit = saved_metadata.get(
                "time_unit",
                ""
            )

            if saved_time_unit in time_unit_options:
                time_unit_selection = saved_time_unit
            else:
                time_unit_selection = "Select a time unit"

            time_unit = st.selectbox(
                "Time-axis unit",
                options=time_unit_options,
                index=time_unit_options.index(
                    time_unit_selection
                )
            )

            # Dynamic time-axis fields
            if time_representation == (
                "Elapsed or numeric time"
            ):
                time_input_mode = "numeric"
                start_label = "Time-axis start"
                end_label = "Time-axis end"
                start_placeholder = "For example: 0"
                end_placeholder = "For example: 30"

            elif time_representation == (
                "Calendar date/time"
            ):
                if time_unit in [
                    "seconds",
                    "minutes",
                    "hours"
                ]:
                    time_input_mode = "datetime"
                    start_label = (
                        "Time-axis start date and time"
                    )
                    end_label = (
                        "Time-axis end date and time"
                    )
                    start_placeholder = (
                        "YYYY-MM-DD HH:MM:SS"
                    )
                    end_placeholder = (
                        "YYYY-MM-DD HH:MM:SS"
                    )

                elif time_unit in [
                    "days",
                    "weeks",
                    "months",
                    "years"
                ]:
                    time_input_mode = "date"
                    start_label = "Time-axis start date"
                    end_label = "Time-axis end date"
                    start_placeholder = "YYYY-MM-DD"
                    end_placeholder = "YYYY-MM-DD"

                else:
                    time_input_mode = "generic"
                    start_label = "Time-axis start"
                    end_label = "Time-axis end"
                    start_placeholder = (
                        "YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"
                    )
                    end_placeholder = (
                        "YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"
                    )

            else:
                time_input_mode = "generic"
                start_label = "Time-axis start"
                end_label = "Time-axis end"
                start_placeholder = (
                    "Select a representation first"
                )
                end_placeholder = (
                    "Select a representation first"
                )

            # Time-axis range
            col1, col2 = st.columns(2)

            with col1:
                time_start = st.text_input(
                    start_label,
                    value=saved_metadata.get(
                        "time_axis_start",
                        ""
                    ),
                    placeholder=start_placeholder
                )

            with col2:
                time_end = st.text_input(
                    end_label,
                    value=saved_metadata.get(
                        "time_axis_end",
                        ""
                    ),
                    placeholder=end_placeholder
                )

            metadata_submitted = st.button(
                "Confirm metadata"
            )

        if metadata_submitted:
            validation_errors = []

            # Basic text validation
            if not series_name.strip():
                validation_errors.append(
                    "Please enter a series name."
                )

            if not unit.strip():
                validation_errors.append(
                    "Please enter the values-axis unit."
                )

            # Values-axis validation
            parsed_value_min = parse_numeric_value(value_min)
            parsed_value_max = parse_numeric_value(value_max)

            if parsed_value_min is None:
                validation_errors.append(
                    "Values-axis minimum must be numeric."
                )

            if parsed_value_max is None:
                validation_errors.append(
                    "Values-axis maximum must be numeric."
                )

            if (
                parsed_value_min is not None
                and parsed_value_max is not None
                and parsed_value_min >= parsed_value_max
            ):
                validation_errors.append(
                    "The values-axis minimum must be smaller "
                    "than the maximum."
                )

            # Time-axis metadata validation
            if time_representation == (
                "Select a time-axis representation"
            ):
                validation_errors.append(
                    "Please select a time-axis representation."
                )

            parsed_frequency = parse_numeric_value(
                frequency_value
            )

            if parsed_frequency is None:
                validation_errors.append(
                    "Time-axis frequency must be numeric."
                )
            elif parsed_frequency <= 0:
                validation_errors.append(
                    "Time-axis frequency must be positive."
                )

            if time_unit == "Select a time unit":
                validation_errors.append(
                    "Please select a time-axis unit."
                )

            # Time range validation
            if time_input_mode == "numeric":
                parsed_start = parse_numeric_value(time_start)
                parsed_end = parse_numeric_value(time_end)

                if parsed_start is None:
                    validation_errors.append(
                        "Time-axis start must be numeric."
                    )

                if parsed_end is None:
                    validation_errors.append(
                        "Time-axis end must be numeric."
                    )

            else:
                parsed_start = parse_calendar_value(
                    time_start,
                    time_input_mode
                )

                parsed_end = parse_calendar_value(
                    time_end,
                    time_input_mode
                )

                if parsed_start is None:
                    validation_errors.append(
                        "The time-axis start has an invalid format."
                    )

                if parsed_end is None:
                    validation_errors.append(
                        "The time-axis end has an invalid format."
                    )

            if (
                parsed_start is not None
                and parsed_end is not None
                and parsed_start >= parsed_end
            ):
                validation_errors.append(
                    "The time-axis start must be earlier "
                    "than the time-axis end."
                )

            if validation_errors:
                for error in validation_errors:
                    st.error(error)

            else:
                confirmed_time_unit = time_unit

                st.session_state["metadata"] = {
                    "series_name": series_name.strip(),
                    "unit": unit.strip(),
                    "value_axis_min": parsed_value_min,
                    "value_axis_max": parsed_value_max,
                    "time_representation": time_representation,
                    "frequency_value": parsed_frequency,
                    "time_unit": confirmed_time_unit,
                    "time_axis_start": (
                        parsed_start.isoformat()
                        if hasattr(
                            parsed_start,
                            "isoformat"
                        )
                        else parsed_start
                    ),
                    "time_axis_end": (
                        parsed_end.isoformat()
                        if hasattr(
                            parsed_end,
                            "isoformat"
                        )
                        else parsed_end
                    )
                }

                st.session_state["metadata_confirmed"] = True
                st.session_state["extraction"] = None
                reset_observation_editing_state()
                reset_forecasting_state()

                st.rerun()

    else:
        metadata = st.session_state["metadata"]

        with st.container(border=True):

            st.text_input(
                "Series name",
                value=metadata["series_name"],
                disabled=True
            )

            st.text_input(
                "Values-axis unit",
                value=metadata["unit"],
                disabled=True
            )

            col1, col2 = st.columns(2)

            with col1:
                st.text_input(
                    "Values-axis minimum",
                    value=str(
                        metadata["value_axis_min"]
                    ),
                    disabled=True
                )

            with col2:
                st.text_input(
                    "Values-axis maximum",
                    value=str(
                        metadata["value_axis_max"]
                    ),
                    disabled=True
                )

            st.text_input(
                "Time-axis representation",
                value=metadata[
                    "time_representation"
                ],
                disabled=True
            )

            st.text_input(
                "Time-axis frequency",
                value=str(
                    metadata["frequency_value"]
                ),
                disabled=True
            )

            st.text_input(
                "Time-axis unit",
                value=metadata["time_unit"],
                disabled=True
            )

            if metadata["time_representation"] == (
                "Elapsed or numeric time"
            ):
                locked_start_label = "Time-axis start"
                locked_end_label = "Time-axis end"

            elif metadata["time_unit"] in [
                "seconds",
                "minutes",
                "hours"
            ]:
                locked_start_label = (
                    "Time-axis start date and time"
                )
                locked_end_label = (
                    "Time-axis end date and time"
                )

            elif metadata["time_unit"] in [
                "days",
                "weeks",
                "months",
                "years"
            ]:
                locked_start_label = (
                    "Time-axis start date"
                )
                locked_end_label = (
                    "Time-axis end date"
                )

            else:
                locked_start_label = "Time-axis start"
                locked_end_label = "Time-axis end"

            col1, col2 = st.columns(2)

            with col1:
                st.text_input(
                    locked_start_label,
                    value=str(
                        metadata["time_axis_start"]
                    ),
                    disabled=True
                )

            with col2:
                st.text_input(
                    locked_end_label,
                    value=str(
                        metadata["time_axis_end"]
                    ),
                    disabled=True
                )

            if st.button("Edit metadata"):
                st.session_state[
                    "metadata_confirmed"
                ] = False
                st.session_state["extraction"] = None
                reset_observation_editing_state()
                reset_forecasting_state()
                st.rerun()
                

metadata_confirmed = st.session_state.get(
    "metadata_confirmed",
    False
)

metadata = st.session_state.get(
    "metadata",
    {}
)

if uploaded_file is not None and metadata_confirmed:
    st.divider()
    st.subheader("Extract data")

    st.write(
        "Run the extraction using the uploaded graph and confirmed metadata."
    )

    if st.button("Extract data"):
        temporary_path = None

        try:
            file_suffix = os.path.splitext(
                uploaded_file.name
            )[1]

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=file_suffix
            ) as temporary_file:
                temporary_file.write(
                    uploaded_file.getvalue()
                )
                temporary_path = temporary_file.name

            extraction_result = extract_chart_data(
                temporary_path,
                metadata
            )

            if extraction_result.success:
                annotated_image_rgb = cv2.cvtColor(
                    extraction_result.annotated_image,
                    cv2.COLOR_BGR2RGB
                )

                st.session_state["extraction"] = {
                    "success": True,
                    "annotated_image": annotated_image_rgb,
                    "observations": (
                        extraction_result.observations
                    ),
                    "warnings": (
                        extraction_result.warnings
                    ),
                    "diagnostics": (
                        extraction_result.diagnostics
                    )
                }
                reset_observation_editing_state()
                reset_forecasting_state()

            else:
                st.session_state["extraction"] = {
                    "success": False,
                    "warnings": (
                        extraction_result.warnings
                    )
                }

        finally:
            if temporary_path is not None:
                os.unlink(temporary_path)

    extraction = st.session_state.get(
        "extraction"
    )

    if extraction is not None:
        if extraction["success"]:
            st.success(
                "Extraction completed successfully."
            )

            st.subheader(
                f"Extraction result: {metadata['series_name']}"
            )

            st.caption(
                "The image below shows the detected line and barriers of the uploaded graph. "
                "You can determine the accuracy of the data extraction through this visual:"
            )

            if extraction["warnings"]:
                for warning in extraction["warnings"]:
                    st.warning(warning)

            st.image(
                extraction["annotated_image"],
                caption=(
                    "Detected line and plot boundaries"
                ),
                width="stretch"
            )

            st.subheader(
                "Extracted observations"
            )

            original_observations = (
                extraction["observations"]
                .drop(
                    columns=["extraction_error"],
                    errors="ignore"
                )
                .reset_index(drop=True)
            )

            observations_locked = st.session_state.get(
                "observations_locked", False
            )

            confirmed_observations = st.session_state.get(
                "confirmed_observations"
            )
            current_observations = st.session_state.get(
                "current_observations"
            )

            if observations_locked and confirmed_observations is not None:
                editor_input = confirmed_observations
            elif not observations_locked and current_observations is not None:
                editor_input = current_observations
            else:
                editor_input = original_observations

            st.write(
                "Review the extracted observations. You can edit the "
                "timestamps or values before accepting the data."
            )

            edited_observations = st.data_editor(
                editor_input,
                width="stretch",
                hide_index=True,
                disabled=observations_locked,
                key=(
                    "observations_editor_"
                    f"{st.session_state.get('observations_editor_revision', 0)}"
                ),
                num_rows="dynamic"
            )

            if not observations_locked:
                st.session_state["current_observations"] = (
                    edited_observations.copy()
                )

                has_edits = not observations_are_equal(
                    edited_observations,
                    original_observations,
                    metadata
                )

                confirmation_label = (
                    "Use edited data" if has_edits
                    else "Use extracted data"
                )

                if st.button(confirmation_label):
                    validation_errors = validate_observations(
                        edited_observations, metadata
                    )

                    if validation_errors:
                        for error in validation_errors:
                            st.error(error)
                    else:
                        st.session_state["confirmed_observations"] = (
                            edited_observations.copy()
                        )
                        st.session_state["observations_locked"] = True
                        reset_forecasting_state()
                        st.rerun()

            else:
                st.success("The observations are confirmed and locked.")

                if st.button("Edit data"):
                    st.session_state["observations_locked"] = False
                    reset_forecasting_state()
                    st.rerun()

            download_observations = (
                st.session_state.get("confirmed_observations")
                if observations_locked
                else edited_observations
            )

            csv_data = prepare_csv_download(
                download_observations,
                metadata
            )

            safe_series_name = "".join(
                character
                if character.isalnum()
                else "_"
                for character in metadata["series_name"]
            ).strip("_") or "extracted_data"

            st.download_button(
                "Download CSV",
                data=csv_data,
                file_name=f"{safe_series_name}.csv",
                mime="text/csv"
            )

            st.caption(
                f"Extracted {len(extraction['observations'])} "
                "frequency-aligned observations."
            )

            if observations_locked:
                st.divider()
                st.subheader("Forecast")
                st.write(
                    "Choose the forecast horizon and error tolerance, "
                    "then run the Holt forecast and historical validation."
                )

                control_col1, control_col2 = st.columns(2)

                with control_col1:
                    forecast_horizon = st.number_input(
                        "Forecast horizon",
                        min_value=1,
                        value=5,
                        step=1,
                        help=(
                            "Number of future frequency-aligned observations "
                            "to forecast."
                        )
                    )

                with control_col2:
                    error_tolerance = st.number_input(
                        "Error tolerance",
                        min_value=0.0,
                        value=1.0,
                        step=0.1,
                        format="%.4f",
                        help=(
                            "Absolute error threshold in the same unit as "
                            "the values-axis data."
                        )
                    )

                if st.button("Forecast"):
                    st.session_state["forecast_result"] = None
                    st.session_state["validation_result"] = None
                    st.session_state["forecast_error"] = None
                    st.session_state["validation_error"] = None

                    confirmed_data = st.session_state[
                        "confirmed_observations"
                    ].copy()

                    try:
                        st.session_state["forecast_result"] = (
                            forecast_time_series(
                                confirmed_data,
                                int(forecast_horizon),
                                metadata,
                            )
                        )
                    except ValueError as error:
                        st.session_state["forecast_error"] = str(error)

                    try:
                        st.session_state["validation_result"] = (
                            rolling_validate_forecast(
                                confirmed_data,
                                int(forecast_horizon),
                                float(error_tolerance),
                                metadata,
                            )
                        )
                    except ValueError as error:
                        st.session_state["validation_error"] = str(error)

                    st.rerun()

                forecast_result = st.session_state.get(
                    "forecast_result"
                )
                validation_result = st.session_state.get(
                    "validation_result"
                )
                forecast_error = st.session_state.get(
                    "forecast_error"
                )
                validation_error = st.session_state.get(
                    "validation_error"
                )

                if forecast_error:
                    st.error(
                        f"Forecast could not be generated: {forecast_error}"
                    )

                if validation_error:
                    st.warning(
                        "Rolling validation could not be completed: "
                        f"{validation_error}"
                    )

                if forecast_result is not None:
                    st.subheader("Forecast results")
                    st.plotly_chart(
                        build_forecast_figure(
                            st.session_state["confirmed_observations"],
                            forecast_result,
                        ),
                        width="stretch",
                    )
                    st.dataframe(
                        forecast_result,
                        width="stretch",
                        hide_index=True,
                    )

                    forecast_csv = prepare_csv_download(
                        forecast_result,
                        metadata,
                    )

                    st.download_button(
                        "Download forecast CSV",
                        data=forecast_csv,
                        file_name=f"{safe_series_name}_forecast.csv",
                        mime="text/csv",
                    )

                if validation_result is not None:
                    st.subheader("Rolling validation")
                    metric_col1, metric_col2, metric_col3 = st.columns(3)

                    with metric_col1:
                        st.metric(
                            "Mean absolute error",
                            f"{validation_result.mean_absolute_error:.4f}",
                        )

                    with metric_col2:
                        st.metric(
                            "Evaluated predictions",
                            validation_result.evaluated_prediction_count,
                        )

                    with metric_col3:
                        st.metric(
                            "Historical exceedance proportion",
                            f"{validation_result.exceedance_proportion:.1%}",
                        )

                    st.caption(
                        "The exceedance proportion is the historical share "
                        "of rolling predictions whose absolute error exceeded "
                        f"the tolerance of {validation_result.tolerance:.4f}. "
                        "It is not an exact probability of future exceedance."
                    )

                    st.plotly_chart(
                        build_validation_figure(
                            validation_result.predictions,
                        ),
                        width="stretch",
                    )

                    with st.expander("View rolling-validation details"):
                        st.dataframe(
                            validation_result.predictions,
                            width="stretch",
                            hide_index=True,
                        )

        else:
            st.error(
                "Extraction could not be completed."
            )

            for warning in extraction["warnings"]:
                st.warning(warning)
