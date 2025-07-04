import streamlit as st
import pandas as pd
import plotly.express as px
import os
from openai import OpenAI
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
data_path = os.getenv("CLAIMS_DATA_PATH")

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

@st.cache_data
def load_claims_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["procedure_date", "submission_date"])

df = load_claims_data(data_path)

st.set_page_config(page_title="Claims Dashboard", layout="wide")

# functions
def is_valid_query(filter_str: str, valid_columns: list) -> bool:
    """
    Check if all column names used in the filter string exist in valid_columns.
    """
    for col in valid_columns:
        filter_str = filter_str.replace(f"`{col}`", "").replace(col, "")
    # If any alphabetical characters remain, suspicious tokens exist
    return filter_str.strip().replace(" ", "").isalnum() == False

def large_numbers(num: float) -> str:
    for unit in ["", "K", "M", "B"]:
        if abs(num) < 1000:
            return f"{num:.1f}{unit}"
        num /= 1000
    return f"{num:.1f}T"


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
sidebar_filtered_df = df[
    (df["insurance_plan"].isin(insurance_filter)) &
    (df["claim_status"].isin(status_filter)) &
    (df["service_location"].isin(location_filter)) &
    (df["turnaround_days"].between(*turnaround_range))
]
if provider_filter != "All":
    sidebar_filtered_df = sidebar_filtered_df[sidebar_filtered_df["provider_id"] == provider_filter]

# ---------------- Dashboard ----------------
st.title("📊 Claims Data Dashboard")
st.write("This dashboard shows summary data, trending, and key metrics.")
st.subheader("Ask for a chart or filter your data (ex. 'Show denied claims from last month.')")

filtered_df = sidebar_filtered_df

#initialize session state for chatbot questions
if "user_question" not in st.session_state:
    st.session_state["user_question"] = ""

#display text input tied to session state

user_question = st.text_input(
    "Results will display as a table by default. You can also request a bar or line graph.",
    value=st.session_state["user_question"],
    key="user_question"
)

# Add clear button here
if st.button("Clear Chatbot Filter"):
    st.session_state["user_question"] = ""
    st.experimental_rerun()

if user_question:
    with st.spinner("Processing your questions..."):

        #system instructions for chatbot with synonyms to enhance NQL comprehension
        system_prompt = (
            "You are a data assistant for a healthcare claims dashboard. "
            "The dataset columns are: claim_id, patient_id, age, gender, procedure_code, diagnosis_code, "
            "procedure_date, submission_date, turnaround_days, insurance_plan, claim_status, is_denied, "
            "is_outlier, denial_reason, billed_amount, paid_amount, service_location, provider_id. "

            "Map synonyms appropriately: "
            "'women', 'female', 'ladies' -> gender == 'Female'; "
            "'men', 'male', 'gentlemen' -> gender == 'Male'; "
            "'older than', 'over', 'above' -> '>'; "
            "'younger than', 'under', 'below' -> '<'; "
            "'doctor', 'provider' -> provider_id; "
            "'location', 'site', 'facility' -> service_location; "
            "'paid', 'payment', 'reimbursed' -> paid_amount; "
            "'billed', 'charge', 'charged' -> billed_amount; "
            "'diagnosis', 'dx' -> diagnosis_code; "
            "'procedure', 'proc' -> procedure_code; "
            "'insurance', 'payer', 'plan' -> insurance_plan; "
            "'private insurance', 'private payer', 'commercial insurance' -> insurance_plan != 'Medicare' and insurance_plan != 'Medicaid'; "
            "'status', 'claim status' -> claim_status; "
            "'turnaround', 'processing time' -> turnaround_days; "
            "'date of service', 'visit date', 'procedure date' -> procedure_date; "
            "'submission date', 'submitted on' -> submission_date; "
            "'denial', 'denied reason' -> denial_reason; "
            "'id', 'identifier' -> patient_id, claim_id. "

            "Use these synonyms to translate natural language into accurate pandas query filters. "
            "Return JSON with:\n"
            "- 'filter': a pandas query string if filtering is needed (else return '').\n"
            "- 'chart': 'bar', 'line', or 'table'.\n"
            "- 'x': column for x-axis if applicable.\n"
            "- 'y': column for y-axis if applicable.\n"
            "If unsure, prefer 'table'. Do not include comments or code, just JSON."
                )

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_question}
                ]
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            st.success("Query processed successfully!")

            #apply filters if appropriate
            if result.get("filter"):
                filter_query = result["filter"]
                valid_columns = df.columns.tolist()
                if is_valid_query(filter_query, valid_columns):
                    try:
                        filtered_df = sidebar_filtered_df.query(filter_query)
                    except Exception as e:
                        st.error(f"Error applying filter: {e}")
                        filtered_df = sidebar_filtered_df
                else:
                    st.warning("The chatbot generated a filter referencing invalid columns; ignoring filter.")
                    filtered_df = sidebar_filtered_df
            #display requested chart or table
            if result.get("chart") == "table" or "chart" not in result:
                st.dataframe(filtered_df)
            elif result.get("chart") in ["bar", "line"]:
                chart_type = result["chart"]
                x_col = result.get("x")
                y_col = result.get("y")

                if x_col and y_col:
                    if chart_type == "bar":
                        fig = px.bar(filtered_df, x=x_col, y=y_col, title = f"{y_col} by {x_col}")
                    elif chart_type == "line":
                        fig = px.line(filtered_df, x=x_col, y=y_col, title = f"{y_col} by {x_col}")

                    st.plotly_chart(fig, use_container_width=True)
                
                else:
                    st.warning("Chart type requested but missing 'x' or 'y' in the response.")
                    st.dataframe(filtered_df)

            else:
                st.dataframe(filtered_df)
        except json.JSONDecodeError:
            st.error("Could not parse the model's response as JSON.")
            st.code(result_text, language="json")
        except Exception as ex:
            st.error(f"An error occurred: {ex}")
                                     
st.caption("Powered by OpenAI")


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
