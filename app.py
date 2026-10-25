import datetime

import streamlit as st


st.set_page_config(
    page_title="Time Series Graph Extraction Tool",
    layout="wide"
)


def parse_time_value(value, requires_datetime):
    """
    Parse a time-axis value.

    Sub-hourly and hourly data require a date and time.
    Daily, monthly, and yearly data require a date.
    Custom frequencies accept either format.
    """

    cleaned_value = value.strip()

    if not cleaned_value:
        return None

    try:
        if requires_datetime:
            return datetime.datetime.fromisoformat(cleaned_value)

        return datetime.date.fromisoformat(cleaned_value)

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
    # Reset metadata when a different file is uploaded.
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

    frequency_options = [
        "10 minutes",
        "hour",
        "day",
        "month",
        "year",
        "custom"
    ]

    saved_frequency = saved_metadata.get(
        "frequency",
        ""
    )

    if saved_frequency in frequency_options:
        frequency_selection = saved_frequency
    elif saved_frequency:
        frequency_selection = "custom"
    else:
        frequency_selection = "10 minutes"

    subhourly_or_hourly = frequency_selection in [
        "10 minutes",
        "hour"
    ]

    if not metadata_confirmed:

        with st.form("metadata_form"):

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

            frequency = st.selectbox(
                "Time-axis frequency",
                options=frequency_options,
                index=frequency_options.index(
                    frequency_selection
                )
            )

            custom_frequency = ""

            if frequency == "custom":
                custom_frequency = st.text_input(
                    "Custom time frequency",
                    value=saved_metadata.get(
                        "custom_frequency",
                        ""
                    ),
                    placeholder="For example: every 15 minutes"
                )

            current_frequency_for_fields = frequency

            if frequency == "custom":
                current_frequency_for_fields = "custom"

            requires_datetime = current_frequency_for_fields in [
                "10 minutes",
                "hour"
            ]

            if requires_datetime:
                start_label = "Time-axis start date and time"
                end_label = "Time-axis end date and time"
                time_placeholder = "YYYY-MM-DD HH:MM"
            else:
                start_label = "Time-axis start date"
                end_label = "Time-axis end date"
                time_placeholder = "YYYY-MM-DD"

            col1, col2 = st.columns(2)

            with col1:
                time_start = st.text_input(
                    start_label,
                    value=saved_metadata.get(
                        "time_axis_start",
                        ""
                    ),
                    placeholder=time_placeholder
                )

            with col2:
                time_end = st.text_input(
                    end_label,
                    value=saved_metadata.get(
                        "time_axis_end",
                        ""
                    ),
                    placeholder=time_placeholder
                )

            col3, col4 = st.columns(2)

            with col3:
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

            with col4:
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

            if frequency == "custom" and not custom_frequency.strip():
                validation_errors.append(
                    "Please enter the custom time frequency."
                )

            requires_datetime = frequency in [
                "10 minutes",
                "hour"
            ]

            parsed_start = parse_time_value(
                time_start,
                requires_datetime
            )

            parsed_end = parse_time_value(
                time_end,
                requires_datetime
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

            parsed_value_min = None
            parsed_value_max = None

            if not value_min.strip():
                validation_errors.append(
                    "Please enter the values-axis minimum."
                )
            else:
                try:
                    parsed_value_min = float(value_min)
                except ValueError:
                    validation_errors.append(
                        "Values-axis minimum must be numeric."
                    )

            if not value_max.strip():
                validation_errors.append(
                    "Please enter the values-axis maximum."
                )
            else:
                try:
                    parsed_value_max = float(value_max)
                except ValueError:
                    validation_errors.append(
                        "Values-axis maximum must be numeric."
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

            if (
                parsed_value_min is not None
                and parsed_value_max is not None
                and parsed_value_min >= parsed_value_max
            ):
                validation_errors.append(
                    "The values-axis minimum must be smaller than "
                    "the maximum."
                )

            if validation_errors:
                for error in validation_errors:
                    st.error(error)

            else:
                if frequency == "custom":
                    confirmed_frequency = custom_frequency.strip()
                    stored_custom_frequency = custom_frequency.strip()
                else:
                    confirmed_frequency = frequency
                    stored_custom_frequency = ""

                st.session_state["metadata"] = {
                    "series_name": series_name.strip(),
                    "unit": unit.strip(),
                    "frequency": confirmed_frequency,
                    "custom_frequency": stored_custom_frequency,
                    "time_axis_start": parsed_start.isoformat(),
                    "time_axis_end": parsed_end.isoformat(),
                    "value_axis_min": parsed_value_min,
                    "value_axis_max": parsed_value_max
                }

                st.session_state["metadata_confirmed"] = True

                st.rerun()

    else:
        metadata = st.session_state["metadata"]

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

        st.text_input(
            "Time-axis frequency",
            value=metadata["frequency"],
            disabled=True
        )

        locked_frequency = metadata["frequency"]

        locked_requires_datetime = locked_frequency in [
            "10 minutes",
            "hour"
        ]

        if locked_requires_datetime:
            locked_start_label = "Time-axis start date and time"
            locked_end_label = "Time-axis end date and time"
        else:
            locked_start_label = "Time-axis start date"
            locked_end_label = "Time-axis end date"

        col1, col2 = st.columns(2)

        with col1:
            st.text_input(
                locked_start_label,
                value=metadata["time_axis_start"],
                disabled=True
            )

        with col2:
            st.text_input(
                locked_end_label,
                value=metadata["time_axis_end"],
                disabled=True
            )

        col3, col4 = st.columns(2)

        with col3:
            st.text_input(
                "Values-axis minimum",
                value=str(metadata["value_axis_min"]),
                disabled=True
            )

        with col4:
            st.text_input(
                "Values-axis maximum",
                value=str(metadata["value_axis_max"]),
                disabled=True
            )

        if st.button("Edit metadata"):
            st.session_state["metadata_confirmed"] = False
            st.rerun()
            