import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------
# Page setup (smuki un profesionāli)
# -----------------------------
st.set_page_config(
    page_title="NordTech Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 NordTech Sales Dashboard")
st.caption("Sales performance, customer behavior and risk signals (returns & support).")

# -----------------------------
# Data loading (ātrāk + drošāk)
# -----------------------------
@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Mēģinām automātiski atpazīt datuma kolonnas (ja ir)
    for col in ["order_date", "date", "created_at", "timestamp"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df


DATA_PATH = "enriched_data.csv"  # ieteicamais variants
# DATA_PATH = "enriched_data.csv"     # ja turi tajā pašā mapē

try:
    df = load_data(DATA_PATH)
except FileNotFoundError:
    st.error(
        f"❌ Nevar atrast failu: `{DATA_PATH}`.\n\n"
        "Pārbaudi, vai tas ir repo un pareizā mapē. Ieteikums: ieliec `data/enriched_data.csv`."
    )
    st.stop()

if df.empty:
    st.warning("Datu fails ir ielādēts, bet tas ir tukšs.")
    st.stop()

# -----------------------------
# Helper: atrod iespējamos kolonu nosaukumus
# -----------------------------
def first_existing(cols):
    for c in cols:
        if c in df.columns:
            return c
    return None

col_date = first_existing(["order_date", "date", "created_at"])
col_revenue = first_existing(["revenue", "sales", "total_revenue", "order_value"])
col_orders = first_existing(["order_id", "orders", "order_number"])
col_channel = first_existing(["channel", "traffic_source", "source"])
col_device = first_existing(["device", "device_type"])
col_returned = first_existing(["is_returned", "returned", "return_flag"])
col_ticket = first_existing(["has_ticket", "ticket_flag", "ticket_created"])

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("🔎 Filtri")

# Datumu filtrs (ja ir datuma kolonna)
if col_date:
    min_d = df[col_date].min()
    max_d = df[col_date].max()
    if pd.notna(min_d) and pd.notna(max_d):
        date_range = st.sidebar.date_input(
            "Datumu diapazons",
            value=(min_d.date(), max_d.date()),
            min_value=min_d.date(),
            max_value=max_d.date(),
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            df = df[(df[col_date] >= pd.to_datetime(start_date)) & (df[col_date] <= pd.to_datetime(end_date))]
else:
    st.sidebar.info("Nav atrasta datuma kolonna — datumu filtrs nav pieejams.")

# Channel filter
if col_channel:
    channels = sorted([c for c in df[col_channel].dropna().unique()])
    selected_channels = st.sidebar.multiselect("Kanāls", options=channels, default=channels)
    if selected_channels:
        df = df[df[col_channel].isin(selected_channels)]

# Device filter
if col_device:
    devices = sorted([d for d in df[col_device].dropna().unique()])
    selected_devices = st.sidebar.multiselect("Ierīce", options=devices, default=devices)
    if selected_devices:
        df = df[df[col_device].isin(selected_devices)]

st.sidebar.divider()
show_raw = st.sidebar.checkbox("Rādīt datu tabulu", value=False)

# -----------------------------
# KPI row
# -----------------------------
def safe_nunique(series):
    try:
        return int(series.nunique())
    except Exception:
        return None

def safe_sum(series):
    try:
        return float(series.sum())
    except Exception:
        return None

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

# Orders
orders_val = safe_nunique(df[col_orders]) if col_orders else len(df)
kpi1.metric("Pasūtījumi", f"{orders_val:,}".replace(",", " "))

# Revenue
if col_revenue:
    revenue_val = safe_sum(df[col_revenue])
    kpi2.metric("Ieņēmumi", f"{revenue_val:,.0f}".replace(",", " "))
else:
    kpi2.metric("Ieņēmumi", "—")

# Return rate
if col_returned:
    # pieņemam, ka True/1 = returned
    ret_rate = (df[col_returned].astype(float).mean() * 100) if len(df) else 0
    kpi3.metric("Atgriešanas %", f"{ret_rate:.1f}%")
else:
    kpi3.metric("Atgriešanas %", "—")

# Ticket rate
if col_ticket:
    t_rate = (df[col_ticket].astype(float).mean() * 100) if len(df) else 0
    kpi4.metric("Ticket %", f"{t_rate:.1f}%")
else:
    kpi4.metric("Ticket %", "—")

st.divider()

# -----------------------------
# Charts
# -----------------------------
left, right = st.columns(2)

# 1) Time trend (Revenue or Orders)
with left:
    st.subheader("📈 Trends laikā")
    if col_date:
        agg = df.copy()
        agg["_day"] = agg[col_date].dt.date
        if col_revenue:
            daily = agg.groupby("_day", as_index=False)[col_revenue].sum()
            fig = px.line(daily, x="_day", y=col_revenue, markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            daily = agg.groupby("_day", as_index=False).size().rename(columns={"size": "orders"})
            fig = px.line(daily, x="_day", y="orders", markers=True)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Lai rādītu trendu, nepieciešama datuma kolonna (piem. order_date).")

# 2) Channel breakdown
with right:
    st.subheader("📊 Kanāli")
    if col_channel:
        if col_revenue:
            ch = df.groupby(col_channel, as_index=False)[col_revenue].sum().sort_values(col_revenue, ascending=False)
            fig = px.bar(ch, x=col_channel, y=col_revenue)
            st.plotly_chart(fig, use_container_width=True)
        else:
            ch = df.groupby(col_channel, as_index=False).size().rename(columns={"size": "orders"}).sort_values("orders", ascending=False)
            fig = px.bar(ch, x=col_channel, y="orders")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nav atrasta kolonna `channel` (vai līdzīga).")

# 3) Return / Ticket risk by channel (ja ir flagi)
st.subheader("⚠️ Riski pēc kanāla")
c1, c2 = st.columns(2)

with c1:
    if col_channel and col_returned:
        tmp = df.copy()
        tmp[col_returned] = tmp[col_returned].astype(float)
        rr = tmp.groupby(col_channel, as_index=False)[col_returned].mean()
        rr[col_returned] = rr[col_returned] * 100
        rr = rr.sort_values(col_returned, ascending=False)
        fig = px.bar(rr, x=col_channel, y=col_returned)
        fig.update_layout(yaxis_title="Return rate (%)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Lai rādītu return risku, vajag `channel` + `is_returned` (vai līdzīgu).")

with c2:
    if col_channel and col_ticket:
        tmp = df.copy()
        tmp[col_ticket] = tmp[col_ticket].astype(float)
        tr = tmp.groupby(col_channel, as_index=False)[col_ticket].mean()
        tr[col_ticket] = tr[col_ticket] * 100
        tr = tr.sort_values(col_ticket, ascending=False)
        fig = px.bar(tr, x=col_channel, y=col_ticket)
        fig.update_layout(yaxis_title="Ticket rate (%)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Lai rādītu ticket risku, vajag `channel` + `has_ticket` (vai līdzīgu).")

# -----------------------------
# Data preview + download
# -----------------------------
if show_raw:
    st.subheader("🧾 Datu priekšskatījums")
    st.dataframe(df.head(200), use_container_width=True)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Lejupielādēt filtrētos datus (CSV)",
        data=csv_bytes,
        file_name="nordtech_filtered.csv",
        mime="text/csv",
    )

# Footer
st.caption("✅ Publicēts tikai ar kursa mācību datiem. Bez paroļu / API atslēgām.")
