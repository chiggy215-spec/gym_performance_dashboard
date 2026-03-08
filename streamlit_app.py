import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
from streamlit_autorefresh import st_autorefresh

# ------------------------------
# AUTO REFRESH (Daily)
# ------------------------------
st_autorefresh(interval=24*60*60*1000, key="daily_refresh")

# ------------------------------
# PAGE CONFIG
# ------------------------------
st.set_page_config(
    page_title="Gym Performance Dashboard",
    layout="wide"
)

st.title("Gym Performance Dashboard")
st.write("Tracking New Gym Memberships and PT Sales Summer Goals (June–August)")

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
df_new = df[df["cust_type"] == "NEW"].copy()

# ------------------------------
# FILTERS
# ------------------------------
st.sidebar.header("Filters")

# Region, district, gym filters
regions = ["All"] + sorted(df_new["region"].dropna().unique().tolist())
districts = ["All"] + sorted(df_new["district"].dropna().unique().tolist())
gyms = ["All"] + sorted(df_new["store_nbr"].dropna().unique().tolist())

selected_region = st.sidebar.selectbox("Region", regions)
filtered_df = df_new if selected_region == "All" else df_new[df_new["region"] == selected_region]

available_districts = ["All"] + sorted(filtered_df["district"].dropna().unique().tolist())
selected_district = st.sidebar.selectbox("District", available_districts)
if selected_district != "All":
    filtered_df = filtered_df[filtered_df["district"] == selected_district]

available_gyms = ["All"] + sorted(filtered_df["store_nbr"].dropna().unique().tolist())
selected_gym = st.sidebar.selectbox("Gym", available_gyms)
if selected_gym != "All":
    filtered_df = filtered_df[filtered_df["store_nbr"] == selected_gym]

# Date range filter
min_date = filtered_df["start_dt"].min()
max_date = filtered_df["start_dt"].max()
start_date, end_date = st.sidebar.date_input(
    "Date Range",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)
filtered_df = filtered_df[(filtered_df["start_dt"] >= pd.Timestamp(start_date)) &
                          (filtered_df["start_dt"] <= pd.Timestamp(end_date))]

# ------------------------------
# HELPER FUNCTIONS
# ------------------------------
def calc_summary(df_current, df_prior, group_field):
    """
    Summarizes current and prior totals, target (prior*1.1), and performance %.
    """
    curr = df_current.groupby(group_field).size().reset_index(name="current")
    prior = df_prior.groupby(group_field).size().reset_index(name="prior")
    merged = pd.merge(curr, prior, on=group_field, how="outer").fillna(0)
    merged["current"] = merged["current"].astype(int)
    merged["prior"] = merged["prior"].astype(int)
    merged["target"] = (merged["prior"] * 1.10).round().astype(int)
    merged["performance_pct"] = merged["current"] / merged["target"]
    return merged

def summer_projection(df_current, df_prior):
    """
    Calculates projected total, variance, and target for summer months.
    """
    summer_start_current = pd.Timestamp(f"{df_current['start_dt'].dt.year.max()}-06-01")
    summer_end_current = pd.Timestamp(f"{df_current['start_dt'].dt.year.max()}-08-31")
    summer_start_prior = summer_start_current.replace(year=summer_start_current.year-1)
    summer_end_prior = summer_end_current.replace(year=summer_end_current.year-1)

    df_current_summer = df_current[(df_current["start_dt"] >= summer_start_current) &
                                   (df_current["start_dt"] <= df_current["start_dt"].max())]
    df_prior_summer = df_prior[(df_prior["start_dt"] >= summer_start_prior) &
                               (df_prior["start_dt"] <= summer_end_prior)]

    days_elapsed = (df_current_summer["start_dt"].max() - summer_start_current).days + 1
    prior_to_date = df_prior_summer[df_prior_summer["start_dt"] <= summer_start_prior + timedelta(days=days_elapsed)].shape[0]
    prior_full_total = df_prior_summer.shape[0]
    current_total = df_current_summer.shape[0]

    percent_complete = prior_to_date / prior_full_total if prior_full_total > 0 else 1
    projected_total = int(current_total / percent_complete)
    target_total = int(prior_full_total * 1.10)
    variance = projected_total - target_total

    return projected_total, variance, target_total

def build_leaderboard(summary_df, group_field, display_name, top_n=10, ascending=False):
    """
    Builds a leaderboard for top or bottom performers.
    Returns dataframe with columns: Display Name, Prior Year, Current Year, Target, Performance %
    """
    df_lb = summary_df.copy()
    df_lb = df_lb.sort_values("performance_pct", ascending=ascending).head(top_n)
    df_lb = df_lb.rename(columns={group_field: display_name, "prior":"Prior Year","current":"Current Year","target":"Target"})
    df_lb["Performance %"] = (df_lb["Current Year"] / df_lb["Target"] * 100).round(1).astype(str) + "%"
    return df_lb[[display_name, "Prior Year","Current Year","Target","Performance %"]]

