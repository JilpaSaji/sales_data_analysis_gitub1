
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "sales.db"


# --------------------------------------------------
# 2. LOAD DATA FROM SQLITE
# --------------------------------------------------

@st.cache_data
def load_data():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}. "
            "Run the database creation notebook first."
        )

    with sqlite3.connect(DB_PATH) as conn:
        data = pd.read_sql_query("SELECT * FROM sales", conn)

    data.columns = data.columns.str.strip().str.lower()

    required_columns = [
        "order_id", "order_date", "amount", "profit",
        "quantity", "category", "sub_category",
        "state", "city", "paymentmode"
    ]

    missing_columns = [
        col for col in required_columns
        if col not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing database columns: {missing_columns}"
        )

    data["order_date"] = pd.to_datetime(
        data["order_date"], errors="coerce"
    )

    for col in ["amount", "profit", "quantity"]:
        data[col] = pd.to_numeric(
            data[col], errors="coerce"
        )

    data = data.dropna(
        subset=["order_date", "amount", "profit", "quantity"]
    )

    return data


try:
    df = load_data()
except (FileNotFoundError, ValueError, sqlite3.Error) as error:
    st.error(str(error))
    st.stop()


# --------------------------------------------------
# 3. DASHBOARD TITLE
# --------------------------------------------------

st.title("📊 Sales Data Analysis Dashboard")
st.caption(
    "Sales performance, product trends, and regional insights"
)


# --------------------------------------------------
# 4. SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.header("Dashboard Filters")

min_date = df["order_date"].min().date()
max_date = df["order_date"].max().date()

date_range = st.sidebar.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

categories = sorted(
    df["category"].dropna().unique().tolist()
)

selected_categories = st.sidebar.multiselect(
    "Select categories",
    categories,
    default=categories
)

states = sorted(
    df["state"].dropna().unique().tolist()
)

selected_states = st.sidebar.multiselect(
    "Select states",
    states,
    default=states
)

products = sorted(
    df["sub_category"].dropna().unique().tolist()
)

selected_products = st.sidebar.multiselect(
    "Select sub-categories",
    products,
    default=products
)


# --------------------------------------------------
# 5. APPLY FILTERS
# --------------------------------------------------

filtered_df = df.copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range

    filtered_df = filtered_df[
        filtered_df["order_date"].dt.date.between(
            start_date, end_date
        )
    ]

filtered_df = filtered_df[
    filtered_df["category"].isin(selected_categories)
    & filtered_df["state"].isin(selected_states)
    & filtered_df["sub_category"].isin(selected_products)
]

if filtered_df.empty:
    st.warning(
        "No records match the selected filters. "
        "Change the filters to see results."
    )
    st.stop()


# --------------------------------------------------
# 6. KEY PERFORMANCE INDICATORS
# --------------------------------------------------

total_sales = filtered_df["amount"].sum()
total_profit = filtered_df["profit"].sum()
total_quantity = filtered_df["quantity"].sum()
distinct_orders = filtered_df["order_id"].nunique()

# Provisional until the order structure is validated
sales_per_order_id = (
    total_sales / distinct_orders
    if distinct_orders > 0 else 0
)

profit_margin = (
    total_profit / total_sales * 100
    if total_sales != 0 else 0
)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Sales",
    f"{total_sales:,.2f}"
)

col2.metric(
    "Total Profit",
    f"{total_profit:,.2f}"
)

col3.metric(
    "Distinct Order IDs",
    f"{distinct_orders:,}"
)

col4.metric(
    "Sales per Distinct Order ID",
    f"{sales_per_order_id:,.2f}",
    help=(
        "Provisional metric. Confirm the meaning of Order ID "
        "before interpreting this as average order value."
    )
)

st.caption(
    f"Units sold: {total_quantity:,.0f} | "
    f"Profit margin: {profit_margin:.2f}%"
)


# --------------------------------------------------
# 7. MONTHLY SALES TREND
# --------------------------------------------------

