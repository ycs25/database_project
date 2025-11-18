import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Time Series", page_icon="📈")

st.sidebar.header("Time Series Plots")

st.title('Time Series Plots')

DATA_PATH = ('cases_month.csv')

# cached data load
@st.cache_data
def load_data():
    data = pd.read_csv(DATA_PATH)
    return data

data_load_state = st.text('Loading data...')

data = load_data()

data_load_state.text("Data Loaded.")