from pathlib import Path
import json

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt


# =========================================================
# Project paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

GROUND_TRUTH_DIR = PROJECT_ROOT / "test_data" / "ground_truth"
IMAGE_DIR = PROJECT_ROOT / "test_data" / "images"
METADATA_FILE = PROJECT_ROOT / "test_data" / "test_cases_metadata.json"

GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)
IMAGE_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# Clean previous generated outputs
# =========================================================

def clean_generated_directory(directory):
    """
    Delete all existing contents while preserving .gitkeep files.
    """

    for item in directory.iterdir():
        if item.name == ".gitkeep":
            continue

        if item.is_file():
            item.unlink()
        elif item.is_dir():
            for nested_item in item.rglob("*"):
                if nested_item.is_file():
                    nested_item.unlink()

            for nested_directory in sorted(
                [path for path in item.rglob("*") if path.is_dir()],
                reverse=True
            ):
                nested_directory.rmdir()

            item.rmdir()


clean_generated_directory(GROUND_TRUTH_DIR)
clean_generated_directory(IMAGE_DIR)

if METADATA_FILE.exists():
    METADATA_FILE.unlink()


# =========================================================
# General configuration
# =========================================================

RANDOM_SEED = 42
rng = np.random.default_rng(RANDOM_SEED)

metadata = {}


# =========================================================
# Axis-limit helpers
# =========================================================

def calculate_axis_limits(timestamps, values):
    """Calculate explicit chart-axis limits with 5% margins."""

    timestamp_series = pd.Series(timestamps)

    if pd.api.types.is_numeric_dtype(timestamp_series):
        x_min = float(timestamp_series.iloc[0])
        x_max = float(timestamp_series.iloc[-1])
    else:
        x_min = pd.Timestamp(timestamp_series.iloc[0])
        x_max = pd.Timestamp(timestamp_series.iloc[-1])

    y_min = float(np.min(values))
    y_max = float(np.max(values))

    if x_min == x_max:
        if isinstance(x_min, pd.Timestamp):
            x_margin = pd.Timedelta(days=1)
        else:
            x_margin = 1
    else:
        if isinstance(x_min, pd.Timestamp):
            x_margin = pd.Timedelta(0)
        else:
            x_margin = 0

    if y_min == y_max:
        y_margin = 1
    else:
        y_margin = (y_max - y_min) * 0.05

    return (
        x_min - x_margin,
        x_max + x_margin,
        y_min - y_margin,
        y_max + y_margin
    )


def add_endpoint_ticks(axis, timestamps):
    """Ensure the first and last time values are visibly labeled."""

    timestamp_series = pd.Series(timestamps)

    if pd.api.types.is_numeric_dtype(timestamp_series):
        endpoint_ticks = np.array([
            float(timestamp_series.iloc[0]),
            float(timestamp_series.iloc[-1])
        ])
    else:
        endpoint_ticks = mdates.date2num([
            pd.Timestamp(
                timestamp_series.iloc[0]
            ).to_pydatetime(),
            pd.Timestamp(
                timestamp_series.iloc[-1]
            ).to_pydatetime()
        ])

    existing_ticks = np.asarray(
        axis.get_xticks(),
        dtype=float
    )

    all_ticks = np.unique(
        np.concatenate([
            existing_ticks,
            endpoint_ticks
        ])
    )

    axis.set_xticks(all_ticks)


def apply_axis_limits(axis, timestamps, values):
    """Apply the calculated axis limits to a chart."""

    x_min, x_max, y_min, y_max = calculate_axis_limits(
        timestamps,
        values
    )

    axis.set_xlim(x_min, x_max)
    axis.set_ylim(y_min, y_max)


# =========================================================
# Helper functions
# =========================================================

def save_ground_truth(filename, timestamps, values, extra_columns=None):
    """Save the known values used to create a chart."""

    data = {
        "timestamp": pd.to_datetime(timestamps),
        "value": values
    }

    if extra_columns:
        data.update(extra_columns)

    dataframe = pd.DataFrame(data)
    dataframe.to_csv(GROUND_TRUTH_DIR / filename, index=False)


