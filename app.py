import datetime

import streamlit as st


st.set_page_config(
    page_title="Time Series Graph Extraction Tool",
    layout="wide"
)


def parse_calendar_value(value, mode):
    """Parse a calendar date or date-time value."""

    cleaned_value = value.strip()

    if not cleaned_value:
        return None

    try:
        if mode == "datetime":
            return datetime.datetime.fromisoformat(cleaned_value)

        if mode == "date":
            return datetime.date.fromisoformat(cleaned_value)

        try:
            return datetime.datetime.fromisoformat(cleaned_value)
        except ValueError:
            return datetime.date.fromisoformat(cleaned_value)

    except ValueError:
        return None


def parse_numeric_value(value):
    """Parse a numeric elapsed-time value."""

    cleaned_value = value.strip()

    if not cleaned_value:
        return None

    try:
        return float(cleaned_value)

    except ValueError:
        return None


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

    st.success(f"Uploaded file: {uploaded_file.name}")

    st.image(
        uploaded_file,
        caption="Uploaded graph",
        use_container_width=True
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

        # Series name and values-axis information
        series_name = st.text_input(
            "Series name",
            value=saved_metadata.get(
                "series_name",
                ""
            ),
            placeholder="For example: Electricity demand"
        )

        unit = st.text_input(
            "Values-axis unit",
            value=saved_metadata.get(
                "unit",
                ""
            ),
            placeholder="For example: kW, EUR, mm, or degrees C"
        )

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

        st.divider()

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
            "months",
            "years",
            "custom"
        ]

        saved_time_unit = saved_metadata.get(
            "time_unit",
            ""
        )

        if saved_time_unit in time_unit_options:
            time_unit_selection = saved_time_unit
        elif saved_time_unit:
            time_unit_selection = "custom"
        else:
            time_unit_selection = "Select a time unit"

        time_unit = st.selectbox(
            "Time-axis unit",
            options=time_unit_options,
            index=time_unit_options.index(
                time_unit_selection
            )
        )

        custom_time_unit = ""

        if time_unit == "custom":
            custom_time_unit = st.text_input(
                "Custom time-axis unit",
                value=saved_metadata.get(
                    "custom_time_unit",
                    ""
                ),
                placeholder="For example: weeks"
            )

        # Dynamic time-axis fields
        if time_representation == "Elapsed or numeric time":
            time_input_mode = "numeric"
            start_label = "Time-axis start"
            end_label = "Time-axis end"
            start_placeholder = "For example: 0"
            end_placeholder = "For example: 30"

        elif time_representation == "Calendar date/time":

            if time_unit in ["seconds", "minutes", "hours"]:
                time_input_mode = "datetime"
                start_label = "Time-axis start date and time"
                end_label = "Time-axis end date and time"
                start_placeholder = "YYYY-MM-DD HH:MM:SS"
                end_placeholder = "YYYY-MM-DD HH:MM:SS"

            elif time_unit in ["days", "months", "years"]:
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
            start_placeholder = "Select a representation first"
            end_placeholder = "Select a representation first"

        with st.form("metadata_form"):

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

            metadata_submitted = st.form_submit_button(
                "Confirm metadata"
            )

        if metadata_submitted:
            validation_errors = []

            if not series_name.strip():
                validation_errors.append(
                    "Please enter a series name."
                )

            if not unit.strip():
                validation_errors.append(
                    "Please enter the values-axis unit."
                )

            parsed_value_min = None
            parsed_value_max = None

            if not value_min.strip():
                validation_errors.append(
                    "Please enter the values-axis minimum."
                )
            else:
                parsed_value_min = parse_numeric_value(value_min)

                if parsed_value_min is None:
                    validation_errors.append(
                        "Values-axis minimum must be numeric."
                    )

            if not value_max.strip():
                validation_errors.append(
                    "Please enter the values-axis maximum."
                )
            else:
                parsed_value_max = parse_numeric_value(value_max)

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

            if (
                time_representation
                == "Select a time-axis representation"
            ):
                validation_errors.append(
                    "Please select a time-axis representation."
                )

            parsed_frequency = None

            if not frequency_value.strip():
                validation_errors.append(
                    "Please enter the time-axis frequency."
                )
            else:
                parsed_frequency = parse_numeric_value(
                    frequency_value
                )

                if (
                    parsed_frequency is None
                    or parsed_frequency <= 0
                ):
                    validation_errors.append(
                        "Time-axis frequency must be a positive number."
                    )

            if time_unit == "Select a time unit":
                validation_errors.append(
                    "Please select a time-axis unit."
                )

            if time_unit == "custom" and not custom_time_unit.strip():
                validation_errors.append(
                    "Please enter the custom time-axis unit."
                )

            if time_input_mode == "numeric":
                parsed_start = parse_numeric_value(time_start)
                parsed_end = parse_numeric_value(time_end)

                if not time_start.strip():
                    validation_errors.append(
                        "Please enter the time-axis start."
                    )
                elif parsed_start is None:
                    validation_errors.append(
                        "Time-axis start must be numeric."
                    )

                if not time_end.strip():
                    validation_errors.append(
                        "Please enter the time-axis end."
                    )
                elif parsed_end is None:
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

                if not time_start.strip():
                    validation_errors.append(
                        "Please enter the time-axis start."
                    )
                elif parsed_start is None:
                    validation_errors.append(
                        "The time-axis start has an invalid format."
                    )

                if not time_end.strip():
                    validation_errors.append(
                        "Please enter the time-axis end."
                    )
                elif parsed_end is None:
                    validation_errors.append(
                        "The time-axis end has an invalid format."
                    )

            if (
                parsed_start is not None
                and parsed_end is not None
                and parsed_start >= parsed_end
            ):
                validation_errors.append(
                    "The time-axis start must be earlier than "
                    "the time-axis end."
                )

            if validation_errors:
                for error in validation_errors:
                    st.error(error)

            else:
                if time_unit == "custom":
                    confirmed_time_unit = custom_time_unit.strip()
                    stored_custom_time_unit = (
                        custom_time_unit.strip()
                    )
                else:
                    confirmed_time_unit = time_unit
                    stored_custom_time_unit = ""

                st.session_state["metadata"] = {
                    "series_name": series_name.strip(),
                    "unit": unit.strip(),
                    "value_axis_min": parsed_value_min,
                    "value_axis_max": parsed_value_max,
                    "time_representation": time_representation,
                    "frequency_value": parsed_frequency,
                    "time_unit": confirmed_time_unit,
                    "custom_time_unit": stored_custom_time_unit,
                    "time_axis_start": (
                        parsed_start.isoformat()
                        if hasattr(parsed_start, "isoformat")
                        else parsed_start
                    ),
                    "time_axis_end": (
                        parsed_end.isoformat()
                        if hasattr(parsed_end, "isoformat")
                        else parsed_end
                    )
                }

                st.session_state["metadata_confirmed"] = True

                st.rerun()

    else:
        metadata = st.session_state["metadata"]

        # Locked metadata display
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
                value=str(metadata["value_axis_min"]),
                disabled=True
            )

        with col2:
            st.text_input(
                "Values-axis maximum",
                value=str(metadata["value_axis_max"]),
                disabled=True
            )

        st.text_input(
            "Time-axis representation",
            value=metadata["time_representation"],
            disabled=True
        )

        st.text_input(
            "Time-axis frequency",
            value=str(metadata["frequency_value"]),
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
            locked_start_label = "Time-axis start date and time"
            locked_end_label = "Time-axis end date and time"

        elif metadata["time_unit"] in [
            "days",
            "months",
            "years"
        ]:
            locked_start_label = "Time-axis start date"
            locked_end_label = "Time-axis end date"

        else:
            locked_start_label = "Time-axis start"
            locked_end_label = "Time-axis end"

        col1, col2 = st.columns(2)

        with col1:
            st.text_input(
                locked_start_label,
                value=str(metadata["time_axis_start"]),
                disabled=True
            )

        with col2:
            st.text_input(
                locked_end_label,
                value=str(metadata["time_axis_end"]),
                disabled=True
            )

        if st.button("Edit metadata"):
            st.session_state["metadata_confirmed"] = False
            st.rerun()
            