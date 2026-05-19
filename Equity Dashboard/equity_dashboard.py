import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# =====================================================
# Project 1: Equity Derivatives Sales Dashboard
# Purpose: Dashboard for Equity Derivatives Sales team
# Metrics: Hit Ratio, Revenue, P&L Trend, Product Performance,
#          Underlying Mix, Top Clients, Quote-to-Trade Conversion
# =====================================================

st.set_page_config(
    page_title="Equity Derivatives Sales Dashboard",
    page_icon="📈",
    layout="wide"
)

# -----------------------------------------------------
# 1. Generate fake sales / trading data
# -----------------------------------------------------
@st.cache_data
def generate_fake_data(n_rows=1200, seed=42):
    np.random.seed(seed)

    clients = [
        "Goldman Sachs PB", "Mirae Asset", "KB Securities",
        "NH Investment", "Shinhan Securities", "Korea Investment",
        "Hana Securities", "Hyundai Motor Securities", "Woori Asset",
        "Private Bank Client A", "Private Bank Client B"
    ]

    product_types = [
        "Autocallable", "Equity Swap", "Variance Swap", "Option", "Structured Note"
    ]

    underlyings = [
        "KOSPI 200", "Samsung Electronics", "SK Hynix", "NAVER",
        "Hyundai Motor", "HSCEI", "S&P 500", "NASDAQ 100",
        "Nikkei 225", "Euro Stoxx 50"
    ]

    salespeople = ["Christine", "Daniel", "Yuna", "Michael", "Soojin"]
    trade_statuses = ["Traded", "Not Traded"]

    start_date = datetime(2025, 1, 1)
    dates = [start_date + timedelta(days=int(x)) for x in np.random.randint(0, 365, n_rows)]

    data = pd.DataFrame({
        "Date": dates,
        "Client": np.random.choice(clients, n_rows),
        "Product Type": np.random.choice(product_types, n_rows, p=[0.35, 0.2, 0.1, 0.2, 0.15]),
        "Underlying": np.random.choice(underlyings, n_rows),
        "Salesperson": np.random.choice(salespeople, n_rows),
        "Trade Status": np.random.choice(trade_statuses, n_rows, p=[0.42, 0.58])
    })

    # Quote Price and Trade Price are simplified pricing indicators, not actual derivative pricing models.
    data["Quote Price"] = np.round(np.random.normal(loc=100, scale=8, size=n_rows), 2)

    # Trade price only exists meaningfully when trade is executed.
    data["Trade Price"] = np.where(
        data["Trade Status"] == "Traded",
        data["Quote Price"] + np.random.normal(loc=0, scale=1.5, size=n_rows),
        np.nan
    )
    data["Trade Price"] = np.round(data["Trade Price"], 2)

    # Notional: larger trades are possible for institutional clients.
    data["Notional"] = np.where(
        data["Trade Status"] == "Traded",
        np.random.lognormal(mean=15.2, sigma=0.75, size=n_rows),
        np.random.lognormal(mean=14.6, sigma=0.7, size=n_rows)
    )
    data["Notional"] = np.round(data["Notional"], 0)

    # Revenue only generated when traded.
    # Assumption: revenue is roughly 5-35 bps of notional, with randomness by product.
    product_margin_bps = {
        "Autocallable": 0.0028,
        "Equity Swap": 0.0012,
        "Variance Swap": 0.0022,
        "Option": 0.0018,
        "Structured Note": 0.0032
    }

    data["Margin Rate"] = data["Product Type"].map(product_margin_bps)
    data["Revenue"] = np.where(
        data["Trade Status"] == "Traded",
        data["Notional"] * data["Margin Rate"] * np.random.uniform(0.7, 1.3, n_rows),
        0
    )
    data["Revenue"] = np.round(data["Revenue"], 2)

    # In this simplified dashboard, P&L is proxied by revenue plus small mark-to-market noise.
    data["P&L"] = np.where(
        data["Trade Status"] == "Traded",
        data["Revenue"] + np.random.normal(loc=0, scale=2500, size=n_rows),
        0
    )
    data["P&L"] = np.round(data["P&L"], 2)

    data["Month"] = pd.to_datetime(data["Date"]).dt.to_period("M").astype(str)

    return data


df = generate_fake_data()


# -----------------------------------------------------
# 2. Sidebar filters
# -----------------------------------------------------
st.sidebar.title("Dashboard Filters")

selected_clients = st.sidebar.multiselect(
    "Client",
    options=sorted(df["Client"].unique()),
    default=sorted(df["Client"].unique())
)

selected_products = st.sidebar.multiselect(
    "Product Type",
    options=sorted(df["Product Type"].unique()),
    default=sorted(df["Product Type"].unique())
)

selected_salespeople = st.sidebar.multiselect(
    "Salesperson",
    options=sorted(df["Salesperson"].unique()),
    default=sorted(df["Salesperson"].unique())
)

min_date = df["Date"].min().date()
max_date = df["Date"].max().date()
selected_date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

filtered_df = df[
    (df["Client"].isin(selected_clients)) &
    (df["Product Type"].isin(selected_products)) &
    (df["Salesperson"].isin(selected_salespeople))
]