def save_numeric_ground_truth(filename, time_values, values):
    """Save ground truth for an elapsed or numeric-time chart."""

    dataframe = pd.DataFrame({
        "timestamp": time_values,
        "value": values
    })

    dataframe.to_csv(
        GROUND_TRUTH_DIR / filename,
        index=False
    )


def get_calendar_frequency_details(frequency):
    """Return a normalized interval value and time unit."""

    frequency_details = {
        "monthly": (1, "months"),
        "yearly": (1, "years"),
        "hourly": (1, "hours"),
        "10 minutes": (10, "minutes"),
        "daily": (1, "days"),
        "weekly": (1, "weeks")
    }

    return frequency_details.get(
        frequency,
        (None, "custom")
    )


def save_metadata(
    case_id,
    series_name,
    unit,
    frequency,
    timestamps,
    values,
    image_filename,
    ground_truth_filename,
    supported=True,
    warning=None
):
    """Store metadata for one calendar-time test case."""

    frequency_value, time_unit = get_calendar_frequency_details(
        frequency
    )

    (
        time_axis_min,
        time_axis_max,
        value_axis_min,
        value_axis_max
    ) = calculate_axis_limits(
        timestamps,
        values
    )

    metadata[case_id] = {
        "series_name": series_name,
        "unit": unit,
        "frequency": frequency,
        "time_representation": "Calendar date/time",
        "frequency_value": frequency_value,
        "time_unit": time_unit,
        "time_axis_range": [
            pd.Timestamp(time_axis_min).isoformat(),
            pd.Timestamp(time_axis_max).isoformat()
        ],
        "value_axis_range": [
            float(value_axis_min),
            float(value_axis_max)
        ],
        "image_file": image_filename,
        "ground_truth_file": ground_truth_filename,
        "supported_by_mvp": supported,
        "warning": warning
    }


def save_numeric_metadata(
    case_id,
    series_name,
    unit,
    frequency_value,
    time_unit,
    time_values,
    values,
    image_filename,
    ground_truth_filename,
    supported=True,
    warning=None
):
    """Store metadata for an elapsed or numeric-time test case."""

    (
        time_axis_min,
        time_axis_max,
        value_axis_min,
        value_axis_max
    ) = calculate_axis_limits(
        time_values,
        values
    )

    metadata[case_id] = {
        "series_name": series_name,
        "unit": unit,
        "frequency": f"{frequency_value} {time_unit}",
        "time_representation": "Elapsed or numeric time",
        "frequency_value": float(frequency_value),
        "time_unit": time_unit,
        "time_axis_range": [
            float(time_axis_min),
            float(time_axis_max)
        ],
        "value_axis_range": [
            float(value_axis_min),
            float(value_axis_max)
        ],
        "image_file": image_filename,
        "ground_truth_file": ground_truth_filename,
        "supported_by_mvp": supported,
        "warning": warning
    }


def save_chart(
    filename,
    timestamps,
    values,
    title,
    x_label,
    y_label,
    dpi=150,
    figsize=(10, 5),
    marker=None,
    color="royalblue"
):
    """Create and save a digital line chart."""

    figure, axis = plt.subplots(figsize=figsize)

    axis.plot(
        timestamps,
        values,
        color=color,
        linewidth=2,
        marker=marker,
        markersize=4 if marker else None
    )

    axis.set_title(title)
    axis.set_xlabel(x_label)
    axis.set_ylabel(y_label)
    axis.grid(True, alpha=0.3)

    apply_axis_limits(
        axis,
        timestamps,
        values
    )

    add_endpoint_ticks(
        axis,
        timestamps
    )

    figure.autofmt_xdate()
    figure.tight_layout()

    figure.savefig(
        IMAGE_DIR / filename,
        dpi=dpi,
        bbox_inches="tight"
    )

    plt.close(figure)