# ------------------------------
# SUMMER DATA CALCULATIONS
# ------------------------------
current_year = filtered_df["start_dt"].dt.year.max()
prior_year = current_year - 1

summer_start_current = pd.Timestamp(f"{current_year}-06-01")
summer_start_prior = pd.Timestamp(f"{prior_year}-06-01")
summer_end_prior = pd.Timestamp(f"{prior_year}-08-31")

df_current_summer = filtered_df[(filtered_df["start_dt"] >= summer_start_current)]
df_prior_summer = df_new[(df_new["start_dt"] >= summer_start_prior) & (df_new["start_dt"] <= summer_end_prior)]

gym_summary = calc_summary(df_current_summer, df_prior_summer, "store_nbr")
district_summary = calc_summary(df_current_summer, df_prior_summer, "district")
region_summary = calc_summary(df_current_summer, df_prior_summer, "region")

projected_total, variance, target_total = summer_projection(df_current_summer, df_prior_summer)

# ------------------------------
# ROW 1: KPIs
# ------------------------------
st.header("Key Metrics (June–August)")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Current Members", f"{df_current_summer.shape[0]:,}")
col2.metric("Summer Target", f"{target_total:,}")
col3.metric("Projected Total", f"{projected_total:,}")
col4.metric("Projected Variance", f"{variance:,}", delta=f"{variance:,}", delta_color="inverse" if variance>=0 else "normal")

# ------------------------------
# ROW 2: Goal Gauge + Cumulative Growth
# ------------------------------
col1, col2 = st.columns(2)

# Goal Gauge
with col1:
    current_value = df_current_summer.shape[0]
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=current_value,
        number={'valueformat': ',', 'font': {'size': 32}},
        title={'text': "Summer Goal Progress", 'font': {'size': 20}},
        gauge={
            'axis': {'range': [0, max(target_total*1.2, current_value)], 'tickformat': ","},
            'bar': {'color': "#3B82F6", 'thickness': 0.5},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#CBCCCE",
            'threshold': {'line': {'color': "#111827", 'width': 4}, 'thickness': 0.75, 'value': target_total}
        }
    ))
    # Position target annotation below the current number
    fig_gauge.add_annotation(x=0.5, y=0.0, text=f"Summer Target: {target_total:,}", showarrow=False, font=dict(size=14))
    st.plotly_chart(fig_gauge, width='stretch')

# Cumulative Growth
with col2:
    df_overlay = filtered_df.copy()
    df_overlay = df_overlay[df_overlay["start_dt"].dt.year.isin([prior_year, current_year])]
    df_overlay["overlay_date"] = df_overlay["start_dt"].apply(lambda d: pd.Timestamp(2000, d.month, d.day))
    df_overlay["year"] = df_overlay["start_dt"].dt.year.astype(str)
    df_overlay = df_overlay.sort_values("start_dt")
    df_overlay["cumulative"] = df_overlay.groupby("year").cumcount() + 1

    fig_cum = px.line(df_overlay, x="overlay_date", y="cumulative", color="year", markers=True,
                      title="Cumulative New Members YoY (Season Comparison)")
    fig_cum.update_layout(xaxis_title="Month / Day", yaxis_title="Cumulative Members", legend_title="Year")
    fig_cum.update_xaxes(tickformat="%b %d")
    st.plotly_chart(fig_cum, width='stretch')

# ------------------------------
# ROW 3: Region / District Bullet Charts
# ------------------------------
st.subheader("Performance by Region / District")
col1, col2 = st.columns(2)

def plot_bullet_chart(summary_df, y_field, title):
    df_sorted = summary_df.sort_values("performance_pct")
    fig = go.Figure()
    fig.add_trace(go.Bar(y=df_sorted[y_field].astype(str), x=df_sorted["current"], orientation="h",
                         marker_color="#3B82F6", text=df_sorted["current"], textposition="inside"))
    fig.add_trace(go.Scatter(y=df_sorted[y_field].astype(str), x=df_sorted["target"], mode="markers",
                             marker=dict(symbol="line-ns", size=28, color="#009113", line=dict(width=4))))
    for _, row in df_sorted.iterrows():
        fig.add_annotation(x=row["target"], y=str(row[y_field]), text=f"{row['target']:,}",
                           showarrow=False, xanchor="left", xshift=8, font=dict(color="#009113", size=12))
    fig.update_layout(title=title, xaxis_title="New Members", yaxis_title=y_field, height=400, showlegend=False)
    return fig