if len(selected_date_range) == 2:
    start, end = selected_date_range
    filtered_df = filtered_df[
        (filtered_df["Date"].dt.date >= start) &
        (filtered_df["Date"].dt.date <= end)
    ]

# -----------------------------------------------------
# 3. Helper functions for metrics
# -----------------------------------------------------
def calculate_hit_ratio(data):
    total_quotes = len(data)
    traded_quotes = (data["Trade Status"] == "Traded").sum()
    if total_quotes == 0:
        return 0
    return traded_quotes / total_quotes


def format_money(value):
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.1f}K"
    else:
        return f"${value:.0f}"

# -----------------------------------------------------
# 4. Dashboard title and KPI cards
# -----------------------------------------------------
st.title("📈 Equity Derivatives Sales Dashboard")
st.caption("Fake-data dashboard for Equity Derivatives Sales workflow: client activity, hit ratio, revenue, P&L, and product analytics.")

col1, col2, col3, col4, col5 = st.columns(5)

hit_ratio = calculate_hit_ratio(filtered_df)
total_revenue = filtered_df["Revenue"].sum()
total_notional = filtered_df.loc[filtered_df["Trade Status"] == "Traded", "Notional"].sum()
total_pnl = filtered_df["P&L"].sum()
total_quotes = len(filtered_df)

col1.metric("Hit Ratio", f"{hit_ratio:.1%}")
col2.metric("Total Revenue", format_money(total_revenue))
col3.metric("Total Notional", format_money(total_notional))
col4.metric("Total P&L", format_money(total_pnl))
col5.metric("Total Quotes", f"{total_quotes:,}")

st.divider()

# -----------------------------------------------------
# 5. Main charts
# -----------------------------------------------------
left_col, right_col = st.columns(2)

# Monthly P&L trend
monthly_pnl = (
    filtered_df.groupby("Month", as_index=False)["P&L"]
    .sum()
    .sort_values("Month")
)

fig_monthly_pnl = px.line(
    monthly_pnl,
    x="Month",
    y="P&L",
    markers=True,
    title="Monthly P&L Trend"
)
left_col.plotly_chart(fig_monthly_pnl, use_container_width=True)

# Product revenue
product_revenue = (
    filtered_df.groupby("Product Type", as_index=False)["Revenue"]
    .sum()
    .sort_values("Revenue", ascending=False)
)

fig_product_revenue = px.bar(
    product_revenue,
    x="Product Type",
    y="Revenue",
    title="Total Revenue by Product Type"
)
right_col.plotly_chart(fig_product_revenue, use_container_width=True)

left_col2, right_col2 = st.columns(2)

# Underlying trade mix
underlying_mix = (
    filtered_df[filtered_df["Trade Status"] == "Traded"]
    .groupby("Underlying", as_index=False)["Notional"]
    .sum()
    .sort_values("Notional", ascending=False)
)

fig_underlying_mix = px.pie(
    underlying_mix,
    names="Underlying",
    values="Notional",
    title="Underlying Mix by Traded Notional"
)
left_col2.plotly_chart(fig_underlying_mix, use_container_width=True)

# Top clients by notional
top_clients = (
    filtered_df[filtered_df["Trade Status"] == "Traded"]
    .groupby("Client", as_index=False)["Notional"]
    .sum()
    .sort_values("Notional", ascending=False)
    .head(10)
)

fig_top_clients = px.bar(
    top_clients,
    x="Notional",
    y="Client",
    orientation="h",
    title="Top Clients by Traded Notional"
)
fig_top_clients.update_layout(yaxis={"categoryorder": "total ascending"})
right_col2.plotly_chart(fig_top_clients, use_container_width=True)

st.divider()

#add something
average_notional = filtered_df.loc[
    filtered_df["Trade Status"] == "Traded", 
    "Notional"
].mean()

col5.metric("Avg Trade Size", format_money(average_notional))

# -----------------------------------------------------
# 6. Detailed analysis tables
# -----------------------------------------------------
st.subheader("Client Hit Ratio")

client_hit_ratio = (
    filtered_df.groupby("Client")
    .agg(
        Total_Quotes=("Trade Status", "count"),
        Trades=("Trade Status", lambda x: (x == "Traded").sum()),
        Total_Notional=("Notional", "sum"),
        Total_Revenue=("Revenue", "sum"),
        Total_PnL=("P&L", "sum")
    )
    .reset_index()
)
client_hit_ratio["Hit_Ratio"] = client_hit_ratio["Trades"] / client_hit_ratio["Total_Quotes"]
client_hit_ratio = client_hit_ratio.sort_values("Total_Revenue", ascending=False)

st.dataframe(
    client_hit_ratio.style.format({
        "Hit_Ratio": "{:.1%}",
        "Total_Notional": "${:,.0f}",
        "Total_Revenue": "${:,.0f}",
        "Total_PnL": "${:,.0f}"
    }),
    use_container_width=True
)

st.subheader("Raw Transaction Data")
st.dataframe(
    filtered_df.sort_values("Date", ascending=False),
    use_container_width=True
)

# -----------------------------------------------------
# 7. Download button
# -----------------------------------------------------
csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download filtered data as CSV",
    data=csv,
    file_name="equity_derivatives_sales_data.csv",
    mime="text/csv"
)
