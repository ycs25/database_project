import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(page_title="Healthcare Capacity", page_icon="📊")

st.sidebar.header("Burdens on Healthcare")

st.title("Burdens on Healthcare")

# -----------------------------------------------------------------------------
# Load Data
DATA_PATH = ('cases_year.csv')

# cached data load
@st.cache_data
def load_data():
    data = pd.read_csv(DATA_PATH)
    return data

with st.spinner('Loading data...'):
    data = load_data()

st.sidebar.success("✅ Data Loaded.")

# Add region_name column
region_mapping = {
    "AFR": "African Region",
    "AMR": "American Region",
    "SEAR": "South-East Asian Region",
    "EUR": "European Region",
    "EMR": "East Mediterranean Region",
    "WPR": "West Pacific Region"
}
data["region_name"] = data["region"].map(region_mapping)
all_regions = list(region_mapping.values())