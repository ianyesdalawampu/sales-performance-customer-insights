import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Sales Performance & Customer Insights",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Sales Performance & Customer Insights")
st.caption("A Python dashboard for revenue, products, customers, and order performance.")

# -----------------------------
# Data loading
# -----------------------------
st.sidebar.header("1. Load your cleaned datasets")
st.sidebar.caption(
    "Upload the four cleaned CSV files. Keep the original column names shown below."
)

uploaded_customers = st.sidebar.file_uploader("customers_cleaned.csv", type="csv", key="customers")
uploaded_orders = st.sidebar.file_uploader("orders_cleaned.csv", type="csv", key="orders")
uploaded_items = st.sidebar.file_uploader("order_items_cleaned.csv", type="csv", key="items")
uploaded_products = st.sidebar.file_uploader("products_cleaned.csv", type="csv", key="products")

DATA_DIR = Path("cleaned_data")

def read_dataset(uploaded_file, filename):
    if uploaded_file is not None:
        return pd.read_csv(uploaded_file)
    path = DATA_DIR / filename
    if path.exists():
        return pd.read_csv(path)
    return None

customers = read_dataset(uploaded_customers, "customers_cleaned.csv")
orders = read_dataset(uploaded_orders, "orders_cleaned.csv")
items = read_dataset(uploaded_items, "order_items_cleaned.csv")
products = read_dataset(uploaded_products, "products_cleaned.csv")

datasets = {
    "customers": customers,
    "orders": orders,
    "order_items": items,
    "products": products
}

missing_datasets = [name for name, df in datasets.items() if df is None]
if missing_datasets:
    st.info(
        "Upload all four cleaned CSV files in the sidebar, or place them in a "
        "`cleaned_data` folder beside this app using these filenames: "
        "`customers_cleaned.csv`, `orders_cleaned.csv`, "
        "`order_items_cleaned.csv`, and `products_cleaned.csv`."
    )
    st.stop()

# -----------------------------
# Required columns and validation
# -----------------------------
required = {
    "customers": {"customer_id", "region_name", "city"},
    "orders": {"order_id", "customer_id", "order_datetime", "order_status",
               "sales_channel", "discount_pct", "shipping_fee"},
    "order_items": {"order_item_id", "order_id", "product_id", "quantity",
                    "unit_price_at_purchase"},
    "products": {"product_id", "product_name", "category", "brand", "unit_cost"}
}

for name, cols in required.items():
    absent = cols - set(datasets[name].columns)
    if absent:
        st.error(f"{name} is missing required columns: {', '.join(sorted(absent))}")
        st.stop()

# Normalize key text to avoid whitespace mismatches.
for df, cols in [
    (customers, ["customer_id"]),
    (orders, ["order_id", "customer_id"]),
    (items, ["order_item_id", "order_id", "product_id"]),
    (products, ["product_id"])
]:
    for col in cols:
        df[col] = df[col].astype("string").str.strip()

# Primary key checks. Stop rather than silently choose an arbitrary duplicate.
primary_keys = [
    ("customers", customers, "customer_id"),
    ("orders", orders, "order_id"),
    ("order_items", items, "order_item_id"),
    ("products", products, "product_id")
]
pk_issues = []
for label, df, key in primary_keys:
    duplicate_count = int(df[key].duplicated().sum())
    missing_count = int(df[key].isna().sum())
    if duplicate_count or missing_count:
        pk_issues.append(
            f"{label}: {duplicate_count:,} duplicate {key} values; "
            f"{missing_count:,} missing {key} values"
        )

if pk_issues:
    st.error("Primary-key validation failed. Resolve these issues in your cleaning notebook before using the dashboard:")
    for issue in pk_issues:
        st.write(f"- {issue}")
    st.stop()

# Foreign key checks
orphan_customer_orders = orders.loc[~orders["customer_id"].isin(customers["customer_id"])]
orphan_order_items = items.loc[~items["order_id"].isin(orders["order_id"])]
orphan_product_items = items.loc[~items["product_id"].isin(products["product_id"])]

if len(orphan_customer_orders) or len(orphan_order_items) or len(orphan_product_items):
    st.error("Foreign-key validation failed. Resolve orphan records before building the fact table.")
    st.write({
        "Orders with unknown customer_id": len(orphan_customer_orders),
        "Order items with unknown order_id": len(orphan_order_items),
        "Order items with unknown product_id": len(orphan_product_items)
    })
    st.stop()

