import streamlit as st


st.set_page_config(
    page_title="Time Series Graph Extraction Tool",
    layout="wide"
)

st.title("Time Series Graph Extraction Tool")

st.write(
    "Upload a digital 2D time-series graph to extract, inspect, "
    "and forecast its data."
)

uploaded_file = st.file_uploader(
    "Upload a digital 2D line graph",
    type=["png", "jpg", "jpeg"]
)

if uploaded_file is not None:
    st.success(f"Uploaded file: {uploaded_file.name}")
    st.image(
        uploaded_file,
        caption="Uploaded graph",
        use_container_width=True
    )
else:
    st.info("Please upload a PNG or JPG graph image to continue.")
    