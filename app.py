import streamlit as st
import pandas as pd
import plotly.express as px

# =============================
# CONFIG
# =============================
st.set_page_config(
    page_title="NordTech Biznesa Operāciju Panelis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================
# PREMIUM STYLING (widescreen)
# =============================
st.markdown(
    """
    <style>
      .block-container {
        max-width: 1480px;
        padding-top: 1.6rem;
        padding-bottom: 2.0rem;
      }
      [data-testid="stSidebar"] .block-container {
        padding-top: 1.1rem;
      }
      header[data-testid="stHeader"] { height: 0px !important; }

      .nl-title {
        font-size: 3.05rem;
        font-weight: 900;
        letter-spacing: -0.035em;
        line-height: 1.05;
        margin: 0 0 0.30rem 0;
      }
      .nl-subtitle {
        opacity: 0.88;
        font-size: 1.05rem;
        margin: 0 0 0.35rem 0;
      }
      .nl-verified {
        color: #2ecc71;
        font-weight: 700;
        font-size: 0.92rem;
        margin: 0 0 1.1rem 0;
      }

      .kpi-grid {
        display: grid;
        grid-template-columns: repeat(6, minmax(0, 1fr));
        gap: 14px;
        margin-top: 0.25rem;
        margin-bottom: 0.65rem;
      }
      .kpi-card {
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(255,255,255,0.03);
        border-radius: 16px;
        padding: 14px 14px 12px 14px;
        box-shadow: 0 10px 26px rgba(0,0,0,0.18);
      }
      .kpi-label {
        font-size: 0.83rem;
        opacity: 0.74;
        margin-bottom: 6px;
      }
      .kpi-value {
        font-size: 1.52rem;
        font-weight: 900;
        letter-spacing: -0.02em;
      }
      .kpi-note {
        font-size: 0.78rem;
        opacity: 0.62;
        margin-top: 6px;
      }
      .pill {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.01em;
        border: 1px solid rgba(255,255,255,0.10);
        background: rgba(255,255,255,0.05);
      }

      .section-h {
        font-size: 1.32rem;
        font-weight: 820;
        letter-spacing: -0.01em;
        margin: 0.2rem 0 0.45rem 0;
      }
      .muted {
        opacity: 0.75;
        font-size: 0.92rem;
      }

      div[data-testid="stTabs"] { margin-top: 0.75rem; }

      [data-testid="stPlotlyChart"] > div {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.06);
        background: rgba(255,255,255,0.02);
      }

      @media (max-width: 1350px) {
        .kpi-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      }
      @media (max-width: 850px) {
        .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================
# HEADER
# =============================
st.markdown('<div class="nl-title">📊 NordTech Biznesa Operāciju Panelis</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="nl-subtitle">Ieņēmumi, atgriezumi un atgriešanas risks — filtrējams panelis ar trendiem un TOP problēmām.</div>',
    unsafe_allow_html=True
)
st.markdown('<div class="nl-verified">✔ Publicēts tikai ar kursa mācību datiem (bez paroļu / API atslēgām)</div>', unsafe_allow_html=True)

# =============================
# LOAD DATA
# =============================
@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    # required columns
    required = [
        "Transaction_ID", "Date", "Product_Category", "Product_Name",
        "Revenue_EUR", "Refund_Amount", "Has_Return"
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"CSV trūkst kolonnas: {missing}")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Revenue_EUR"] = pd.to_numeric(df["Revenue_EUR"], errors="coerce").fillna(0)
    df["Refund_Amount"] = pd.to_numeric(df["Refund_Amount"], errors="coerce").fillna(0)
    df["Has_Return"] = pd.to_numeric(df["Has_Return"], errors="coerce").fillna(0).astype(int)

    df["Product_Category"] = df["Product_Category"].astype(str)
    df["Product_Name"] = df["Product_Name"].astype(str)

    return df


DATA_PATH = "enriched_data.csv"
try:
    df0 = load_data(DATA_PATH)
except FileNotFoundError:
    st.error(f"❌ Nevar atrast failu `{DATA_PATH}` repo saknē.")
    st.stop()
except ValueError as e:
    st.error(f"❌ Datu struktūras kļūda: {e}")
    st.stop()

if df0.empty:
    st.warning("Datu fails ielādēts, bet tas ir tukšs.")
    st.stop()

# =============================
# SIDEBAR CONTROLS
# =============================
st.sidebar.header("Iestatījumi")

cats = sorted(df0["Product_Category"].dropna().unique().tolist())
selected_cats = st.sidebar.multiselect("Produktu kategorija:", options=cats, default=cats)

min_d = df0["Date"].min()
max_d = df0["Date"].max()

if pd.isna(min_d) or pd.isna(max_d):
    st.sidebar.warning("Datumu kolonna nav korekti nolasīta (`Date`).")
    date_range = None
else:
    date_range = st.sidebar.date_input("Periods (no – līdz):", value=(min_d.date(), max_d.date()))

st.sidebar.divider()
risk_threshold = st.sidebar.slider("Riska slieksnis brīdinājumam (%)", min_value=1, max_value=30, value=8)
show_data = st.sidebar.checkbox("Rādīt datu tabulu (Dati tabā)", value=False)

# Apply filters
df = df0.copy()
df = df[df["Product_Category"].isin(selected_cats)]

if date_range:
    start_date, end_date = date_range
    df = df[(df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))]

# =============================
# KPI COMPUTE
# =============================
total_revenue = float(df["Revenue_EUR"].sum())
total_refunds = float(df["Refund_Amount"].sum())
net_revenue = total_revenue - total_refunds
orders = int(df["Transaction_ID"].nunique())
return_rate = float(df["Has_Return"].mean() * 100) if len(df) else 0.0
refund_rate = float((total_refunds / total_revenue) * 100) if total_revenue > 0 else 0.0

def eur(x: float) -> str:
    return f"{x:,.2f}".replace(",", " ")

def risk_level(rr: float) -> str:
    if rr >= 12:
        return "HIGH"
    if rr >= 7:
        return "MEDIUM"
    return "LOW"

lvl = risk_level(return_rate)

pill_html = {
    "LOW": '<span class="pill" style="color:#2ecc71;">LOW RISK</span>',
    "MEDIUM": '<span class="pill" style="color:#f1c40f;">MEDIUM RISK</span>',
    "HIGH": '<span class="pill" style="color:#e74c3c;">HIGH RISK</span>',
}[lvl]

# Alert
if return_rate >= risk_threshold:
    st.warning(f"⚠️ Atgriešanas risks **{return_rate:.1f}%** pārsniedz slieksni **{risk_threshold}%** šajā filtrā.", icon="⚠️")

st.markdown(
    f"""
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Kopējie ieņēmumi (€)</div>
        <div class="kpi-value">{eur(total_revenue)}</div>
        <div class="kpi-note">Filtrētais periods</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">Atgriezumu summa (€)</div>
        <div class="kpi-value">{eur(total_refunds)}</div>
        <div class="kpi-note">Refund_Amount summa</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">Net ieņēmumi (€)</div>
        <div class="kpi-value">{eur(net_revenue)}</div>
        <div class="kpi-note">Revenue − Refund</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">Atgriešanas %</div>
        <div class="kpi-value">{return_rate:.1f}%</div>
        <div class="kpi-note">{pill_html}</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">Refund/Revenue %</div>
        <div class="kpi-value">{refund_rate:.2f}%</div>
        <div class="kpi-note">Refund kā daļa no ieņēmumiem</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">Darījumi</div>
        <div class="kpi-value">{orders:,}</div>
        <div class="kpi-note">Transaction_ID unikālie</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# =============================
# TABS
# =============================
tab1, tab2, tab3, tab4 = st.tabs(["📈 Dinamika", "⚠️ Riski", "🧾 TOP problēmas", "📦 Dati"])

# =============================
# TAB 1: Dynamics
# =============================
with tab1:
    st.markdown('<div class="section-h">Ieņēmumu un atgriezumu dinamika</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">Divas metrikas vienā grafikā, lai ātri redzētu, kad pieaug refundi.</div>', unsafe_allow_html=True)

    tmp = df.dropna(subset=["Date"]).copy()
    tmp["day"] = tmp["Date"].dt.date

    daily = tmp.groupby("day", as_index=False)[["Revenue_EUR", "Refund_Amount"]].sum()

    long = daily.melt(
        id_vars="day",
        value_vars=["Revenue_EUR", "Refund_Amount"],
        var_name="Metric",
        value_name="Value",
    )
    fig = px.line(long, x="day", y="Value", color="Metric", markers=True)
    fig.update_layout(xaxis_title="Datums", yaxis_title="€", legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="section-h">Ieņēmumi pēc kategorijas</div>', unsafe_allow_html=True)
        cat_rev = (
            df.groupby("Product_Category", as_index=False)["Revenue_EUR"]
            .sum()
            .sort_values("Revenue_EUR", ascending=False)
        )
        fig2 = px.bar(cat_rev, x="Product_Category", y="Revenue_EUR")
        fig2.update_layout(xaxis_title="Kategorija", yaxis_title="€")
        st.plotly_chart(fig2, use_container_width=True)

    with c2:
        st.markdown('<div class="section-h">Atgriezumu sadalījums pēc kategorijas</div>', unsafe_allow_html=True)
        cat_ref = (
            df.groupby("Product_Category", as_index=False)["Refund_Amount"]
            .sum()
            .sort_values("Refund_Amount", ascending=False)
        )
        if cat_ref["Refund_Amount"].sum() > 0:
            fig3 = px.pie(cat_ref, names="Product_Category", values="Refund_Amount", hole=0.40)
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Šajā filtrā nav atgriezumu (Refund_Amount = 0).")

# =============================
# TAB 2: Risk
# =============================
with tab2:
    st.markdown('<div class="section-h">Atgriešanas risks laika gaitā</div>', unsafe_allow_html=True)

    tmp = df.dropna(subset=["Date"]).copy()
    tmp["day"] = tmp["Date"].dt.date

    daily_risk = tmp.groupby("day", as_index=False)["Has_Return"].mean()
    daily_risk["Return_Rate_%"] = daily_risk["Has_Return"] * 100

    fig_risk = px.area(daily_risk, x="day", y="Return_Rate_%")
    fig_risk.update_layout(xaxis_title="Datums", yaxis_title="Return rate (%)")
    st.plotly_chart(fig_risk, use_container_width=True)

    st.markdown('<div class="section-h">Atgriešanas risks pēc kategorijas (heat)</div>', unsafe_allow_html=True)

    risk = df.groupby("Product_Category", as_index=False)["Has_Return"].mean()
    risk["Return_Rate_%"] = risk["Has_Return"] * 100
    risk = risk.sort_values("Return_Rate_%", ascending=False)

    fig_bar = px.bar(
        risk,
        x="Product_Category",
        y="Return_Rate_%",
        color="Return_Rate_%",
        color_continuous_scale="Reds",
    )
    fig_bar.update_layout(
        xaxis_title="Kategorija",
        yaxis_title="Return rate (%)",
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown('<div class="section-h">Return vs No Return (pēc darījumu skaita)</div>', unsafe_allow_html=True)
    ret_counts = df["Has_Return"].value_counts().rename_axis("Has_Return").reset_index(name="count")
    ret_counts["Label"] = ret_counts["Has_Return"].map({0: "Nav atgriezts", 1: "Atgriezts"})
    fig_pie = px.pie(ret_counts, names="Label", values="count", hole=0.40)
    st.plotly_chart(fig_pie, use_container_width=True)

# =============================
# TAB 3: TOP issues
# =============================
with tab3:
    st.markdown('<div class="section-h">Top problemātiskie darījumi (pēc lielākā atgriezuma €)</div>', unsafe_allow_html=True)

    top_refunds = (
        df[df["Refund_Amount"] > 0]
        .sort_values("Refund_Amount", ascending=False)
        .loc[:, ["Transaction_ID", "Date", "Product_Category", "Product_Name", "Revenue_EUR", "Refund_Amount", "Has_Return"]]
        .head(20)
    )

    if top_refunds.empty:
        st.info("Šajā filtrā nav darījumu ar atgriezumiem (Refund_Amount > 0).")
    else:
        st.dataframe(top_refunds, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        st.markdown('<div class="section-h">Top 10 produkti pēc atgriezumiem (€)</div>', unsafe_allow_html=True)
        prod_ref = (
            df.groupby("Product_Name", as_index=False)["Refund_Amount"]
            .sum()
            .sort_values("Refund_Amount", ascending=False)
            .head(10)
        )
        fig6 = px.bar(prod_ref, x="Product_Name", y="Refund_Amount")
        fig6.update_layout(xaxis_title="Produkts", yaxis_title="€")
        st.plotly_chart(fig6, use_container_width=True)

    with c4:
        st.markdown('<div class="section-h">Top 10 produkti pēc ieņēmumiem (€)</div>', unsafe_allow_html=True)
        prod_rev = (
            df.groupby("Product_Name", as_index=False)["Revenue_EUR"]
            .sum()
            .sort_values("Revenue_EUR", ascending=False)
            .head(10)
        )
        fig7 = px.bar(prod_rev, x="Product_Name", y="Revenue_EUR")
        fig7.update_layout(xaxis_title="Produkts", yaxis_title="€")
        st.plotly_chart(fig7, use_container_width=True)

# =============================
# TAB 4: Data
# =============================
with tab4:
    st.markdown('<div class="section-h">Dati (filtrēti)</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">Šeit vari pārbaudīt, ka filtri strādā korekti un lejupielādēt CSV.</div>', unsafe_allow_html=True)

    if show_data:
        st.dataframe(df.head(300), use_container_width=True)
    else:
        st.info("Ieslēdz sidebarā “Rādīt datu tabulu (Dati tabā)”, ja gribi redzēt preview.")

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Lejupielādēt filtrētos datus (CSV)",
        data=csv_bytes,
        file_name="nordtech_filtered.csv",
        mime="text/csv",
    )

st.caption("✅ Publicēts tikai ar kursa mācību datiem. Bez paroļu / API atslēgām.")