# -----------------------------
# Prepare and merge fact table
# -----------------------------
orders = orders.copy()
items = items.copy()
products = products.copy()
customers = customers.copy()

orders["order_datetime"] = pd.to_datetime(
    orders["order_datetime"], errors="coerce", format="mixed"
)
orders["discount_pct"] = pd.to_numeric(orders["discount_pct"], errors="coerce").fillna(0)
items["quantity"] = pd.to_numeric(items["quantity"], errors="coerce")
items["unit_price_at_purchase"] = pd.to_numeric(
    items["unit_price_at_purchase"].astype("string")
      .str.replace("₱", "", regex=False)
      .str.replace(",", "", regex=False)
      .str.strip(),
    errors="coerce"
)
products["unit_cost"] = pd.to_numeric(products["unit_cost"], errors="coerce")

fact = (
    items.merge(orders, on="order_id", how="left", validate="many_to_one")
         .merge(products, on="product_id", how="left", validate="many_to_one")
         .merge(customers, on="customer_id", how="left", validate="many_to_one",
                suffixes=("", "_customer"))
)

# Apply the order-level discount to each line item.
fact["gross_revenue"] = fact["quantity"] * fact["unit_price_at_purchase"]
fact["net_revenue"] = fact["gross_revenue"] * (1 - fact["discount_pct"])
fact["estimated_product_cost"] = fact["quantity"] * fact["unit_cost"]
fact["estimated_gross_profit"] = fact["net_revenue"] - fact["estimated_product_cost"]
fact["order_month"] = fact["order_datetime"].dt.to_period("M").astype("string")

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("2. Filter the analysis")

statuses_available = sorted(fact["order_status"].dropna().astype(str).unique().tolist())
default_statuses = [s for s in ["Completed", "Shipped"] if s in statuses_available]
selected_statuses = st.sidebar.multiselect(
    "Sales statuses included in revenue",
    options=statuses_available,
    default=default_statuses
)
st.sidebar.caption(
    "Default includes Completed and Shipped. Confirm that this matches your project’s "
    "sales definition. Returned, Cancelled, and Pending are excluded by default."
)

valid_dates = fact["order_datetime"].dropna()
if valid_dates.empty:
    st.error("No valid order dates were found. Review the order_datetime cleaning.")
    st.stop()

