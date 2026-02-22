import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(
    page_title="NordTech Biznesa Operāciju Panelis",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🛡️ NordTech Biznesa Operāciju Panelis")
st.caption("Kopējie ieņēmumi, atgriezumi un atgriešanas risks (filtrējams).")

# -----------------------------
# Load data
# -----------------------------
@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    # Drošībai: ja Refund_Amount ir tukšs/teksts
    df["Refund_Amount"] = pd.to_numeric(df["Refund_Amount"], errors="coerce").fillna(0)
    df["Revenue_EUR"] = pd.to_numeric(df["Revenue_EUR"], errors="coerce").fillna(0)
    # Has_Return var būt 0/1, True/False
    df["Has_Return"] = pd.to_numeric(df["Has_Return"], errors="coerce").fillna(0).astype(int)
    return df

DATA_PATH = "enriched_data.csv"  # tev repo saknē
df0 = load_data(DATA_PATH)

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Iestatījumi")

# Category filter
cats = sorted(df0["Product_Category"].dropna().unique().tolist())
selected_cats = st.sidebar.multiselect("Produktu kategorija:", options=cats, default=cats)

# Date range filter
min_d = df0["Date"].min()
max_d = df0["Date"].max()
date_range = st.sidebar.date_input("Periods (no – līdz):", value=(min_d.date(), max_d.date()))

start_date, end_date = date_range
df = df0.copy()
df = df[df["Product_Category"].isin(selected_cats)]
df = df[(df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))]

# -----------------------------
# KPIs
# -----------------------------
total_revenue = float(df["Revenue_EUR"].sum())
total_refunds = float(df["Refund_Amount"].sum())
net_revenue = total_revenue - total_refunds
orders = int(df["Transaction_ID"].nunique())
return_rate = float(df["Has_Return"].mean() * 100) if len(df) else 0.0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Kopējie ieņēmumi (€)", f"{total_revenue:,.2f}")
k2.metric("Atgriezumu summa (€)", f"{total_refunds:,.2f}")
k3.metric("Net ieņēmumi (€)", f"{net_revenue:,.2f}")
k4.metric("Atgriešanas %", f"{return_rate:.1f}%")
k5.metric("Darījumi", f"{orders:,}".replace(",", " "))

st.divider()

# -----------------------------
# Tabs (ļoti profesionāli izskatās)
# -----------------------------
tab1, tab2, tab3 = st.tabs(["📈 Dinamika", "⚠️ Riski", "🧾 Problēmu TOP"])

# -----------------------------
# TAB 1: Trends
# -----------------------------
with tab1:
    st.subheader("Ieņēmumu un atgriezumu dinamika")

    daily = (
        df.assign(day=df["Date"].dt.date)
          .groupby("day", as_index=False)[["Revenue_EUR", "Refund_Amount"]]
          .sum()
    )

    long = daily.melt(id_vars="day", value_vars=["Revenue_EUR", "Refund_Amount"],
                      var_name="Metric", value_name="Value")

    fig = px.line(long, x="day", y="Value", color="Metric", markers=True)
    fig.update_layout(xaxis_title="Datums", yaxis_title="€")
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Ieņēmumi pēc kategorijas")
        cat_rev = df.groupby("Product_Category", as_index=False)["Revenue_EUR"].sum().sort_values("Revenue_EUR", ascending=False)
        fig2 = px.bar(cat_rev, x="Product_Category", y="Revenue_EUR")
        fig2.update_layout(xaxis_title="Kategorija", yaxis_title="€")
        st.plotly_chart(fig2, use_container_width=True)

    with c2:
        st.subheader("Atgriezumu sadalījums pēc kategorijas")
        cat_ref = df.groupby("Product_Category", as_index=False)["Refund_Amount"].sum().sort_values("Refund_Amount", ascending=False)
        # pīrāgs izskatās līdzīgi kā tajā studenta panelī
        fig3 = px.pie(cat_ref, names="Product_Category", values="Refund_Amount", hole=0.35)
        st.plotly_chart(fig3, use_container_width=True)

# -----------------------------
# TAB 2: Risks
# -----------------------------
with tab2:
    st.subheader("Atgriešanas risks pēc kategorijas")

    risk = df.groupby("Product_Category", as_index=False)["Has_Return"].mean()
    risk["Return_Rate_%"] = risk["Has_Return"] * 100
    risk = risk.sort_values("Return_Rate_%", ascending=False)

    fig4 = px.bar(risk, x="Product_Category", y="Return_Rate_%")
    fig4.update_layout(xaxis_title="Kategorija", yaxis_title="Return rate (%)")
    st.plotly_chart(fig4, use_container_width=True)

    st.subheader("Return vs No Return (pēc darījumu skaita)")
    ret_counts = df["Has_Return"].value_counts().rename_axis("Has_Return").reset_index(name="count")
    ret_counts["Label"] = ret_counts["Has_Return"].map({0: "Nav atgriezts", 1: "Atgriezts"})
    fig5 = px.pie(ret_counts, names="Label", values="count", hole=0.35)
    st.plotly_chart(fig5, use_container_width=True)

# -----------------------------
# TAB 3: Top problematic
# -----------------------------
with tab3:
    st.subheader("Top problemātiskie darījumi (pēc lielākā atgriezuma €)")

    top_refunds = (
        df[df["Refund_Amount"] > 0]
        .sort_values("Refund_Amount", ascending=False)
        .loc[:, ["Transaction_ID", "Date", "Product_Category", "Product_Name", "Refund_Amount", "Revenue_EUR"]]
        .head(15)
    )

    st.dataframe(top_refunds, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("Top 10 produkti pēc atgriezumiem (€)")
        prod_ref = (
            df.groupby("Product_Name", as_index=False)["Refund_Amount"].sum()
            .sort_values("Refund_Amount", ascending=False)
            .head(10)
        )
        fig6 = px.bar(prod_ref, x="Product_Name", y="Refund_Amount")
        fig6.update_layout(xaxis_title="Produkts", yaxis_title="€")
        st.plotly_chart(fig6, use_container_width=True)

    with c4:
        st.subheader("Top 10 produkti pēc ieņēmumiem (€)")
        prod_rev = (
            df.groupby("Product_Name", as_index=False)["Revenue_EUR"].sum()
            .sort_values("Revenue_EUR", ascending=False)
            .head(10)
        )
        fig7 = px.bar(prod_rev, x="Product_Name", y="Revenue_EUR")
        fig7.update_layout(xaxis_title="Produkts", yaxis_title="€")
        st.plotly_chart(fig7, use_container_width=True)

st.caption("✅ Publicēts tikai ar kursa mācību datiem. Bez paroļu / API atslēgām.")
