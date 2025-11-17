import streamlit as st
import numpy as np
import pandas as pd
import matplotlib as plt
import plotly.express as px

# INSTALL "requirements.txt" FIRST
# pip install -r requirements.txt

# TEST APP
# use "streamlit run app.py" in terminal to run

st.title('Measles Cases')

DATA_PATH = ('cases_month.csv')

# cached data load
@st.cache_data
def load_data():
    data = pd.read_csv(DATA_PATH)
    return data


data_load_state = st.text('Loading data...')

data = load_data()

data_load_state.text("Data Loaded.")

if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.dataframe(data)

# plot configure
max_cases = data["measles_total"].max()
offset = 20

# user input year/month

# subsetting data
CONDITIONS = (data["year"] == 2024) & (data["month"] == 12) & (data["measles_total"].notna())
COLUMNS = ["country", "iso3", "measles_total"]

filtered_data = data.loc[CONDITIONS, COLUMNS]

# category for color mapping
bins = [0, 50, 200, 1000, max_cases + 1]
labels = ["0-50", "50-200", "200-1000", "1000+"]
color_map_reds = {
    "0-50": "#F1948A",
    "50-200": "#E74C3C",
    "200-1000": "#C0392B",
    "1000+": "#78281F"
}

filtered_data["measles_category"] = pd.cut(
    filtered_data['measles_total'], 
    bins=bins, 
    labels=labels, 
    right=True,
    include_lowest=True
)

# offsetting small points
filtered_data['visible_measles_size'] = filtered_data['measles_total'] + offset

# measles case map
fig = px.scatter_geo(
    filtered_data,
    locations = "iso3",
    locationmode = "ISO-3",

    size = "visible_measles_size",

    color = "measles_category",
    # color_continuous_scale = "Reds",
    # range_color = [0, 1000],
    color_discrete_map = color_map_reds,
    category_orders = {"measles_category": ["0-50", "50-200", "200-1000", "1000+"]},

    labels = {
        "measles_category": "Measles Level",
        "measles_total": "Measles Cases",
        "iso3": "ISO-3"
        },
    hover_name = "country",

    custom_data = ["measles_total", "measles_category"],
    hover_data = None,

    projection = "natural earth",
    
    title = "Global Measles Cases by Level"
)

# hover information
template = (
    '<b>%{hovertext}</b><br>' + 
    '<br>' +
    'Cases: %{customdata[0]:,}<br>' + 
    'Level: %{customdata[1]}<extra></extra>' 
)

fig.update_traces(
    hovertemplate=template
)

st.plotly_chart(fig)