with col1:
    st.plotly_chart(plot_bullet_chart(region_summary, "region", "Region Progress vs Target"), width='stretch')
with col2:
    st.plotly_chart(plot_bullet_chart(district_summary, "district", "District Progress vs Target"), width='stretch')

# ------------------------------
# GYM BULLET CHART
# ------------------------------
st.subheader("Gym Progress vs Target")
gym_summary_sorted = gym_summary.sort_values("performance_pct").reset_index(drop=True)
gym_summary_sorted["y_coord"] = gym_summary_sorted.index
gym_summary_sorted["gym_label"] = gym_summary_sorted["store_nbr"].astype(str)

gym_fig = go.Figure()
gym_fig.add_trace(go.Bar(y=gym_summary_sorted["y_coord"], x=gym_summary_sorted["current"], orientation="h",
                         marker_color="#3B82F6", text=gym_summary_sorted["current"], textposition="inside", width=0.7))
gym_fig.add_trace(go.Scatter(y=gym_summary_sorted["y_coord"], x=gym_summary_sorted["target"], mode="markers",
                             marker=dict(symbol="line-ns", size=24, color="#009113", line=dict(width=4))))
for _, row in gym_summary_sorted.iterrows():
    gym_fig.add_annotation(x=row["target"], y=row["y_coord"], text=f"{row['target']:,}", showarrow=False,
                           xanchor="left", xshift=10, font=dict(color="#009113", size=11))
gym_fig.update_layout(title="Gym Progress vs Target", xaxis_title="New Members",
                      yaxis=dict(title="Store Number", tickmode="array", tickvals=gym_summary_sorted["y_coord"],
                                 ticktext=gym_summary_sorted["gym_label"], range=[-0.5, len(gym_summary_sorted)-0.5]),
                      height=max(500, len(gym_summary_sorted)*45), showlegend=False, margin=dict(l=120, r=50))
st.plotly_chart(gym_fig, width='stretch')

# ------------------------------
# TOP / BOTTOM GYM LEADERBOARDS (SIMPLIFIED)
# ------------------------------
st.subheader("Top / Bottom Gyms")
col1, col2 = st.columns(2)

with col1:
    st.write("Top 5 Gyms")
    st.dataframe(build_leaderboard(gym_summary, "store_nbr", "Gym", top_n=5), width='stretch', hide_index=True)

with col2:
    st.write("Bottom 5 Gyms")
    st.dataframe(build_leaderboard(gym_summary, "store_nbr", "Gym", top_n=5, ascending=True), width='stretch', hide_index=True)

# ------------------------------
# PERSONAL TRAINING KPI TILES
# ------------------------------
st.subheader("Personal Training Summary (June–August)")

current_year = df["start_dt"].dt.year.max()
prior_year = current_year - 1

latest_current_date = df[df["start_dt"].dt.year == current_year]["start_dt"].max()

# Current year total through latest date
current_total = df[
    (df["start_dt"].dt.year == current_year) &
    (df["start_dt"] <= latest_current_date)
]["prod_cnt"].sum()

# Correct prior year total: from 6/1 up to same MM/DD as current year's latest date
summer_start_prior = pd.Timestamp(f"{prior_year}-06-01")
prior_same_day = pd.Timestamp(f"{prior_year}-{latest_current_date.month:02d}-{latest_current_date.day:02d}")

prior_same_day_total = df[
    (df["start_dt"].dt.year == prior_year) &
    (df["start_dt"] >= summer_start_prior) &
    (df["start_dt"] <= prior_same_day)
]["prod_cnt"].sum()

# Prior year full summer total (6/1–8/31)
summer_end_prior = pd.Timestamp(f"{prior_year}-08-31")
prior_full_summer_total = df[
    (df["start_dt"].dt.year == prior_year) &
    (df["start_dt"] >= summer_start_prior) &
    (df["start_dt"] <= summer_end_prior)
]["prod_cnt"].sum()

# Display KPIs
col1, col2, col3 = st.columns(3)
col1.metric("Current Year Total PT Sessions", f"{current_total:,}")
col2.metric(f"Prior Year Total PT Sessions (through {latest_current_date.strftime('%m/%d')})", f"{prior_same_day_total:,}")
col3.metric("Prior Year Full Summer Total PT Sessions", f"{prior_full_summer_total:,}")

# ------------------------------
# PROD_CNT YOY LINE CHART
# ------------------------------
st.header("Total Personal Training Sessions YoY (June–August)")

