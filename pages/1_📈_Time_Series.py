import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.graphics.tsaplots import plot_acf

st.set_page_config(page_title="Time Series", page_icon="📈")

st.sidebar.header("Time Series Plots")

st.title('Time Series Plots')

# -----------------------------------------------------------------------------
# Load Data
DATA_PATH = ('cases_month.csv')

# cached data load
@st.cache_data
def load_data():
    data = pd.read_csv(DATA_PATH)
    return data

with st.spinner('Loading data...'):
    data = load_data()

st.sidebar.success("✅ Data Loaded.")

# Add date column
data["date"] = pd.to_datetime(data[["year", "month"]].assign(DAY=1))
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

# -----------------------------------------------------------------------------
# Initialize Session States
if 'active_regions' not in st.session_state:
    # all by default
    st.session_state.active_regions = all_regions
if 'active_case_column' not in st.session_state:
    # first one by default
    st.session_state.active_case_column = "measles_total"
if 'active_display_name' not in st.session_state:
    st.session_state.active_display_name = "Measles Total"

#------------------------------------------------------------------------------
# Add case names and mapping
RAW_CASE_COLUMNS = [
    "measles_total", 
    "measles_suspect", 
    "measles_clinical", 
    "measles_epi_linked", 
    "measles_lab_confirmed"
]
CASE_NAME_MAPPING = {
    "measles_total": "Measles Total",
    "measles_suspect": "Measles Suspect", 
    "measles_clinical": "Measles Clinical", 
    "measles_epi_linked": "Measles Epi-Linked", 
    "measles_lab_confirmed": "Measles Lab Confirmed"
}
REVERSE_MAPPING = {v: k for k, v in CASE_NAME_MAPPING.items()}
DISPLAY_CASE_OPTIONS = list(CASE_NAME_MAPPING.values())

#------------------------------------------------------------------------------
# Sidebar user input
with st.sidebar.form(key='plot_settings_form'):
    st.header("Plot Configuration")
    
    # multiselect
    selected_regions_input = st.multiselect(
        label="Select Regions",
        options=all_regions,
        default=st.session_state.active_regions,
        help="Choose one or more regions to display."
    )
    
    # selection of case type
    selected_display_name_input = st.radio(
        label="Select Case Category",
        options=DISPLAY_CASE_OPTIONS,
        index=DISPLAY_CASE_OPTIONS.index(st.session_state.active_display_name),
        help="Select the type of measles cases to visualize."
    )
    
    submit_button = st.form_submit_button(label='Update Plot')

# Update Session State
if submit_button:
    target_column_input = REVERSE_MAPPING.get(selected_display_name_input)

    if not selected_regions_input:
        st.warning("⚠️ Please select at least one region.")
    else:
        st.session_state.active_regions = selected_regions_input
        st.session_state.active_case_column = target_column_input
        st.session_state.active_display_name = selected_display_name_input
        st.rerun()


current_regions = st.session_state.active_regions
current_column = st.session_state.active_case_column
current_title = st.session_state.active_display_name

# -----------------------------------------------------------------------------
# Time Series Plot
if current_regions and current_column:

    filtered_data = data[data["region_name"].isin(current_regions)]

    df_indexed_summed = filtered_data.groupby(['date', 'region_name'])[current_column].sum().sort_index()

    df_plot = df_indexed_summed.unstack(level='region_name')

    df_plot.index = pd.to_datetime(df_plot.index)

    fig, ax = plt.subplots(figsize=(10, 6))

    if not df_plot.empty:
        df_plot.plot(
            ax=ax,
            title=f'{current_title} Over Time by Region',
            x_compat=True 
        )

        locator = mdates.YearLocator()
        ax.xaxis.set_major_locator(locator)
        formatter = mdates.DateFormatter('%Y')
        ax.xaxis.set_major_formatter(formatter)

        fig.autofmt_xdate()

        ax.set_ylabel('Cases Count')
        ax.legend(title='Region')
        fig.tight_layout()

        st.subheader(f"📈 {current_title} Time Series Plot")
        st.pyplot(fig)

    else:
        st.info("No data available for the selected criteria.")

