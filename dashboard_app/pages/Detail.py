import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

data_path = os.getenv("CLAIMS_DATA_PATH")

@st.cache_data
def load_claims_data(path):
    return pd.read_csv(path, parse_dates=["procedure_date", "submission_date"])

df = load_claims_data(data_path)

st.title("🩺 Claims Detail Explorer")
st.write("Filter, sort, and explore individual claims. Download for ad-hoc analysis.")

# Navigation button to go back to Home
if st.button("⬅️ Back to Dashboard"):
    st.switch_page("Home.py")

# Initialize session state for filters if not already set
for filter_key, default in {
    "providers": df["provider_id"].unique().tolist(),
    "insurance_plans": df["insurance_plan"].unique().tolist(),
    "service_locations": df["service_location"].unique().tolist(),
    "claim_status": df["claim_status"].unique().tolist()
}.items():
    if filter_key not in st.session_state:
        st.session_state[filter_key] = default

# Sidebar filters
with st.sidebar:
    st.header("Filter Claims")
    date_range = st.date_input(
        "Procedure Date Range",
        [df["procedure_date"].min(), df["procedure_date"].max()]
    )

    providers = st.multiselect(
        "Provider",
        options=df["provider_id"].unique(),
        default=st.session_state["providers"],
        key="providers"
    )

    insurance_plans = st.multiselect(
        "Insurance Plan",
        options=df["insurance_plan"].unique(),
        default=st.session_state["insurance_plans"],
        key="insurance_plans"
    )

    service_locations = st.multiselect(
        "Service Location",
        options=df["service_location"].unique(),
        default=st.session_state["service_locations"],
        key="service_locations"
    )

    claim_status = st.multiselect(
        "Claim Status",
        options=df["claim_status"].unique(),
        default=st.session_state["claim_status"],
        key="claim_status"
    )

# Apply filters
filtered_df = df[
    (df["procedure_date"] >= pd.to_datetime(date_range[0])) &
    (df["procedure_date"] <= pd.to_datetime(date_range[1])) &
    (df["provider_id"].isin(providers)) &
    (df["insurance_plan"].isin(insurance_plans)) &
    (df["service_location"].isin(service_locations)) &
    (df["claim_status"].isin(claim_status))
]

st.subheader(f"Filtered Claims ({len(filtered_df):,})")
st.dataframe(filtered_df, use_container_width=True)

# Download filtered data
st.download_button(
    label="📥 Download Filtered Claims as CSV",
    data=filtered_df.to_csv(index=False).encode('utf-8'),
    file_name="filtered_claims.csv",
    mime="text/csv"
)

# Optional Paid vs Denied by Provider visual
viz_df = (
    filtered_df.groupby(["provider_id", "claim_status"])["paid_amount"]
    .sum()
    .reset_index()
)

if not viz_df.empty:
    st.subheader("💡 Paid vs Denied by Provider")
    fig = px.bar(
        viz_df,
        x="provider_id",
        y="paid_amount",
        color="claim_status",
        barmode="group",
        title="Paid vs Denied Amount by Provider"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No Paid or Denied claims available for the selected filters.")

