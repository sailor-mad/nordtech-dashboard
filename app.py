import streamlit as st
import pandas as pd
import plotly.express as px

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="NordTech Business Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# PREMIUM STYLING
# =========================================================
st.markdown("""
<style>
.block-container {
    max-width: 1500px;
    padding-top: 1.6rem;
    padding-bottom: 2rem;
}

header[data-testid="stHeader"] { height: 0px !important; }

.title {
    font-size: 3.2rem;
    font-weight: 900;
    letter-spacing: -0.04em;
    margin-bottom: 0.3rem;
}

.subtitle {
    font-size: 1.05rem;
    opacity: 0.85;
    margin-bottom: 1.3rem;
}

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 16px;
    margin-bottom: 1rem;
}

.kpi-card {
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.03);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.18);
}

.kpi-label {
    font-size: 0.8rem;
    opacity: 0.7;
    margin-bottom: 6px;
}

.kpi-value {
    font-size: 1.6rem;
    font-weight: 900;
}

.section-title {
    font-size: 1.35rem;
    font-weight: 800;
    margin: 0.4rem 0 0.6rem 0;
}

[data-testid="stPlotlyChart"] > div {
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.06);
    background: rgba(255,255,255,0.02);
}

@media (max-width: 1200px) {
    .kpi-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
st.markdown('<div class="title">📊 NordTech Business Analytics Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Revenue performance, refund analysis and return risk monitoring.</div>', unsafe_allow_html=True)

# =========================================================
# LOAD DATA
# =========================================================
@st.cache_data
def load_data():
    df = pd.read_csv("enriched_data.csv")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Revenue_EUR"] = pd.to_numeric(df["Revenue_EUR"], errors="coerce").fillna(0)
    df["Refund_Amount"] = pd.to_numeric(df["Refund_Amount"], errors="coerce").fillna(0)
    df["Has_Return"] = pd.to_numeric(df["Has_Return"], errors="coerce").fillna(0).astype(int)

    return df

df0 = load_data()

# =========================================================
# SIDEBAR FILTERS
# =========================================================
st.sidebar.header("Filters")

categories = sorted(df0["Product_Category"].unique())
selected_categories = st.sidebar.multiselect(
    "Product Category",
    options=categories,
    default=categories
)

date_range = st.sidebar.date_input(
    "Date Range",
    value=(df0["Date"].min(), df0["Date"].max())
)

df = df0[df0["Product_Category"].isin(selected_categories)]

if len(date_range) == 2:
    start, end = date_range
    df = df[(df["Date"] >= pd.to_datetime(start)) & (df["Date"] <= pd.to_datetime(end))]

# =========================================================
# KPI CALCULATIONS
# =========================================================
total_revenue = df["Revenue_EUR"].sum()
total_refunds = df["Refund_Amount"].sum()
net_revenue = total_revenue - total_refunds
return_rate = df["Has_Return"].mean() * 100 if len(df) else 0
orders = df["Transaction_ID"].nunique()

def eur(x):
    return f"{x:,.2f}".replace(",", " ")

st.markdown(f"""
<div class="kpi-grid">

<div class="kpi-card">
<div class="kpi-label">Total Revenue (€)</div>
<div class="kpi-value">{eur(total_revenue)}</div>
</div>

<div class="kpi-card">
<div class="kpi-label">Refund Amount (€)</div>
<div class="kpi-value">{eur(total_refunds)}</div>
</div>

<div class="kpi-card">
<div class="kpi-label">Net Revenue (€)</div>
<div class="kpi-value">{eur(net_revenue)}</div>
</div>

<div class="kpi-card">
<div class="kpi-label">Return Rate (%)</div>
<div class="kpi-value">{return_rate:.1f}%</div>
</div>

<div class="kpi-card">
<div class="kpi-label">Transactions</div>
<div class="kpi-value">{orders:,}</div>
</div>

</div>
""", unsafe_allow_html=True)

st.divider()

# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3 = st.tabs(["📈 Performance", "⚠️ Risk Analysis", "🧾 Top Issues"])

# =========================================================
# TAB 1 – PERFORMANCE
# =========================================================
with tab1:

    st.markdown('<div class="section-title">Revenue vs Refund Trend</div>', unsafe_allow_html=True)

    daily = df.groupby(df["Date"].dt.date)[["Revenue_EUR", "Refund_Amount"]].sum().reset_index()
    melted = daily.melt(id_vars="Date", var_name="Metric", value_name="Value")

    fig = px.line(melted, x="Date", y="Value", color="Metric", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-title">Revenue by Category</div>', unsafe_allow_html=True)
        cat_rev = df.groupby("Product_Category")["Revenue_EUR"].sum().reset_index()
        fig2 = px.bar(cat_rev, x="Product_Category", y="Revenue_EUR")
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.markdown('<div class="section-title">Refund Distribution</div>', unsafe_allow_html=True)
        cat_ref = df.groupby("Product_Category")["Refund_Amount"].sum().reset_index()
        fig3 = px.pie(cat_ref, names="Product_Category", values="Refund_Amount", hole=0.4)
        st.plotly_chart(fig3, use_container_width=True)

# =========================================================
# TAB 2 – RISK
# =========================================================
with tab2:

    st.markdown('<div class="section-title">Return Risk Over Time</div>', unsafe_allow_html=True)

    risk_time = df.groupby(df["Date"].dt.date)["Has_Return"].mean().reset_index()
    risk_time["Risk_%"] = risk_time["Has_Return"] * 100

    fig4 = px.area(risk_time, x="Date", y="Risk_%")
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown('<div class="section-title">Return Risk by Category</div>', unsafe_allow_html=True)

    risk_cat = df.groupby("Product_Category")["Has_Return"].mean().reset_index()
    risk_cat["Risk_%"] = risk_cat["Has_Return"] * 100

    fig5 = px.bar(
        risk_cat,
        x="Product_Category",
        y="Risk_%",
        color="Risk_%",
        color_continuous_scale="Reds"
    )

    fig5.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig5, use_container_width=True)

# =========================================================
# TAB 3 – TOP ISSUES
# =========================================================
with tab3:

    st.markdown('<div class="section-title">Top Refund Transactions</div>', unsafe_allow_html=True)

    top_ref = df[df["Refund_Amount"] > 0] \
        .sort_values("Refund_Amount", ascending=False) \
        .head(20)

    st.dataframe(top_ref, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown('<div class="section-title">Top Products by Refund (€)</div>', unsafe_allow_html=True)
        prod_ref = df.groupby("Product_Name")["Refund_Amount"].sum().reset_index().sort_values("Refund_Amount", ascending=False).head(10)
        fig6 = px.bar(prod_ref, x="Product_Name", y="Refund_Amount")
        st.plotly_chart(fig6, use_container_width=True)

    with col4:
        st.markdown('<div class="section-title">Top Products by Revenue (€)</div>', unsafe_allow_html=True)
        prod_rev = df.groupby("Product_Name")["Revenue_EUR"].sum().reset_index().sort_values("Revenue_EUR", ascending=False).head(10)
        fig7 = px.bar(prod_rev, x="Product_Name", y="Revenue_EUR")
        st.plotly_chart(fig7, use_container_width=True)
