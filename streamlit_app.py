import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# Connect to google spreadsheets
url = "https://docs.google.com/spreadsheets/d/1oGcvcMnjVTynDW-VjL58ssUaVVrlqWwt8AKtyLiDykk/edit?gid=0#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

# Load data
# df = pd.read_csv("SHC Heavy Equipment Master Log.csv")
df = conn.read(spreadsheet = url)
#st.dataframe(df)

st.title("📆 JGCP-HE Document Expiry Status - PH III")

# Convert date columns to datetime (remove TR Sticker Expiry Date)
exp_date_column = [
    "Registration Expiry", "MVPI Expiry", "Insurance expiry", 
     "Third Party Expiry","License Expiry", "Cert Expiry", "Medical Insurance Expiry", "Fitness Expiry"
]
df[exp_date_column] = df[exp_date_column].apply(pd.to_datetime, errors="coerce")

# Today's date
today = pd.to_datetime(datetime.today().date())

# Function to classify expiry status
def classify_date(expiry_date):
    if pd.isna(expiry_date):
        return "No Date"
    elif expiry_date < today:
        return "Expired"
    elif expiry_date <= today + timedelta(days=15):
        return "For Renewal"
    else:
        return "Valid"

# Apply status classification
for col in exp_date_column:
    df[f"{col}_Status"] = df[col].apply(classify_date)

# Create list of status columns
status_columns = [f"{col}_Status" for col in exp_date_column]

# Searchable dropdown for registration number
registration_numbers = sorted(df["Registration Number"].dropna().astype(str).unique())
selected_registration = st.selectbox("🔍 Search Registration Number", ["All"] + registration_numbers)

if selected_registration != "All":
    filtered_df = df[df["Registration Number"] == selected_registration]
else:
    filtered_df = df

# Prepare details for Expired and For Renewal, now including Expiry Date
expired_details = []
renewal_details = []

for idx, row in filtered_df.iterrows():
    for doc, status_col, date_col in zip(exp_date_column, status_columns, exp_date_column):
        if row[status_col] == "Expired":
            expired_details.append({
                "Equipment Type": row["Equipment Type"], 
                "Registration Number": row["Registration Number"], 
                "Document Type": doc,
                "Expiry Date": row[date_col]
            })
        elif row[status_col] == "For Renewal":
            renewal_details.append({
                "Equipment Type": row["Equipment Type"], 
                "Registration Number": row["Registration Number"], 
                "Document Type": doc,
                "Expiry Date": row[date_col]
            })

expired_details = pd.DataFrame(expired_details)
renewal_details = pd.DataFrame(renewal_details)

# ========================
# INTERACTIVE CHART: EXPIRED
# ========================
st.subheader("📌 Expired Documents by Type")
if not expired_details.empty:
    expired_counts = expired_details["Document Type"].value_counts().reset_index()
    expired_counts.columns = ["Document Type", "Count"]

    fig_expired = px.bar(
        expired_counts,
        x="Document Type",
        y="Count",
        text="Count",
        title="Expired Documents by Type"
    )
    fig_expired.update_traces(textposition="outside")
    fig_expired.update_layout(xaxis_tickangle=-45)

    st.plotly_chart(fig_expired, use_container_width=True)

    clicked_doc_type_expired = st.selectbox("🔍 Search Expired Document Type", ["All"] + list(expired_counts["Document Type"]))
    if clicked_doc_type_expired != "All":
        st.dataframe(expired_details[expired_details["Document Type"] == clicked_doc_type_expired])
    else:
        st.dataframe(expired_details)

# ========================
# INTERACTIVE CHART: FOR RENEWAL
# ========================
st.subheader("📌 For Renewal Documents by Type")
if not renewal_details.empty:
    renewal_counts = renewal_details["Document Type"].value_counts().reset_index()
    renewal_counts.columns = ["Document Type", "Count"]

    fig_renewal = px.bar(
        renewal_counts,
        x="Document Type",
        y="Count",
        text="Count",
        title="For Renewal Documents by Type"
    )
    fig_renewal.update_traces(textposition="outside")
    fig_renewal.update_layout(xaxis_tickangle=-45)

    st.plotly_chart(fig_renewal, use_container_width=True)

    clicked_doc_type_renewal = st.selectbox("🔍 Search Renewal Document Type", ["All"] + list(renewal_counts["Document Type"]))
    if clicked_doc_type_renewal != "All":
        st.dataframe(renewal_details[renewal_details["Document Type"] == clicked_doc_type_renewal])
    else:
        st.dataframe(renewal_details)
