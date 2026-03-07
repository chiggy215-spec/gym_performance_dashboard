import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Gym Performance Dashboard")

@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/chiggy215-spec/gym_performance_dashboard/main/data/Dashboard%20Exercise%20Data.xlsx"
    df = pd.read_excel(url)
    return df

df = load_data()

st.subheader("Data Preview")
st.dataframe(df)

st.subheader("New Members by Gym")

fig = px.bar(
    df,
    x="Gym",
    y="New Members",
    color="Region"
)

st.plotly_chart(fig)
