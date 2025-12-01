import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from database_retrieve import get_monthly_cases

st.set_page_config(page_title="Seasonal Trends", page_icon="🌙")

st.title('Seasonal Trends Analysis')

# ------------------------------------
# Load Data
@st.cache_data
def load_data():
    df = get_monthly_cases()
    return df

with st.spinner('Loading data...'):
    df = load_data()

data = df.copy()
data['date'] = pd.to_datetime(data['date'])
data['month'] = data['date'].dt.month
data['year'] = data['date'].dt.year
data['month_name'] = data['date'].dt.strftime('%B')

st.sidebar.success("✅ Data Loaded.")
st.sidebar.header("Seasonal Trends")

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

# Initialize Session States
if 'seasonal_regions' not in st.session_state:
    st.session_state.seasonal_regions = all_regions
if 'seasonal_case_column' not in st.session_state:
    st.session_state.seasonal_case_column = "measles_total"
if 'seasonal_display_name' not in st.session_state:
    st.session_state.seasonal_display_name = "Measles Total"

# Case names and mapping
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

# Sidebar user input
with st.sidebar.form(key='seasonal_settings_form'):
    st.header("Plot Configuration")
    
    selected_regions_input = st.multiselect(
        label="Select Regions",
        options=all_regions,
        default=st.session_state.seasonal_regions,
        help="Choose one or more regions to display."
    )
    
    selected_display_name_input = st.radio(
        label="Select Case Category",
        options=DISPLAY_CASE_OPTIONS,
        index=DISPLAY_CASE_OPTIONS.index(st.session_state.seasonal_display_name),
        help="Select the type of measles cases to visualize."
    )
    
    submit_button = st.form_submit_button(label='Update Plot')

# Update Session State
if submit_button:
    target_column_input = REVERSE_MAPPING.get(selected_display_name_input)

    if not selected_regions_input:
        st.warning("⚠️ Please select at least one region.")
    else:
        st.session_state.seasonal_regions = selected_regions_input
        st.session_state.seasonal_case_column = target_column_input
        st.session_state.seasonal_display_name = selected_display_name_input

current_regions = st.session_state.seasonal_regions
current_column = st.session_state.seasonal_case_column
current_title = st.session_state.seasonal_display_name

# ------------------------------------
# Seasonal Heatmap by Month
if current_regions and current_column:
    st.subheader(f"🔥 Seasonal Heatmap: {current_title} by Month and Year")
    
    filtered_data = data[data["region_name"].isin(current_regions)]
    
    # Aggregate by month and year
    seasonal_data = filtered_data.groupby(['year', 'month'])[current_column].sum().reset_index()
    seasonal_pivot = seasonal_data.pivot(index='month', columns='year', values=current_column)
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(14, 6))
    sns.heatmap(seasonal_pivot, annot=False, fmt='.0f', cmap='YlOrRd', ax=ax, cbar_kws={'label': 'Cases Count'})
    ax.set_xlabel('Year')
    ax.set_ylabel('Month')
    ax.set_yticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], rotation=0)
    
    st.pyplot(fig)

# ------------------------------------
# Average Monthly Pattern
if current_regions and current_column:
    st.subheader(f"📊 Average Monthly Pattern: {current_title}")
    
    filtered_data = data[data["region_name"].isin(current_regions)]
    
    # Calculate average cases per month across all years
    monthly_avg = filtered_data.groupby('month')[current_column].mean().reset_index()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    ax.bar(range(1, 13), monthly_avg[current_column].values, color='steelblue', edgecolor='black')
    ax.set_xlabel('Month')
    ax.set_ylabel('Average Cases Count')
    ax.set_title(f'Average {current_title} by Month (Across All Years)')
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(months)
    ax.grid(axis='y', alpha=0.3)
    
    st.pyplot(fig)

# ------------------------------------
# Monthly Box Plot (Distribution across years)
if current_regions and current_column:
    st.subheader(f"📦 Monthly Distribution: {current_title}")
    
    filtered_data = data[data["region_name"].isin(current_regions)]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Prepare data for box plot
    box_data = [filtered_data[filtered_data['month'] == i][current_column].values for i in range(1, 13)]
    
    bp = ax.boxplot(box_data, labels=months, patch_artist=True)
    
    # Color the boxes
    for patch in bp['boxes']:
        patch.set_facecolor('lightblue')
    
    ax.set_xlabel('Month')
    ax.set_ylabel('Cases Count')
    ax.set_title(f'Distribution of {current_title} by Month (Box Plot)')
    ax.grid(axis='y', alpha=0.3)
    
    st.pyplot(fig)

# ------------------------------------
# Regional Comparison - Seasonal Pattern
if current_regions and current_column:
    st.subheader(f"🌍 Regional Seasonal Patterns: {current_title}")
    
    filtered_data = data[data["region_name"].isin(current_regions)]
    
    # Calculate average for each region and month
    regional_seasonal = filtered_data.groupby(['region_name', 'month'])[current_column].mean().reset_index()
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    for region in current_regions:
        region_data = regional_seasonal[regional_seasonal['region_name'] == region]
        ax.plot(region_data['month'], region_data[current_column], marker='o', label=region, linewidth=2)
    
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    ax.set_xlabel('Month')
    ax.set_ylabel('Average Cases Count')
    ax.set_title(f'Regional Comparison: {current_title} Seasonal Pattern')
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(months)
    ax.legend(title='Region')
    ax.grid(True, alpha=0.3)
    
    st.pyplot(fig)

# ------------------------------------
# Statistics Table
if current_regions and current_column:
    st.subheader(f"📈 Seasonal Statistics: {current_title}")
    
    filtered_data = data[data["region_name"].isin(current_regions)]
    
    # Calculate statistics per month
    stats_by_month = filtered_data.groupby('month')[current_column].agg([
        ('Mean', 'mean'),
        ('Median', 'median'),
        ('Std Dev', 'std'),
        ('Min', 'min'),
        ('Max', 'max'),
        ('Count', 'count')
    ]).round(2)
    
    months = ['January', 'February', 'March', 'April', 'May', 'June', 
              'July', 'August', 'September', 'October', 'November', 'December']
    stats_by_month.index = months
    
    st.dataframe(stats_by_month, use_container_width=True)

# ------------------------------------
# Peak and Trough Information
if current_regions and current_column:
    st.subheader("📍 Peak and Trough Months")
    
    filtered_data = data[data["region_name"].isin(current_regions)]
    monthly_avg = filtered_data.groupby('month')[current_column].mean()
    
    peak_month = monthly_avg.idxmax()
    trough_month = monthly_avg.idxmin()
    
    months = ['January', 'February', 'March', 'April', 'May', 'June', 
              'July', 'August', 'September', 'October', 'November', 'December']
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="🔴 Peak Month", value=months[peak_month-1], delta=f"{monthly_avg[peak_month]:.0f} avg cases")
    with col2:
        st.metric(label="🔵 Trough Month", value=months[trough_month-1], delta=f"{monthly_avg[trough_month]:.0f} avg cases")


