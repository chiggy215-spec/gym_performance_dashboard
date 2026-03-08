import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# ------------------------------
# PAGE CONFIG
# ------------------------------
st.set_page_config(page_title="Gym Performance Dashboard", layout="wide")
st.title("Gym Performance Dashboard")
st.write("Tracking New Gym Memberships and PT Sales Summer Goals")
# ------------------------------
# AUTO REFRESH
# ------------------------------
# Refresh once every 24 hours (in milliseconds)
count = st_autorefresh(interval=24*60*60*1000, key="dailyrefresh")

# ------------------------------
# LOAD DATA
# ------------------------------
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/chiggy215-spec/gym_performance_dashboard/main/data/Dashboard%20Exercise%20Data.xlsx"
    df = pd.read_excel(url)
    df.columns = df.columns.str.lower()
    df["start_dt"] = pd.to_datetime(df["start_dt"])
    return df

df = load_data()

# ------------------------------
# FILTER NEW MEMBERS
# ------------------------------
df_new = df[df["cust_type"] == "NEW"].copy()

current_year = df_new["start_dt"].dt.year.max()
prior_year = current_year - 1

# ------------------------------
# DETERMINE DYNAMIC CUTOFF DATE
# ------------------------------
latest_current_date = df_new[df_new["start_dt"].dt.year == current_year]["start_dt"].max()

cutoff_month = latest_current_date.month
cutoff_day = latest_current_date.day

# ------------------------------
# SUMMER DATE MASK (6/1 → dynamic cutoff)
# ------------------------------
summer_period_mask = (
    (df_new["start_dt"].dt.month >= 6) &
    (
        (df_new["start_dt"].dt.month < cutoff_month) |
        (
            (df_new["start_dt"].dt.month == cutoff_month) &
            (df_new["start_dt"].dt.day <= cutoff_day)
        )
    )
)

# ------------------------------
# TREND DATA (ALL DATES)
# ------------------------------
df_new_trend = df_new.groupby("start_dt").size().reset_index(name="count")

# ------------------------------
# DYNAMIC TIME FRAME
# ------------------------------
df_new_summer_current = df_new[
    (df_new["start_dt"].dt.year == current_year) &
    summer_period_mask
]

df_new_summer_prior = df_new[
    (df_new["start_dt"].dt.year == prior_year) &
    summer_period_mask
]

# ------------------------------
# CALCULATED FIELDS FUNCTION
# ------------------------------
def calc_summary(df_current, df_prior, group_field):

    curr = df_current.groupby(group_field).size().reset_index(name="current")
    prior = df_prior.groupby(group_field).size().reset_index(name="prior")

    merged = pd.merge(prior, curr, on=group_field, how="outer").fillna(0)

    merged["prior"] = merged["prior"].astype(int)
    merged["current"] = merged["current"].astype(int)

    # Target = 10% above prior year
    merged["target"] = merged["prior"] * 1.10

    # Color logic for charts
    def color_logic(row):

        target = row["target"]
        yellow_threshold = target * 0.9

        if row["current"] >= target:
            return "green"
        elif row["current"] >= yellow_threshold:
            return "yellow"
        else:
            return "red"

    merged["color"] = merged.apply(color_logic, axis=1)
    return merged


# ------------------------------
# SUMMARY TABLES
# ------------------------------
gym_summary = calc_summary(df_new_summer_current, df_new_summer_prior, "store_nbr")
district_summary = calc_summary(df_new_summer_current, df_new_summer_prior, "district")
region_summary = calc_summary(df_new_summer_current, df_new_summer_prior, "region")

# ------------------------------
# TOP KPI TILES
# ------------------------------
st.header("Top Metrics (6/1-8/31)")
col1, col2, col3 = st.columns(3)
col1.metric("Current Year New Members", int(df_new_summer_current.shape[0]))
col2.metric("Target New Members Through Date", int(df_new_summer_prior.shape[0]*1.10))
col3.metric("Prior Year New Members Through Date", int(df_new_summer_prior.shape[0]))

# ------------------------------
# TOP PERFORMERS LEADERBOARDS
# ------------------------------
st.subheader("Top Performing Units (Leaderboards)")

col1, col2, col3 = st.columns(3)


def build_leaderboard(df, group_field, display_name):

    leaderboard = df.copy()

    leaderboard["performance_pct"] = leaderboard["current"] / leaderboard["target"]

    leaderboard = leaderboard[leaderboard["current"] >= leaderboard["target"]]

    leaderboard = leaderboard.sort_values("performance_pct", ascending=False)

    leaderboard = leaderboard[[group_field, "prior", "current", "target", "performance_pct"]]

    leaderboard = leaderboard.rename(columns={
        group_field: display_name,
        "prior": "Prior Year",
        "current": "Current Year",
        "target": "Target",
        "performance_pct": "Performance %"
    })

    leaderboard["Performance %"] = (leaderboard["Performance %"] * 100).round(1).astype(str) + "%"

    return leaderboard


gym_leaderboard = build_leaderboard(gym_summary, "store_nbr", "Gym")
district_leaderboard = build_leaderboard(district_summary, "district", "District")
region_leaderboard = build_leaderboard(region_summary, "region", "Region")


with col1:
    st.metric("Gyms Exceeding Target", gym_leaderboard.shape[0])
    st.dataframe(gym_leaderboard, use_container_width=True, hide_index=True)

with col2:
    st.metric("Districts Exceeding Target", district_leaderboard.shape[0])
    st.dataframe(district_leaderboard, use_container_width=True, hide_index=True)

with col3:
    st.metric("Regions Exceeding Target", region_leaderboard.shape[0])
    st.dataframe(region_leaderboard, use_container_width=True, hide_index=True)

