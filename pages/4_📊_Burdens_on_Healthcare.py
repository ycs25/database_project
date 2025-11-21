import streamlit as st
import numpy as np
import pandas as pd
import seaborn as sns
import plotly.express as px

st.set_page_config(page_title="Healthcare Capacity", page_icon="📊")

st.title("Burdens of Measles on Healthcare")

# -----------------------------------------------------------------------------
# Load Data
DATA_PATH = ('cases_year.csv')

# cached data load
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    return df

with st.spinner('Loading data...'):
    df = load_data(DATA_PATH)

data = df.copy() # Deep Copy

st.sidebar.success("✅ Data Loaded.")
st.sidebar.header("Burdens on Healthcare")
st.sidebar.markdown(
    """
    We check the **Median Incidence Rate Per 1 Million Population** and 
    the **Laboratory Confirmed Case Ratio**.
    """
)

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

#------------------------------------------------------------------------------
# Top 20 countries by median measles incidence
target_column = "measles_incidence_rate_per_1000000_total_population"

top20 = data.groupby("country")[target_column].median().sort_values(ascending=False).head(20).index

df_subset = data[data['country'].isin(top20)].copy()

df_subset.rename(columns={target_column: 'measles_per1M'}, inplace=True)

# Boxplot

fig = px.box(
    df_subset, 
    x="measles_per1M", 
    y="country",
    title="<b>Top 20 Countries by Median Measles Incidence</b><br><sup>Hover over points to see outbreak years</sup>",
    
    category_orders={"country": top20}, 
    
    hover_name="country",
    # hover_data=["year", "measles_total", "total_population"],
    custom_data = ["year", "measles_total", "total_population", "measles_per1M"],
    
    points="outliers",
    orientation="h",
    height=800
)

# hover information
template = (
    '<b>%{hovertext}</b><br>' + 
    '<br>' +
    'Year: %{customdata[0]}<br>' +
    f'Total Cases: %{{customdata[1]:,}}<extra></extra><br>' +
    f'Total Population: %{{customdata[2]:,}}<br>' +
    'Rate per 1M: %{customdata[3]}<br>'
)

fig.update_traces(hovertemplate=template)

fig.update_layout(
    xaxis_title="Incidence Rate (per 1,000,000)",
    yaxis_title="",
    template="plotly_white",
    hovermode="closest"
)

st.plotly_chart(fig)

#------------------------------------------------------------------------------
# Bottom 20 Countries By Laboratory Confirmed Case Ratio

df_ratio = data[data['measles_total'] > 0].copy()

df_ratio['lab_confirmed_ratio'] = df_ratio['measles_lab_confirmed'] / df_ratio['measles_total']

bottom20 = df_ratio.groupby("country")['lab_confirmed_ratio'].median().sort_values(ascending=True).head(20).index

df_ratio_plot = df_ratio[df_ratio["country"].isin(bottom20)].copy()

fig2 = px.box(
    df_ratio_plot, 
    x="lab_confirmed_ratio", 
    y="country",
    title="<b>Bottom 20 Countries by Laboratory Confirmed Case Ratio</b><br><sup>Hover over points to check outliers</sup>",
    
    category_orders={"country": bottom20}, 
    
    hover_name="country",
    custom_data = ["year", "measles_total", "total_population", "lab_confirmed_ratio"],
    
    points="all",
    orientation="h",
    height=800
)

template2 = (
    '<b>%{hovertext}</b><br>' + 
    '<br>' +
    'Year: %{customdata[0]}<br>' +
    f'Total Cases: %{{customdata[1]:,}}<extra></extra><br>' +
    f'Total Population: %{{customdata[2]:,}}<br>' +
    f'Laboratory Confirmed Case Ratio: %{{customdata[3]:.2f}}<br>'
)

fig2.update_traces(hovertemplate=template2)

fig2.update_layout(
    xaxis_title="Laboratory Confirmed Case Ratio",
    yaxis_title="",
    template="plotly_white",
    hovermode="closest"
)

st.plotly_chart(fig2)