def save_obscured_chart(
    filename,
    timestamps,
    values,
    title,
    x_label,
    y_label,
    obscured_start_index,
    obscured_end_index
):
    """Create a chart with an intentionally obscured line segment."""

    figure, axis = plt.subplots(figsize=(10, 5))

    axis.plot(
        timestamps,
        values,
        color="royalblue",
        linewidth=2
    )

    axis.axvspan(
        timestamps[obscured_start_index],
        timestamps[obscured_end_index],
        color="white",
        alpha=1.0,
        zorder=3
    )

    axis.set_title(title)
    axis.set_xlabel(x_label)
    axis.set_ylabel(y_label)
    axis.grid(True, alpha=0.3)

    apply_axis_limits(
        axis,
        timestamps,
        values
    )

    add_endpoint_ticks(
        axis,
        timestamps
    )

    figure.autofmt_xdate()
    figure.tight_layout()

    figure.savefig(
        IMAGE_DIR / filename,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(figure)


def save_metadata_file():
    """Save metadata for all generated test cases."""

    with open(METADATA_FILE, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4)


# =========================================================
# 1. Product sales: increasing trend
# =========================================================

timestamps = pd.date_range(
    start="2023-01-01",
    periods=24,
    freq="MS"
)

values = (
    12000
    + np.arange(24) * 550
    + rng.normal(0, 250, 24)
)

save_ground_truth(
    "product_sales_ground_truth.csv",
    timestamps,
    values
)

save_chart(
    "product_sales.png",
    timestamps,
    values,
    title="Monthly Product Sales",
    x_label="Time (month)",
    y_label="Sales (EUR)"
)

save_metadata(
    "product_sales",
    "Product Sales",
    "EUR",
    "monthly",
    timestamps,
    values,
    "product_sales.png",
    "product_sales_ground_truth.csv"
)


# =========================================================
# 2. Manufacturing defect rate: decreasing trend
# =========================================================

timestamps = pd.date_range(
    start="2010-01-01",
    periods=15,
    freq="YS"
)

values = (
    12
    - np.arange(15) * 0.65
    + rng.normal(0, 0.25, 15)
)

save_ground_truth(
    "manufacturing_defect_rate_ground_truth.csv",
    timestamps,
    values
)

save_chart(
    "manufacturing_defect_rate.png",
    timestamps,
    values,
    title="Annual Manufacturing Defect Rate",
    x_label="Time (year)",
    y_label="Defect Rate (percent)"
)

save_metadata(
    "manufacturing_defect_rate",
    "Manufacturing Defect Rate",
    "percent",
    "yearly",
    timestamps,
    values,
    "manufacturing_defect_rate.png",
    "manufacturing_defect_rate_ground_truth.csv"
)


# =========================================================
# 3. Room temperature: stable series
# =========================================================

timestamps = pd.date_range(
    start="2024-01-01",
    periods=48,
    freq="h"
)

values = (
    21.0
    + 0.25 * np.sin(np.arange(48) / 5)
    + rng.normal(0, 0.08, 48)
)

save_ground_truth(
    "room_temperature_ground_truth.csv",
    timestamps,
    values
)

save_chart(
    "room_temperature.png",
    timestamps,
    values,
    title="Office Room Temperature",
    x_label="Time (hour)",
    y_label="Temperature (degrees C)"
)

save_metadata(
    "room_temperature",
    "Office Room Temperature",
    "degrees C",
    "hourly",
    timestamps,
    values,
    "room_temperature.png",
    "room_temperature_ground_truth.csv"
)


# =========================================================
# 4. Machine vibration: noisy series
# =========================================================

timestamps = pd.date_range(
    start="2024-02-01 08:00",
    periods=144,
    freq="10min"
)

values = 4.5 + rng.normal(0, 0.9, 144)

save_ground_truth(
    "machine_vibration_ground_truth.csv",
    timestamps,
    values
)

save_chart(
    "machine_vibration.png",
    timestamps,
    values,
    title="Machine Vibration",
    x_label="Time (10 minutes)",
    y_label="Vibration (mm/s)",
    marker="."
)

save_metadata(
    "machine_vibration",
    "Machine Vibration",
    "mm/s",
    "10 minutes",
    timestamps,
    values,
    "machine_vibration.png",
    "machine_vibration_ground_truth.csv"
)


# =========================================================
# 5. Electricity demand: seasonal series
# =========================================================

timestamps = pd.date_range(
    start="2024-03-01",
    periods=168,
    freq="h"
)

hourly_pattern = 35 * np.sin(
    2 * np.pi * np.arange(168) / 24
)

weekly_pattern = 15 * np.sin(
    2 * np.pi * np.arange(168) / 168
)

values = (
    250
    + hourly_pattern
    + weekly_pattern
    + rng.normal(0, 5, 168)
)

save_ground_truth(
    "electricity_demand_ground_truth.csv",
    timestamps,
    values
)

save_chart(
    "electricity_demand.png",
    timestamps,
    values,
    title="Hourly Electricity Demand",
    x_label="Time (hour)",
    y_label="Demand (kW)"
)

save_metadata(
    "electricity_demand",
    "Electricity Demand",
    "kW",
    "hourly",
    timestamps,
    values,
    "electricity_demand.png",
    "electricity_demand_ground_truth.csv"
)


# =========================================================
# 6. Daily rainfall: obscured data segment
# =========================================================

timestamps = pd.date_range(
    start="2024-04-01",
    periods=60,
    freq="D"
)

values = np.zeros(60)

rainy_days = [3, 8, 15, 16, 27, 36, 42, 51, 57]
values[rainy_days] = rng.uniform(2, 25, len(rainy_days))

save_ground_truth(
    "daily_rainfall_ground_truth.csv",
    timestamps,
    values
)

save_obscured_chart(
    "daily_rainfall_obscured.png",
    timestamps,
    values,
    title="Daily Rainfall with Obscured Segment",
    x_label="Time (day)",
    y_label="Rainfall (mm)",
    obscured_start_index=25,
    obscured_end_index=34
)

save_metadata(
    "daily_rainfall_obscured",
    "Daily Rainfall",
    "mm",
    "daily",
    timestamps,
    values,
    "daily_rainfall_obscured.png",
    "daily_rainfall_ground_truth.csv",
    warning="The chart contains an intentionally obscured segment."
)


# =========================================================
# 7. Annual energy consumption: large values
# =========================================================

timestamps = pd.date_range(
    start="2000-01-01",
    periods=20,
    freq="YS"
)

values = (
    1_000_000
    + 45_000 * np.sin(np.arange(20) / 2)
    + rng.normal(0, 12_000, 20)
)

save_ground_truth(
    "annual_energy_consumption_ground_truth.csv",
    timestamps,
    values
)

save_chart(
    "annual_energy_consumption.png",
    timestamps,
    values,
    title="Annual Energy Consumption",
    x_label="Time (year)",
    y_label="Energy Consumption (MWh)"
)

save_metadata(
    "annual_energy_consumption",
    "Annual Energy Consumption",
    "MWh",
    "yearly",
    timestamps,
    values,
    "annual_energy_consumption.png",
    "annual_energy_consumption_ground_truth.csv"
)


# =========================================================
# 8. Website visits: low-resolution image
# =========================================================

timestamps = pd.date_range(
    start="2024-05-01",
    periods=45,
    freq="D"
)

values = (
    800
    + np.arange(45) * 12
    + 80 * np.sin(np.arange(45) / 3)
    + rng.normal(0, 35, 45)
)

save_ground_truth(
    "website_visits_ground_truth.csv",
    timestamps,
    values
)

save_chart(
    "website_visits_low_resolution.png",
    timestamps,
    values,
    title="Daily Website Visits - Low Resolution",
    x_label="Time (day)",
    y_label="Visits",
    dpi=40,
    figsize=(5, 3)
)

save_metadata(
    "website_visits_low_resolution",
    "Website Visits",
    "visits",
    "daily",
    timestamps,
    values,
    "website_visits_low_resolution.png",
    "website_visits_ground_truth.csv",
    warning="The chart intentionally has low image resolution."
)


# =========================================================
# 9. Unsupported chart: multiple lines
# =========================================================

timestamps = pd.date_range(
    start="2024-06-01",
    periods=45,
    freq="D"
)

machine_a = (
    100
    + np.arange(45) * 1.2
    + rng.normal(0, 5, 45)
)

machine_b = (
    140
    - np.arange(45) * 0.8
    + rng.normal(0, 5, 45)
)

unsupported_ground_truth = pd.DataFrame({
    "timestamp": timestamps,
    "machine_a_energy": machine_a,
    "machine_b_energy": machine_b
})

unsupported_ground_truth.to_csv(
    GROUND_TRUTH_DIR / "unsupported_multiple_lines_ground_truth.csv",
    index=False
)

figure, axis = plt.subplots(figsize=(10, 5))

axis.plot(
    timestamps,
    machine_a,
    color="royalblue",
    linewidth=2,
    label="Machine A"
)

axis.plot(
    timestamps,
    machine_b,
    color="darkorange",
    linewidth=2,
    label="Machine B"
)

axis.set_title("Energy Consumption of Two Machines")
axis.set_xlabel("Time (day)")
axis.set_ylabel("Energy Consumption (kWh)")
axis.legend()
axis.grid(True, alpha=0.3)

all_unsupported_values = np.concatenate([
    machine_a,
    machine_b
])

apply_axis_limits(
    axis,
    timestamps,
    all_unsupported_values
)

figure.autofmt_xdate()
figure.tight_layout()

figure.savefig(
    IMAGE_DIR / "unsupported_multiple_lines.png",
    dpi=150,
    bbox_inches="tight"
)

plt.close(figure)

save_metadata(
    "unsupported_multiple_lines",
    "Two-Machine Energy Consumption",
    "kWh",
    "daily",
    timestamps,
    machine_a,
    "unsupported_multiple_lines.png",
    "unsupported_multiple_lines_ground_truth.csv",
    supported=False,
    warning="The chart contains two plotted lines. The MVP supports only one line."
)


# =========================================================
# 10. Battery discharge: elapsed numeric time
# =========================================================

time_values = np.arange(0, 31, 5)

values = (
    12.6
    - time_values * 0.08
    + rng.normal(0, 0.05, len(time_values))
)

save_numeric_ground_truth(
    "battery_discharge_elapsed_time_ground_truth.csv",
    time_values,
    values
)

save_chart(
    "battery_discharge_elapsed_time.png",
    time_values,
    values,
    title="Battery Discharge Voltage",
    x_label="Time (minutes)",
    y_label="Voltage (V)",
    marker="o"
)

save_numeric_metadata(
    "battery_discharge_elapsed_time",
    "Battery Discharge Voltage",
    "V",
    frequency_value=5,
    time_unit="minutes",
    time_values=time_values,
    values=values,
    image_filename="battery_discharge_elapsed_time.png",
    ground_truth_filename=(
        "battery_discharge_elapsed_time_ground_truth.csv"
    )
)


# =========================================================
# 11. Weekly customer orders
# =========================================================

timestamps = pd.date_range(
    start="2024-01-07",
    periods=52,
    freq="W-SUN"
)

values = (
    850
    + np.arange(52) * 7
    + 45 * np.sin(np.arange(52) / 3.5)
    + rng.normal(0, 22, 52)
)

save_ground_truth(
    "weekly_customer_orders_ground_truth.csv",
    timestamps,
    values
)

save_chart(
    "weekly_customer_orders.png",
    timestamps,
    values,
    title="Weekly Customer Orders",
    x_label="Time (week)",
    y_label="Orders",
    marker="o"
)

save_metadata(
    "weekly_customer_orders",
    "Weekly Customer Orders",
    "orders",
    "weekly",
    timestamps,
    values,
    "weekly_customer_orders.png",
    "weekly_customer_orders_ground_truth.csv"
)


# =========================================================
# Save metadata and finish
# =========================================================

save_metadata_file()

print("Old generated outputs were cleared.")
print("Test chart generation complete.")
print(f"Ground-truth files saved to: {GROUND_TRUTH_DIR}")
print(f"Chart images saved to: {IMAGE_DIR}")
print(f"Metadata saved to: {METADATA_FILE}")
