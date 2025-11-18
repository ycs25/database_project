import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Global Measles Map", page_icon="🌍")

st.sidebar.header("Global Spread Animation")

st.title('Animated Global Map')

DATA_PATH = ('cases_month.csv')

# cached data load
@st.cache_data
def load_data():
    data = pd.read_csv(DATA_PATH)
    data['period'] = data['year'].astype(str) + "-" + data['month'].astype(str).str.zfill(2)
    return data

data_load_state = st.text('Loading data...')

data = load_data()

data_load_state.text("Data Loaded.")

# plot configure
offset = 20

# category for color mapping
color_map_reds = {
    "0-50": "#F1948A",
    "50-200": "#E74C3C",
    "200-1000": "#C0392B",
    "1000+": "#78281F"
}

# user input
with st.form("query_form"):
    st.write("Configuration")
    
    col1, col2, col3 = st.columns(3)

    with col1:
        selected_scope = st.selectbox("Scope", ["World", "Asia", "Europe", "Africa", "North America", "South America"], index=0)

    with col2:
        selected_proj = st.selectbox("Projection", ["Natural Earth", "Mercator", "Equirectangular"], index=0)

    with col3:
        selected_disease = st.selectbox("Disease Type", ["Measles", "Rubella"], index=0)

    st.markdown("---")

    min_year = int(data['year'].min())
    max_year = int(data['year'].max())

    selected_years = st.slider(
        "Select Animation Year Range", 
        min_value=min_year, 
        max_value=max_year, 
        value=(min_year, max_year)
    )
    
    submitted = st.form_submit_button("Submit")

if submitted:
    # only runs after submit
    # target column
    if selected_disease == "Measles":
        target_column = "measles_total"
        display_name = "Measles Cases"
    else:
        target_column = "rubella_total"
        display_name = "Rubella Cases"

    start_year, end_year = selected_years

    # subsetting data
    CONDITIONS = (data["year"] >= start_year) & \
                (data["year"] <= end_year) & \
                (data[target_column].notna())
    
    COLUMNS = ["country", "iso3", "period", target_column]

    filtered_data = data.loc[CONDITIONS, COLUMNS].copy()

    filtered_data = filtered_data.sort_values("period")

    # upper bound for levels
    current_max = filtered_data[target_column].max()

    if pd.isna(current_max): # incase of NaN
        current_max = 0

    # generate binned category
    upper_bound = max(1001, current_max + 1)
    
    bins = [0, 50, 200, 1000, upper_bound]
    labels = ["0-50", "50-200", "200-1000", "1000+"]

    filtered_data["category"] = pd.cut(
        filtered_data[target_column], 
        bins=bins, 
        labels=labels, 
        right=True,
        include_lowest=True
    )

    # offsetting small points
    filtered_data['visible_size'] = filtered_data[target_column] + offset

    # set scope and projection to lower cases
    scope_param = selected_scope.lower()
    proj_param = selected_proj.lower()

    # map
    fig = px.scatter_geo(
        filtered_data,
        locations = "iso3",
        locationmode = "ISO-3",

        # animation configure
        animation_frame = "period", # play by time
        animation_group = "iso3", # transit by country

        size = "visible_size",
        size_max = 50,

        color = "category",
        # color_continuous_scale = "Reds",
        # range_color = [0, 1000],
        color_discrete_map = color_map_reds,
        category_orders = {"category": ["0-50", "50-200", "200-1000", "1000+"]},

        labels = {
            "category": "Level",
            target_column: display_name,
            "iso3": "ISO-3",
            "period": "Time"
            },
        hover_name = "country",

        custom_data = [target_column, "category"],

        projection = proj_param,
        scope = scope_param,
        
        title = f"Global {selected_disease} Cases by Level ({start_year}-{end_year})"
    )

    # hover information
    template = (
        '<b>%{hovertext}</b><br>' + 
        '<br>' +
        f'{selected_disease}: %{{customdata[0]:,}}<br>' +
        'Level: %{customdata[1]}<extra></extra>'
    )

    fig.update_traces(hovertemplate=template)
    fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})

    st.plotly_chart(fig)


if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.dataframe(data)