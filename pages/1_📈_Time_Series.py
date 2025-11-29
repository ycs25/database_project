import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from statsmodels.tsa.seasonal import seasonal_decompose
# from statsmodels.graphics.tsaplots import plot_acf

from database_retrieve import get_monthly_cases

st.set_page_config(page_title="Time Series", page_icon="📈")

st.title('Time Series Plots')

# -----------------------------------------------------------------------------
# Load Data

# cached data load
@st.cache_data
def load_data():
    df = get_monthly_cases()
    return df

with st.spinner('Loading data...'):
    df = load_data()

data = df.copy()
data['date'] = pd.to_datetime(data['date'])

st.sidebar.success("✅ Data Loaded.")
st.sidebar.header("Time Series Plots")

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
if 'ts_active_regions' not in st.session_state:
    # all by default
    st.session_state.ts_active_regions = all_regions
if 'ts_active_case_column' not in st.session_state:
    # first one by default
    st.session_state.ts_active_case_column = "measles_total"
if 'ts_active_display_name' not in st.session_state:
    st.session_state.ts_active_display_name = "Measles Total"

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
        default=st.session_state.ts_active_regions,
        help="Choose one or more regions to display."
    )
    
    # selection of case type
    selected_display_name_input = st.radio(
        label="Select Case Category",
        options=DISPLAY_CASE_OPTIONS,
        index=DISPLAY_CASE_OPTIONS.index(st.session_state.ts_active_display_name),
        help="Select the type of measles cases to visualize."
    )
    
    submit_button = st.form_submit_button(label='Update Plot')

# Update Session State
if submit_button:
    target_column_input = REVERSE_MAPPING.get(selected_display_name_input)

    if not selected_regions_input:
        st.warning("⚠️ Please select at least one region.")
    else:
        st.session_state.ts_active_regions = selected_regions_input
        st.session_state.ts_active_case_column = target_column_input
        st.session_state.ts_active_display_name = selected_display_name_input
        # st.rerun()


current_regions = st.session_state.ts_active_regions
current_column = st.session_state.ts_active_case_column
current_title = st.session_state.ts_active_display_name

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

st.markdown("---")
#------------------------------------------------------------------------------
# Seasonal Decomposition

# Using same region/case selection as the privous block
st.title("Time Series Decomposition Analysis")

ts_data = df_plot.sum(axis=1)

decomposition = seasonal_decompose(ts_data + 1, model='multiplicative', period=12)
decomposition_fig = decomposition.plot()

decomposition_fig.set_size_inches(10, 8) 
decomposition_fig.tight_layout()

st.subheader("🔬 Case Seasonal Decomposition")
st.pyplot(decomposition_fig)

st.markdown("---")

st.markdown(
    """
    ## 📈 Guide to Interpreting Seasonal Decomposition Graphs

    Seasonal decomposition breaks down the time series into three core components 
    to help understand the underlying drivers of the data.

    | Component | Definition | Key Takeaway |
    | --- | --- | --- |
    | Observed | The original time series data. | Shows the combined effect of trend, seasonality, and noise. |
    | Trend | The long-term, underlying progression of the data. | Shows whether the data is generally increasing, decreasing, or stable over multiple years, ignoring short-term fluctuations. |
    | Seasonal | Recurring fluctuations that repeat over a fixed period (e.g., annually). | Reveals predictable patterns, such as whether cases always peak in a specific month. |
    | Residual | The "leftover" noise or irregular component after removing trend and seasonality. | Represents random noise or unpredictable events (e.g., sudden outbreaks, reporting errors, or policy shocks). Large spikes here indicate anomalies. |

"""
)

# Independent Block with user control version
# st.subheader("Seasonal Decomposition of Measles Cases")

# if 'sd_selected_regions' not in st.session_state:
#     st.session_state.sd_selected_regions = ["African Region"]

# with st.form(key='seasonal_decomposition_form'):
#     sd_selected_regions_input = st.multiselect(
#         label="Select Regions",
#         options=all_regions,
#         default=st.session_state.sd_selected_regions,
#         help="Choose one or more regions to analyze."
#     )

#     submit_sd = st.form_submit_button("Update Chart")

# if submit_sd:
#     if not selected_regions_input:
#         st.warning("⚠️ Please select at least one region.")
#     else:
#         st.session_state.sd_selected_regions = sd_selected_regions_input

# current_sd_regions = st.session_state.sd_selected_regions

# if current_sd_regions:

#     sd_filtered_data = data[data["region_name"].isin(current_sd_regions)]

#     df_sd_plot = sd_filtered_data.groupby(["date"])["measles_total"].sum().reset_index()

#     df_sd_plot.set_index("date", inplace=True)

#     df_sd_plot = df_sd_plot.asfreq('MS').fillna(0)

#     decomposition = seasonal_decompose(df_sd_plot + 1, model='multiplicative', period=12)
#     decomposition_fig = decomposition.plot()

#     decomposition_fig.set_size_inches(10, 8) 
#     decomposition_fig.tight_layout()

#     st.subheader("🔬Case Seasonal Decomposition")
#     st.pyplot(decomposition_fig)