min_date = valid_dates.min().date()
max_date = valid_dates.max().date()
date_range = st.sidebar.date_input(
    "Order date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

regions = sorted(fact["region_name"].dropna().astype(str).unique().tolist())
selected_regions = st.sidebar.multiselect("Region", regions, default=[])
categories = sorted(fact["category"].dropna().astype(str).unique().tolist())
selected_categories = st.sidebar.multiselect("Category", categories, default=[])
channels = sorted(fact["sales_channel"].dropna().astype(str).unique().tolist())
selected_channels = st.sidebar.multiselect("Sales channel", channels, default=[])

# Date input can be a single date or a pair.
if isinstance(date_range, tuple):
    start_date = date_range[0]
    end_date = date_range[-1]
else:
    start_date = end_date = date_range

mask = (
    fact["order_status"].isin(selected_statuses)
    & fact["order_datetime"].dt.date.between(start_date, end_date)
)
if selected_regions:
    mask &= fact["region_name"].astype(str).isin(selected_regions)
if selected_categories:
    mask &= fact["category"].astype(str).isin(selected_categories)
if selected_channels:
    mask &= fact["sales_channel"].astype(str).isin(selected_channels)

sales = fact.loc[mask].copy()
if sales.empty:
    st.warning("No sales records match the selected filters. Adjust the filters to view results.")
    st.stop()

# -----------------------------
# KPI calculations
# -----------------------------
total_revenue = sales["net_revenue"].sum(min_count=1)
total_orders = sales["order_id"].nunique()
aov = total_revenue / total_orders if total_orders else 0
unique_customers = sales["customer_id"].nunique()
units_sold = sales["quantity"].sum()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Net Revenue", f"₱{(total_revenue or 0):,.2f}")
c2.metric("Orders", f"{total_orders:,}")
c3.metric("Average Order Value", f"₱{aov:,.2f}")
c4.metric("Customers", f"{unique_customers:,}")
c5.metric("Units Sold", f"{units_sold:,.0f}")

st.caption(
    "Revenue is calculated as quantity × purchase unit price × (1 − discount percentage). "
    "Shipping fees are excluded. AOV = filtered net revenue ÷ unique filtered orders."
)

# -----------------------------
# Charts
# -----------------------------
st.subheader("Revenue performance")

monthly = (
    sales.dropna(subset=["order_datetime"])
         .groupby(sales["order_datetime"].dt.to_period("M"))["net_revenue"]
         .sum()
         .rename_axis("month")
         .reset_index()
)
monthly["month"] = monthly["month"].astype(str)

left, right = st.columns(2)
with left:
    fig = px.line(
        monthly, x="month", y="net_revenue", markers=True,
        title="Monthly Net Revenue",
        labels={"month": "Month", "net_revenue": "Net revenue (₱)"}
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    category_rev = (
        sales.groupby("category", dropna=False)["net_revenue"]
             .sum().reset_index()
             .sort_values("net_revenue", ascending=True)
    )
    fig = px.bar(
        category_rev, x="net_revenue", y="category", orientation="h",
        title="Revenue by Category",
        labels={"category": "Category", "net_revenue": "Net revenue (₱)"}
    )
    st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)
with left:
    top_products = (
        sales.groupby("product_name")["net_revenue"]
             .sum().nlargest(10).reset_index()
             .sort_values("net_revenue", ascending=True)
    )
    fig = px.bar(
        top_products, x="net_revenue", y="product_name", orientation="h",
        title="Top 10 Products by Revenue",
        labels={"product_name": "Product", "net_revenue": "Net revenue (₱)"}
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    region_rev = (
        sales.groupby("region_name", dropna=False)["net_revenue"]
             .sum().nlargest(12).reset_index()
             .sort_values("net_revenue", ascending=True)
    )
    fig = px.bar(
        region_rev, x="net_revenue", y="region_name", orientation="h",
        title="Revenue by Region (Top 12)",
        labels={"region_name": "Region", "net_revenue": "Net revenue (₱)"}
    )
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Customer insights")
customer_spend = (
    sales.groupby("customer_id")["net_revenue"]
         .sum().reset_index(name="customer_spend")
)
fig = px.histogram(
    customer_spend, x="customer_spend", nbins=30,
    title="Distribution of Customer Spend",
    labels={"customer_spend": "Customer spend (₱)", "count": "Customers"}
)
st.plotly_chart(fig, use_container_width=True)

customer_order_counts = (
    sales.groupby("customer_id")["order_id"].nunique()
         .reset_index(name="order_count")
)
customer_order_counts["customer_type"] = np.where(
    customer_order_counts["order_count"] >= 2, "Repeat Customer", "New Customer"
)
repeat_summary = (
    customer_order_counts["customer_type"].value_counts()
    .rename_axis("customer_type").reset_index(name="customers")
)
fig = px.pie(
    repeat_summary, names="customer_type", values="customers",
    title="New vs. Repeat Customers"
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Order outcomes")
status_counts = (
    orders.assign(order_month=orders["order_datetime"].dt.to_period("M").astype("string"))
          .groupby(["order_month", "order_status"])["order_id"].nunique()
          .reset_index(name="orders")
)
status_counts = status_counts[status_counts["order_status"].isin(["Returned", "Cancelled"])]
if not status_counts.empty:
    fig = px.line(
        status_counts, x="order_month", y="orders", color="order_status",
        markers=True, title="Returns and Cancellations by Month",
        labels={"order_month": "Month", "orders": "Unique orders", "order_status": "Status"}
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No Returned or Cancelled orders are present in the loaded orders dataset.")

# -----------------------------
# Detail tables and downloads
# -----------------------------
with st.expander("View KPI breakdown tables"):
    st.write("Monthly revenue")
    st.dataframe(monthly, use_container_width=True)
    st.write("Top products")
    st.dataframe(top_products.sort_values("net_revenue", ascending=False), use_container_width=True)
    st.write("Revenue by category")
    st.dataframe(category_rev.sort_values("net_revenue", ascending=False), use_container_width=True)
    st.write("Revenue by region")
    st.dataframe(region_rev.sort_values("net_revenue", ascending=False), use_container_width=True)
    st.write("New vs. repeat customers")
    st.dataframe(repeat_summary, use_container_width=True)

st.download_button(
    "Download filtered fact table as CSV",
    data=sales.to_csv(index=False).encode("utf-8"),
    file_name="filtered_fact_sales.csv",
    mime="text/csv"
)

st.caption(
    "Method note: New vs. repeat is based on the number of qualifying orders within the "
    "currently selected date range and filters. It is a simple period-based definition, "
    "not necessarily the customer's lifetime first purchase."
)
