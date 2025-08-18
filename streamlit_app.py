import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# =====================
# CONNECT TO GOOGLE SHEETS
# =====================
url = "https://docs.google.com/spreadsheets/d/1oQuWmbOjjbK8emvpP7eD9cH3q5YgTl_A/edit?gid=1073396090#gid=1073396090"
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(spreadsheet=url)

st.title("📆 JGCP-HE Document Expiry Status - PH III")

# =====================
# DATE HANDLING
# =====================
exp_date_column = [
    "Registration Expiry", "MVPI Expiry", "Insurance expiry", 
    "Third Party Expiry", "License Expiry", 
    "Cert Expiry", "Medical Insurance Expiry", "Fitness Expiry"
]
df[exp_date_column] = df[exp_date_column].apply(pd.to_datetime, errors="coerce")
today = pd.to_datetime(datetime.today().date())

def classify_date(expiry_date):
    if pd.isna(expiry_date):
        return "No Date"
    elif expiry_date < today:
        return "Expired"
    elif expiry_date <= today + timedelta(days=15):
        return "For Renewal"
    else:
        return "Valid"

# Add status columns
for col in exp_date_column:
    df[f"{col}_Status"] = df[col].apply(classify_date)

status_columns = [f"{col}_Status" for col in exp_date_column]

# =====================
# FILTER BY REGISTRATION NUMBER
# =====================
registration_numbers = sorted(df["Registration Number"].dropna().astype(str).unique())
selected_registration = st.selectbox("🔍 Search Registration Number", ["All"] + registration_numbers)

if selected_registration != "All":
    filtered_df = df[df["Registration Number"] == selected_registration]
else:
    filtered_df = df

# =====================
# BUILD EXPIRED & RENEWAL LISTS
# =====================
expired_details = []
renewal_details = []

for _, row in filtered_df.iterrows():
    for doc, status_col in zip(exp_date_column, status_columns):
        if row[status_col] == "Expired":
            expired_details.append({
                "Equipment Type": row["Equipment Type"],
                "Company_Subontractor": row["Company_Subcontractor"],  
                "Registration Number": row["Registration Number"], 
                "Document Type": doc,
                "Expiry Date": row[doc]
            })
        elif row[status_col] == "For Renewal":
            renewal_details.append({
                "Equipment Type": row["Equipment Type"],
                "Company_Subontractor": row["Company_Subcontractor"], 
                "Registration Number": row["Registration Number"], 
                "Document Type": doc,
                "Expiry Date": row[doc]
            })

expired_details = pd.DataFrame(expired_details)
renewal_details = pd.DataFrame(renewal_details)

# Format dates for display
for df_details in [expired_details, renewal_details]:
    if not df_details.empty:
        df_details["Expiry Date"] = pd.to_datetime(df_details["Expiry Date"], errors="coerce").dt.strftime("%d-%b-%Y")

# =====================
# CHART: EXPIRED
# =====================
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

    clicked_doc_type_expired = st.selectbox(
        "🔍 Search Expired Document Type", ["All"] + list(expired_counts["Document Type"])
    )
    if clicked_doc_type_expired != "All":
        st.dataframe(expired_details[expired_details["Document Type"] == clicked_doc_type_expired])
    else:
        st.dataframe(expired_details)

# =====================
# CHART: FOR RENEWAL
# =====================
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

    clicked_doc_type_renewal = st.selectbox(
        "🔍 Search Renewal Document Type", ["All"] + list(renewal_counts["Document Type"])
    )
    if clicked_doc_type_renewal != "All":
        st.dataframe(renewal_details[renewal_details["Document Type"] == clicked_doc_type_renewal])
    else:
        st.dataframe(renewal_details)