def prod_cnt_yoy_overlay(df):
    df = df.copy()
    df["start_dt"] = pd.to_datetime(df["start_dt"])
    
    # Current and prior year
    current_year = df["start_dt"].dt.year.max()
    prior_year = current_year - 1
    
    # Filter to summer months (June–August) and these two years
    df_summer = df[
        (df["start_dt"].dt.month >= 6) &
        (df["start_dt"].dt.month <= 8) &
        (df["start_dt"].dt.year.isin([current_year, prior_year]))
    ].copy()
    
    # Normalize both years onto same reference year (2000) for overlay
    df_summer["season_date"] = df_summer["start_dt"].apply(
        lambda d: pd.Timestamp(year=2000, month=d.month, day=d.day)
    )
    
    df_summer["year"] = df_summer["start_dt"].dt.year.astype(str)
    
    # Aggregate total prod_cnt per day
    df_trend = df_summer.groupby(["season_date", "year"])["prod_cnt"].sum().reset_index()
    
    # Plot line chart
    fig = px.line(
        df_trend,
        x="season_date",
        y="prod_cnt",
        color="year",
        title="Total Personal Training Sessions YoY (June–August)",
        markers=True
    )
    
    fig.update_layout(
        plot_bgcolor="#1e1e1e",
        paper_bgcolor="#1e1e1e",
        font_color="white",
        xaxis_title="Summer Date",
        yaxis_title="PT Sessions",
        legend_title="Year"
    )
    
    # Format X-axis as Month-Day
    fig.update_xaxes(tickformat="%b %d")
    
    return fig

st.plotly_chart(prod_cnt_yoy_overlay(df), width='stretch')

# ------------------------------
# PERSONAL TRAINING PERFORMANCE LEADERBOARDS (FIXED)
# ------------------------------

st.subheader("Top Performing Units — Personal Training Sessions")

def calc_pt_summary_correct(df, group_field):
    """
    Returns a summary table with prior year (through same day as current year),
    current year, improvement %, and performance flag.
    """
    df = df.copy()
    current_year = df["start_dt"].dt.year.max()
    prior_year = current_year - 1

    # Determine cutoff date for current year
    latest_current_date = df[df["start_dt"].dt.year == current_year]["start_dt"].max()
    cutoff_month = latest_current_date.month
    cutoff_day = latest_current_date.day

    # Current year PT sessions (6/1 → latest_current_date)
    summer_current = df[
        (df["start_dt"].dt.year == current_year) &
        (df["start_dt"] >= pd.Timestamp(f"{current_year}-06-01")) &
        (df["start_dt"] <= latest_current_date)
    ]
    curr = summer_current.groupby(group_field)["prod_cnt"].sum().reset_index(name="current")

    # Prior year PT sessions for same period (6/1 → same month/day as current year)
    summer_prior = df[
        (df["start_dt"].dt.year == prior_year) &
        (
            (df["start_dt"].dt.month < cutoff_month) |
            ((df["start_dt"].dt.month == cutoff_month) & (df["start_dt"].dt.day <= cutoff_day))
        ) &
        (df["start_dt"] >= pd.Timestamp(f"{prior_year}-06-01"))
    ]
    prior = summer_prior.groupby(group_field)["prod_cnt"].sum().reset_index(name="prior")

    # Merge
    merged = pd.merge(prior, curr, on=group_field, how="outer").fillna(0)
    merged["current"] = merged["current"].astype(int)
    merged["prior"] = merged["prior"].astype(int)

    # Improvement %
    merged["Improvement %"] = ((merged["current"] - merged["prior"]) / merged["prior"].replace(0, 1) * 100).round(1)

    # Flag top performers
    merged["Performance"] = merged["current"] >= merged["prior"]

    return merged.sort_values("Improvement %", ascending=False)

# ------------------------------
# Generate PT leaderboards
# ------------------------------
gym_pt_summary = calc_pt_summary_correct(df, "store_nbr")
district_pt_summary = calc_pt_summary_correct(df, "district")
region_pt_summary = calc_pt_summary_correct(df, "region")

# ------------------------------
# Display as Streamlit leaderboards
# ------------------------------
col1, col2, col3 = st.columns(3)

def display_pt_leaderboard(col, df, group_field, title):
    top_count = df[df["Performance"]].shape[0]
    col.metric(f"{title} Exceeding Last Year", top_count)
    display_df = df.rename(columns={group_field: title})
    col.dataframe(display_df[[title, "prior", "current", "Improvement %", "Performance"]], width='stretch', hide_index=True)

display_pt_leaderboard(col1, gym_pt_summary, "store_nbr", "Gym")
display_pt_leaderboard(col2, district_pt_summary, "district", "District")
display_pt_leaderboard(col3, region_pt_summary, "region", "Region")