# ------------------------------
# CLUSTERED BAR PLOTS
# ------------------------------
def clustered_bar_plot(summary_df, group_field, title):

    # Force categorical axis
    summary_df[group_field] = summary_df[group_field].astype(str)

    fig = go.Figure()

    # Prior Year
    fig.add_trace(go.Bar(
        x=summary_df[group_field],
        y=summary_df["prior"],
        name="Prior Year",
        marker_color="grey"
    ))

    # Current Year (colored by performance)
    fig.add_trace(go.Bar(
        x=summary_df[group_field],
        y=summary_df["current"],
        name="Current Year",
        marker_color=summary_df["color"]
    ))

    fig.update_layout(
        title=title,
        barmode="group",
        plot_bgcolor="#1e1e1e",
        paper_bgcolor="#1e1e1e",
        font_color="white",
        xaxis_title=group_field,
        yaxis_title="New Members"
    )

    # Critical fix: treat axis as categorical
    fig.update_xaxes(type="category")

    return fig
st.subheader("YoY New Members vs Target")

st.markdown("""
<div style="display: flex; gap: 20px; margin-bottom: 10px;">
    <div style="display: flex; align-items: center; gap: 5px;">
        <div style="width: 20px; height: 20px; background-color: green;"></div>
        <span>Exceeding Target</span>
    </div>
    <div style="display: flex; align-items: center; gap: 5px;">
        <div style="width: 20px; height: 20px; background-color: yellow; border: 1px solid #ccc;"></div>
        <span>Within 10% of Target</span>
    </div>
    <div style="display: flex; align-items: center; gap: 5px;">
        <div style="width: 20px; height: 20px; background-color: red;"></div>
        <span>More than 10% Below Target</span>
    </div>
</div>
""", unsafe_allow_html=True)
# Create two columns for Region and District
col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(
        clustered_bar_plot(region_summary, "region", "Region YoY New Members vs Target"),
        width='stretch'
    )

with col2:
    st.plotly_chart(
        clustered_bar_plot(district_summary, "district", "District YoY New Members vs Target"),
        width='stretch'
    )

# Full-width Gym plot below
st.plotly_chart(
    clustered_bar_plot(gym_summary, "store_nbr", "Gym YoY New Members vs Target"),
    width='stretch'
)
# ------------------------------
# TREND OF NEW MEMBERS OVER TIME
# ------------------------------
st.header("New Members YoY")

def new_members_yoy(df):

    df["start_dt"] = pd.to_datetime(df["start_dt"])

    current_year = df["start_dt"].dt.year.max()
    prior_year = current_year - 1

    # Filter to NEW members and summer months
    df_summer = df[
        (df["cust_type"] == "NEW") &
        (df["start_dt"].dt.month >= 6) &
        (df["start_dt"].dt.month <= 8) &
        (df["start_dt"].dt.year.isin([current_year, prior_year]))
    ].copy()

    # Normalize both years onto same seasonal axis
    df_summer["season_date"] = df_summer["start_dt"].apply(
        lambda d: pd.Timestamp(year=2000, month=d.month, day=d.day)
    )

    df_summer["year"] = df_summer["start_dt"].dt.year.astype(str)

    # Weekly aggregation
    df_trend = (
        df_summer
        .groupby(["year", pd.Grouper(key="season_date", freq="W")])
        .size()
        .reset_index(name="new_members")
    )

    fig = px.line(
        df_trend,
        x="season_date",
        y="new_members",
        color="year",
        title="New Members YoY (June–August)",
        markers=True
    )

    fig.update_layout(
        plot_bgcolor="#1e1e1e",
        paper_bgcolor="#1e1e1e",
        font_color="white",
        xaxis_title="Summer Week",
        yaxis_title="New Members",
        legend_title="Year"
    )

    fig.update_xaxes(
        tickformat="%b %d"
    )

    return fig


st.plotly_chart(new_members_yoy(df),  width='stretch')

# ------------------------------
# PROD_CNT VISUALIZATION
# ------------------------------
st.header("Personal Training Sessions YoY")

def pt_sessions_yoy(df):

    df["start_dt"] = pd.to_datetime(df["start_dt"])

    current_year = df["start_dt"].dt.year.max()
    prior_year = current_year - 1

    # Filter to summer window
    df_summer = df[
        (df["start_dt"].dt.month >= 6) &
        (df["start_dt"].dt.month <= 8) &
        (df["start_dt"].dt.year.isin([current_year, prior_year]))
    ].copy()

    # Normalize both years onto the same reference year (2000)
    df_summer["season_date"] = df_summer["start_dt"].apply(
        lambda d: pd.Timestamp(year=2000, month=d.month, day=d.day)
    )

    df_summer["year"] = df_summer["start_dt"].dt.year.astype(str)

    # Aggregate weekly PT sessions
    df_trend = (
        df_summer
        .groupby(["year", pd.Grouper(key="season_date", freq="W")])["prod_cnt"]
        .sum()
        .reset_index()
    )

    # Plot YoY lines
    fig = px.line(
        df_trend,
        x="season_date",
        y="prod_cnt",
        color="year",
        title="Personal Training Sessions YoY (June–August)",
        markers=True
    )

    fig.update_layout(
        plot_bgcolor="#1e1e1e",
        paper_bgcolor="#1e1e1e",
        font_color="white",
        xaxis_title="Summer Week",
        yaxis_title="PT Sessions",
        legend_title="Year"
    )

    # Weekly ticks formatted as Month-Day
    fig.update_xaxes(
        tickformat="%b %d",
        dtick="M1"
    )

    return fig


st.plotly_chart(pt_sessions_yoy(df), width='stretch')



st.plotly_chart(pt_sessions_yoy(df), width='stretch')