st.subheader("Monthly Sales Trend")

monthly = (
    filtered_df
    .assign(
        month=filtered_df["order_date"].dt.to_period("M").dt.to_timestamp()
    )
    .groupby("month", as_index=False)
    .agg(
        Sales=("amount", "sum"),
        Profit=("profit", "sum")
    )
    .sort_values("month")
)

fig_monthly = px.line(
    monthly,
    x="month",
    y=["Sales", "Profit"],
    markers=True,
    title="Monthly Sales and Profit",
    labels={
        "month": "Month",
        "value": "Amount",
        "variable": "Metric"
    }
)

st.plotly_chart(fig_monthly, use_container_width=True)


# --------------------------------------------------
# 8. CATEGORY PERFORMANCE
# --------------------------------------------------

st.subheader("Category Performance")

category_data = (
    filtered_df
    .groupby("category", as_index=False)
    .agg(
        Sales=("amount", "sum"),
        Profit=("profit", "sum")
    )
    .sort_values("Sales", ascending=False)
)

fig_category = px.bar(
    category_data,
    x="category",
    y=["Sales", "Profit"],
    barmode="group",
    title="Sales and Profit by Category",
    labels={
        "category": "Category",
        "value": "Amount",
        "variable": "Metric"
    }
)

st.plotly_chart(fig_category, use_container_width=True)


# --------------------------------------------------
# 9. REGIONAL PERFORMANCE
# --------------------------------------------------

st.subheader("Regional Performance")

state_data = (
    filtered_df
    .groupby("state", as_index=False)
    .agg(
        Sales=("amount", "sum"),
        Profit=("profit", "sum")
    )
    .sort_values("Sales", ascending=False)
    .head(10)
)

fig_state = px.bar(
    state_data,
    x="Sales",
    y="state",
    orientation="h",
    color="Profit",
    title="Top 10 States by Sales",
    labels={"state": "State"}
)

fig_state.update_layout(
    yaxis={"categoryorder": "total ascending"}
)

st.plotly_chart(fig_state, use_container_width=True)


# --------------------------------------------------
# 10. PRODUCT PERFORMANCE
# --------------------------------------------------

st.subheader("Product Performance")

product_data = (
    filtered_df
    .groupby("sub_category", as_index=False)
    .agg(
        Sales=("amount", "sum"),
        Profit=("profit", "sum"),
        Quantity=("quantity", "sum")
    )
    .sort_values("Sales", ascending=False)
)

left, right = st.columns(2)

with left:
    st.write("Top 10 Sub-Categories by Sales")
    st.dataframe(
        product_data.head(10),
        use_container_width=True,
        hide_index=True
    )

with right:
    st.write("Bottom 10 Sub-Categories by Profit")
    st.dataframe(
        product_data.nsmallest(10, "Profit"),
        use_container_width=True,
        hide_index=True
    )


# --------------------------------------------------
# 11. PAYMENT MODE ANALYSIS
# --------------------------------------------------

st.subheader("Payment Mode Analysis")

payment_data = (
    filtered_df
    .groupby("paymentmode", as_index=False)
    .agg(Sales=("amount", "sum"))
)

fig_payment = px.pie(
    payment_data,
    names="paymentmode",
    values="Sales",
    title="Sales Share by Payment Mode",
    hole=0.35
)

st.plotly_chart(fig_payment, use_container_width=True)


# --------------------------------------------------
# 12. FILTERED SALES DATA
# --------------------------------------------------

st.subheader("Filtered Sales Records")

st.write(f"Records displayed: {len(filtered_df):,}")

st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# 13. DOWNLOAD FILTERED REPORT
# --------------------------------------------------

csv_data = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Filtered Sales CSV",
    data=csv_data,
    file_name="filtered_sales_report.csv",
    mime="text/csv"
)


# --------------------------------------------------
# 14. FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Sales Analytics Internship Project | "
    "Python • Pandas • SQLite • Streamlit • Plotly"
)
