import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="NordTech Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 NordTech Sales Dashboard")
st.caption("Sales performance and return risk analysis.")

@st.cache_data
def load_data():
    df = pd.read_csv("enriched_data.csv")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df

df = load_data()

# -----------------------
# Sidebar filters
# -----------------------
st.sidebar.header("🔎 Filtri")

min_d = df["Date"].min()
max_d = df["Date"].max()

date_range = st.sidebar.date_input(
    "Datumu diapazons",
    value=(min_d.date(), max_d.date())
)

start_date, end_date = date_range
df = df[(df["Date"] >= pd.to_datetime(start_date)) &
        (df["Date"] <= pd.to_datetime(end_date))]

categories = df["Product_Category"].unique()
selected_cat = st.sidebar.multiselect(
    "Produkta kategorija",
    options=categories,
    default=categories
)

df = df[df["Product_Category"].isin(selected_cat)]

# -----------------------
# KPI
# -----------------------
col1, col2, col3 = st.columns(3)

orders = df["Transaction_ID"].nunique()
revenue = df["Revenue_EUR"].sum()
return_rate = df["Has_Return"].mean() * 100

col1.metric("Pasūtījumi", f"{orders}")
col2.metric("Ieņēmumi (€)", f"{revenue:,.0f}")
col3.metric("Atgriešanas %", f"{return_rate:.1f}%")

st.divider()

# -----------------------
# Revenue over time
# -----------------------
st.subheader("📈 Ieņēmumi laikā")

daily = df.groupby(df["Date"].dt.date)["Revenue_EUR"].sum().reset_index()

fig1 = px.line(daily, x="Date", y="Revenue_EUR", markers=True)
st.plotly_chart(fig1, use_container_width=True)

# -----------------------
# Revenue by category
# -----------------------
st.subheader("📊 Ieņēmumi pēc kategorijas")

cat_rev = df.groupby("Product_Category")["Revenue_EUR"].sum().reset_index()
fig2 = px.bar(cat_rev, x="Product_Category", y="Revenue_EUR")
st.plotly_chart(fig2, use_container_width=True)

# -----------------------
# Return risk by category
# -----------------------
st.subheader("⚠️ Atgriešanas risks pēc kategorijas")

ret_cat = df.groupby("Product_Category")["Has_Return"].mean().reset_index()
ret_cat["Has_Return"] = ret_cat["Has_Return"] * 100

fig3 = px.bar(ret_cat, x="Product_Category", y="Has_Return")
fig3.update_layout(yaxis_title="Return rate (%)")

st.plotly_chart(fig3, use_container_width=True)

st.caption("✅ Publicēts tikai ar kursa mācību datiem.")
