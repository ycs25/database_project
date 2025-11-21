import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Global Measles Map", page_icon="🌍")

st.title('Global Measles Map')

DATA_PATH = ('cases_month.csv')

# cached data load
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    return df

with st.spinner('Loading data...'):
    df = load_data(DATA_PATH)

data = df.copy() # Deep Copy

st.sidebar.success("✅ Data Loaded.")
st.sidebar.header("Static Global Map")
st.sidebar.markdown(
    """
    Choose **year/month, region, projection method** and **case type** to draw a map.
    """
)

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
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        selected_year = st.selectbox("Year", range(2012, 2026), index=0)
        
    with col2:
        selected_month = st.selectbox("Month", range(1, 13), index=0)

    with col3:
        selected_scope = st.selectbox("Scope", ["World", "Asia", "Europe", "Africa", "North America", "South America"], index=0)

    with col4:
        selected_proj = st.selectbox("Projection", ["Natural Earth", "Mercator", "Equirectangular"], index=0)

    st.markdown("---")
    col_data, col_empty = st.columns([1, 3])
    with col_data:
        selected_disease = st.selectbox("Disease Type", ["Measles", "Rubella"], index=0)
    
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

    # subsetting data
    CONDITIONS = (data["year"] == selected_year) & \
                (data["month"] == selected_month) & \
                (data[target_column].notna())
    
    COLUMNS = ["country", "iso3", target_column]

    filtered_data = data.loc[CONDITIONS, COLUMNS].copy()

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
            "iso3": "ISO-3"
            },
        hover_name = "country",

        custom_data = [target_column, "category"],

        projection = proj_param,
        scope = scope_param,
        
        title = f"Global {selected_disease} Cases by Level ({selected_year}-{selected_month})"
    )

    # hover information
    template = (
        '<b>%{hovertext}</b><br>' + 
        '<br>' +
        f'{selected_disease}: %{{customdata[0]:,}}<br>' +
        'Level: %{customdata[1]}<extra></extra>'
    )

    fig.update_traces(
        hovertemplate=template
    )

    st.plotly_chart(fig)


if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.dataframe(data)