import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
data_path = os.getenv("CLAIMS_DATA_PATH")

@st.cache_data
def load_claims_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

df = load_claims_data(data_path)

# ---------------- Sidebar Filters ----------------
st.sidebar.header("🔍 Filters")

# Insurance Plan (multi-select)
insurance_options = sorted(df["insurance_plan"].dropna().unique())
insurance_filter = st.sidebar.multiselect(
    "Insurance Plan(s)",
    options=insurance_options,
    default=insurance_options
)

# Provider ID (selectbox)
provider_options = ["All"] + sorted(df["provider_id"].dropna().unique())
provider_filter = st.sidebar.selectbox("Provider ID", provider_options)

# Claim Status (multi-select)
status_options = sorted(df["claim_status"].dropna().unique())
status_filter = st.sidebar.multiselect(
    "Claim Status",
    options=status_options,
    default=status_options
)

# Service Location (multi-select)
location_options = sorted(df["service_location"].dropna().unique())
location_filter = st.sidebar.multiselect(
    "Service Location",
    options=location_options,
    default=location_options
)

# Turnaround Days (slider)
min_days = int(df["turnaround_days"].min())
max_days = int(df["turnaround_days"].max())
turnaround_range = st.sidebar.slider(
    "Turnaround Days",
    min_value=min_days,
    max_value=max_days,
    value=(min_days, max_days)
)

# ---------------- Filter Application ----------------
filtered_df = df[
    (df["insurance_plan"].isin(insurance_filter)) &
    (df["claim_status"].isin(status_filter)) &
    (df["service_location"].isin(location_filter)) &
    (df["turnaround_days"].between(*turnaround_range))
]
if provider_filter != "All":
    filtered_df = filtered_df[filtered_df["provider_id"] == provider_filter]

# ---------------- Dashboard ----------------
st.title("📊 Claims Data Dashboard")
st.write("This dashboard shows summary data, trending, and key metrics.")

def large_numbers(num: float) -> str:
    for unit in ["", "K", "M", "B"]:
        if abs(num) < 1000:
            return f"{num:.1f}{unit}"
        num /= 1000
    return f"{num:.1f}T"

st.subheader("📈 Key Performance Indicators")
col1, col2, col3 = st.columns(3)
col1.metric("Total Claims", f"{len(filtered_df):,}")
col2.metric("Total Paid", f"${large_numbers(filtered_df['paid_amount'].sum())}")
col3.metric("Denied Rate", f"{filtered_df['is_denied'].mean():.2%}")

st.subheader("🔁 Turnaround Time Distribution")
fig = px.histogram(
    filtered_df,
    x="turnaround_days",
    nbins=30,
    title="Distribution of Turnaround Times"
)
fig.update_layout(xaxis_title="Days", yaxis_title="Claim Count")
st.plotly_chart(fig)

with st.expander("👨‍⚕️ Top Providers by Paid Amount"):
    top_prov = (
        filtered_df.groupby("provider_id")["paid_amount"]
        .sum()
        .nlargest(10)
        .reset_index()
        .sort_values("paid_amount", ascending=True)
    )
    fig = px.bar(
        top_prov,
        x="paid_amount",
        y="provider_id",
        orientation="h",
        title="Top 10 Providers by Paid Amount"
    )
    fig.update_traces(
        text=[large_numbers(x) for x in top_prov["paid_amount"]],
        textposition="inside",
        insidetextanchor="start"
    )
    fig.update_layout(
        xaxis_title="Total Paid $",
        xaxis=dict(title=dict(text="Total Paid $", standoff=10), tickformat=".2s"),
        yaxis_title="Provider",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=80, r=40, t=40, b=60),
        showlegend=False
    )
    st.plotly_chart(fig)

st.subheader("❌ Denial Reasons Breakdown")
denials = filtered_df[filtered_df["is_denied"]]
if denials.empty:
    st.info("No denied claims to display.")
else:
    denial_counts = denials["denial_reason"].value_counts().reset_index()
    denial_counts.columns = ["denial_reason", "count"]
    fig = px.pie(
        denial_counts,
        values="count",
        names="denial_reason",
        hole=0.4,
        title="Denial Reasons Distribution"
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig)

st.subheader("📆 Claim Volume Over Time")
filtered_df["procedure_date"] = pd.to_datetime(filtered_df["procedure_date"])
monthly = (
    filtered_df
    .assign(month=lambda x: x["procedure_date"].dt.to_period("M").astype(str))
    .groupby(["month", "claim_status"])
    .size()
    .reset_index(name="count")
)
fig = px.line(monthly, x="month", y="count", color="claim_status", title="Monthly Claim Status Trends")
fig.update_layout(xaxis_title="Month", yaxis_title="Claims")
st.plotly_chart(fig)

st.subheader("🏥 Paid Amount by Service Location")
loc_paid = (
    filtered_df.groupby("service_location")["paid_amount"].sum().reset_index()
)
fig = px.bar(
    loc_paid,
    x="service_location",
    y="paid_amount",
    color="service_location",
    title="Total Paid by Service Location"
)
fig.update_layout(showlegend=False, xaxis_title="Location", yaxis_title="Total Paid ($)")
st.plotly_chart(fig)

st.subheader("💰 Paid by Insurance Plan")
plan_paid = (
    filtered_df.groupby("insurance_plan")["paid_amount"].sum().reset_index()
)
fig = px.treemap(plan_paid, path=["insurance_plan"], values="paid_amount", title="Paid Amount by Insurance Plan")
st.plotly_chart(fig)

st.markdown("\n*Tip: Use the sidebar to filter by plan, provider, location, status, or turnaround days.*")
