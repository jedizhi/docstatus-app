import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection


# =====================
# PAGE CONFIG
# =====================
st.set_page_config(
    page_title="JGCP-HE Document Expiry Dashboard",
    page_icon="📆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================
# CUSTOM CSS
# =====================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .sidebar-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# =====================
# CONNECT TO GOOGLE SHEETS
# =====================
@st.cache_data(ttl=0)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/12UG2ofCyDGNl8jUKbuxMZrcTQJHh5G4Ypv_6FUc1luk/edit?pli=1&gid=1073396090#gid=1073396090"
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# =====================
# SIDEBAR CONTROLS
# =====================
st.sidebar.markdown('<div class="sidebar-header">🎛️ Dashboard Controls</div>', unsafe_allow_html=True)

# Clean ownership data
#df["Ownership"] = df["Ownership"].astype(str).str.strip().str.title()

# Ownership filter
ownership = st.sidebar.radio(
    "📋 Filter By Ownership:",
    ["All", "Rental", "Subcontractor","Company","Unknown"],
    help="Select equipment ownership type"
)

# Registration number filter
registration_numbers = sorted(df["Registration Number"].dropna().astype(str).unique())
selected_registration = st.sidebar.selectbox(
    "🔍 Registration Number:",
    ["All"] + registration_numbers,
    help="Filter by specific registration number"
)

# Equipment type filter
equipment_types = sorted(df["Equipment Type"].dropna().astype(str).unique())
selected_equipment = st.sidebar.selectbox(
    "⚙️ Equipment Type:",
    ["All"] + equipment_types,
    help="Filter by equipment type"
)

# =====================
# APPLY FILTERS
# =====================

filtered_df = df.copy()

if ownership != "All":
    filtered_df = filtered_df[filtered_df["Ownership"] == ownership]

if selected_registration != "All":
    filtered_df = filtered_df[filtered_df["Registration Number"] == selected_registration]

if selected_equipment != "All":
    filtered_df = filtered_df[filtered_df["Equipment Type"] == selected_equipment]

# ✅ LOCATION FILTER MUST BE HERE
if selected_location != "All":
    filtered_df = filtered_df[filtered_df["Location"] == selected_location]
# Clean Location column
if "Location" in df.columns:
    df["Location"] = (
        df["Location"]
        .astype(str)
        .str.strip()
        .str.title()
    )

# Location filter
locations = sorted(
    df["Location"]
    .dropna()
    .astype(str)
    .str.strip()
    .str.title()
    .unique()
)

selected_location = st.sidebar.selectbox(
    "📍 Location:",
    ["All"] + locations,
    help="Filter by equipment location"
)

if selected_location != "All" and "Location" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["Location"].str.strip().str.title() == selected_location]

# Refresh button
if st.sidebar.button("🔄 Refresh Data", type="primary"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("📊 **Dashboard Features:**")
st.sidebar.markdown("• Real-time document status tracking")
st.sidebar.markdown("• Interactive filtering options")
st.sidebar.markdown("• Visual status distribution")
st.sidebar.markdown("• Detailed expiry management")

# =====================
# APPLY FILTERS
# =====================
# Make a copy of the original data for debugging purposes
original_df = df.copy()

# Clean the data first - remove header rows and invalid entries
df = df.dropna(subset=["Equipment Type"])
df = df[df["Equipment Type"].astype(str).str.strip() != ""]
df = df[df["Equipment Type"].astype(str).str.lower() != "equipment type"]

# Try to find the serial number column
serial_col = None
possible_serial_cols = ["S.NO.", "S.No.", "S.No", "Serial No.", "Serial No", "SNo", "Index", "No.", "S. No."]

for col in possible_serial_cols:
    if col in df.columns:
        serial_col = col
        break

if serial_col:
    df = df[df[serial_col].notna() & (df[serial_col].astype(str).str.strip() != "") & (df[serial_col].astype(str).str.lower() != serial_col.lower())]
    st.sidebar.info(f"📊 Using '{serial_col}' column for equipment counting")
else:
    st.sidebar.warning("⚠️ Serial number column not found. Using all rows with equipment type.")

# Clean ownership data and remove header-like entries
df.loc[:, "Ownership"] = df["Ownership"].astype(str).str.strip().str.title()
df = df[df["Ownership"].fillna("").str.lower() != "ownership"]

filtered_df = df.copy()

if ownership != "All":
    filtered_df = filtered_df[filtered_df["Ownership"] == ownership]

if selected_registration != "All":
    filtered_df = filtered_df[filtered_df["Registration Number"] == selected_registration]

if selected_equipment != "All":
    filtered_df = filtered_df[filtered_df["Equipment Type"] == selected_equipment]

# =====================
# DATE HANDLING & STATUS CLASSIFICATION  
# =====================
exp_date_columns = [
    "Registration Expiry", "MVPI Expiry", "Equipment Insurance Exp", 
    "Third Party Expiry", "License Expiry", 
    "Cert Expiry", "Medical Insurance Expiry", "Fitness Expiry"
]

# First, clean N/A and NA values before datetime conversion
for col in exp_date_columns:
    if col in filtered_df.columns:
        filtered_df[col] = filtered_df[col].replace(['N/A', 'NA', 'n/a', 'na'], pd.NaT)
        filtered_df[col] = pd.to_datetime(filtered_df[col], errors="coerce")

today = pd.to_datetime(datetime.today().date())
pending_target_date = pd.to_datetime("2024-01-01").date()  # Use just the date part

def classify_date(expiry_date):
    if pd.isna(expiry_date):
        return "No Date"
    elif expiry_date.date() == pending_target_date:  # Compare date parts only
        return "Pending"
    elif expiry_date < today:
        return "Expired"
    elif expiry_date <= today + timedelta(days=15):
        return "For Renewal"
    else:
        return "Valid"

# Add status columns
for col in exp_date_columns:
    if col in filtered_df.columns:
        filtered_df[f"{col}_Status"] = filtered_df[col].apply(classify_date)

status_columns = [f"{col}_Status" for col in exp_date_columns if col in filtered_df.columns]


st.sidebar.write(f"Debug - Target date: {pending_target_date}")
st.sidebar.write(f"Debug - Target date type: {type(pending_target_date)}")


# =====================
# MAIN DASHBOARD
# =====================
st.markdown('<div class="main-header">📆 JGCP-HE Document Expiry Status - PH III</div>', unsafe_allow_html=True)

# =====================
# BUILD DETAILED LISTS AND COUNT DOCUMENTS CONSISTENTLY
# =====================
expired_details = []
renewal_details = []
pending_details = []

# Counters for total documents in each category
expired_count = 0
renewal_count = 0
pending_count = 0

# Debug section - FIXED to use date comparison
st.sidebar.write("Debug - Document counts by column:")
pending_by_column = {}

for col in exp_date_columns:
    if col in filtered_df.columns:
        # FIX: Compare date parts only, handle NaT values properly
        pending_count_col = 0
        for _, row in filtered_df.iterrows():
            if pd.notna(row[col]) and row[col].date() == pending_target_date:
                pending_count_col += 1
        
        pending_by_column[col] = pending_count_col
        st.sidebar.write(f"• {col}: {pending_count_col} pending")

# Process all columns and count documents by status
for _, row in filtered_df.iterrows():
    for doc, status_col in zip(exp_date_columns, status_columns):
        if doc in filtered_df.columns and status_col in filtered_df.columns:
            detail = {
                "Equipment Type": row["Equipment Type"],
                "Ownership": row["Ownership"],
                "Company Name": row["Company Name"],
                "Registration Number": row["Registration Number"],
                "Document Type": doc,
                "Expiry Date": row[doc]
            }
            
            # Count each document by its status
            if row[status_col] == "Expired":
                expired_details.append(detail)
                expired_count += 1
            elif row[status_col] == "For Renewal":
                renewal_details.append(detail)
                renewal_count += 1
            elif row[status_col] == "Pending":
                pending_details.append(detail)
                pending_count += 1

# Convert to DataFrames
expired_df = pd.DataFrame(expired_details)
renewal_df = pd.DataFrame(renewal_details)
pending_df = pd.DataFrame(pending_details)

st.sidebar.write("---")
st.sidebar.write("📊 **Document Count Summary:**")
st.sidebar.write(f"• Expired Documents: {expired_count}")
st.sidebar.write(f"• Renewal Documents: {renewal_count}")
st.sidebar.write(f"• Pending Documents: {pending_count}")
st.sidebar.write(f"• Total Critical Documents: {expired_count + renewal_count + pending_count}")

# Verification check
total_from_columns = sum(pending_by_column.values())
st.sidebar.write(f"• Verification - Column sum: {total_from_columns}")

# =====================
# ROW 1: OVERVIEW METRICS & PIE CHARTS
# =====================
st.markdown("### 📊 Dashboard Overview")

# Metrics row
col1, col2, col3, col4 = st.columns(4)

total_equipment = len(filtered_df)

with col1:
    st.metric(
        label="📦 Total Equipment",
        value=total_equipment,
        help="Total number of equipment"
    )

with col2:
    st.metric(
        label="❌ Expired",
        value=expired_count,
        delta=f"0.7%",
        delta_color="inverse",
        help="Total expired documents"
    )

with col3:
    st.metric(
        label="⚠️ For Renewal",
        value=renewal_count,
        delta=f"1.6%",
        delta_color="off",
        help="Total documents for renewal"
    )

with col4:
    st.metric(
        label="⏳ Pending",
        value=pending_count,
        delta=f"2.6%",
        delta_color="off",
        help="Total documents with placeholder dates 1-Jan-2024"
    )

st.markdown("---")

# Charts row
col1, col2, col3 = st.columns(3)


with col1:
    st.subheader("📈 Document Status Distribution")
    if expired_count > 0 or renewal_count > 0 or pending_count > 0:
        status_data = {
            "Status": [],
            "Count": [],
            "Color": []
        }
        
        if expired_count > 0:
            status_data["Status"].append("Expired")
            status_data["Count"].append(expired_count)
            status_data["Color"].append("#e74c3c")
        
        if renewal_count > 0:
            status_data["Status"].append("For Renewal")
            status_data["Count"].append(renewal_count)
            status_data["Color"].append("#f39c12")
        
        if pending_count > 0:
            status_data["Status"].append("Pending")
            status_data["Count"].append(pending_count)
            status_data["Color"].append("#95a5a6")
        
        fig_status = px.pie(
            values=status_data["Count"],
            names=status_data["Status"],
            title="Overall Document Status",
            color_discrete_sequence=status_data["Color"],
            height=550
        )
        fig_status.update_traces(
            textposition='inside',
            textinfo='value+label',
            texttemplate='%{label}<br>%{value}'
        )
        st.plotly_chart(fig_status, use_container_width=True)
    else:
        st.info("No critical documents found.")

with col2:
    st.subheader("🏗️ Equipment Type Distribution")
    if not filtered_df.empty:
        equipment_counts = filtered_df["Equipment Type"].value_counts().reset_index()
        equipment_counts.columns = ["Equipment Type", "Count"]
        
        fig_equipment = px.bar(
            equipment_counts,
            x="Equipment Type",
            y="Count",
            text="Count",
            title="Equipment Distribution",
            color="Count",
            color_continuous_scale="Blues",
            height=550
        )
        fig_equipment.update_traces(textposition="outside")
        fig_equipment.update_layout(xaxis_tickangle=-45, showlegend=False)
        st.plotly_chart(fig_equipment, use_container_width=True)

with col3:
    st.subheader("📍 Equipment by Location")
    if not filtered_df.empty:
        location_counts = filtered_df["Location"].value_counts().reset_index()
        location_counts.columns = ["Location", "Count"]

        fig_location = px.bar(
            location_counts,
            x="Location",
            y="Count",
            text="Count",
            title="Equipment Distribution by Location",
            color="Count",
            color_continuous_scale="Greens",
            height=550
        )
        fig_location.update_traces(textposition="outside")
        fig_location.update_layout(xaxis_tickangle=-45, showlegend=False)
        st.plotly_chart(fig_location, use_container_width=True)
    else:
        st.info("No data available for selected filters.")

# =====================
# ROW 2: EXPIRED & RENEWAL CHARTS
# =====================
st.markdown("---")
st.markdown("### 🚨 Critical Status Analysis")

col1, col2 = st.columns(2)

with col1:
    st.subheader("❌ Expired Documents by Type")
    if not expired_df.empty:
        expired_counts = expired_df["Document Type"].value_counts().reset_index()
        expired_counts.columns = ["Document Type", "Count"]

        fig_expired = px.bar(
            expired_counts,
            x="Document Type",
            y="Count",
            text="Count",
            title=f"Expired Documents ({ownership})",
            color="Count",
            color_continuous_scale="Reds",
            height=550
        )
        fig_expired.update_traces(textposition="outside", textfont_size=12)
        fig_expired.update_layout(xaxis_tickangle=-45, showlegend=False)
        st.plotly_chart(fig_expired, use_container_width=True)
        
        with st.expander(f"📋 View {len(expired_df)} Expired Document Details"):
            expired_display = expired_df.copy()
            if not expired_display.empty:
                expired_display["Expiry Date"] = pd.to_datetime(expired_display["Expiry Date"], errors="coerce").dt.strftime("%b-%d-%Y")
                expired_display.index = expired_display.index + 1
                st.dataframe(expired_display, use_container_width=True)
    else:
        st.success("🎉 No expired documents!")

with col2:
    st.subheader("⚠️ For Renewal Documents by Type")
    if not renewal_df.empty:
        renewal_counts = renewal_df["Document Type"].value_counts().reset_index()
        renewal_counts.columns = ["Document Type", "Count"]

        fig_renewal = px.bar(
            renewal_counts,
            x="Document Type",
            y="Count",
            text="Count",
            title=f"For Renewal Documents ({ownership})",
            color="Count",
            color_continuous_scale="Oranges",
            height=550
        )
        fig_renewal.update_traces(textposition="outside", textfont_size=12)
        fig_renewal.update_layout(xaxis_tickangle=-45, showlegend=False)
        st.plotly_chart(fig_renewal, use_container_width=True)
        
        with st.expander(f"📋 View {len(renewal_df)} Renewal Document Details"):
            renewal_display = renewal_df.copy()
            if not renewal_display.empty:
                renewal_display["Expiry Date"] = pd.to_datetime(renewal_display["Expiry Date"], errors="coerce").dt.strftime("%b-%d-%Y")
                renewal_display.index = renewal_display.index + 1
                st.dataframe(renewal_display, use_container_width=True)
    else:
        st.success("🎉 No documents for renewal!")

# =====================
# PENDING DOCUMENTS SECTION
# =====================
st.markdown("---")
col1 = st.columns(1)
with col1[0]:
    st.subheader("⏳ Pending Documents with Placeholder Dates")
    st.markdown(f"Total Pending Documents (with placeholder date {pending_target_date}): **{pending_count}**")
    if not pending_df.empty:
        pending_display = pending_df.copy()
        pending_display["Expiry Date"] = pd.to_datetime(pending_display["Expiry Date"], errors="coerce").dt.strftime("%b-%d-%Y")
        pending_display.index = pending_display.index + 1
        with st.expander(f"📋 View {len(pending_df)} Pending Document Details"):
            st.dataframe(pending_display, use_container_width=True)
    else:
        st.success("🎉 No pending documents!")

# =====================
# ADDITIONAL INSIGHTS
# =====================
st.markdown("---")
st.markdown("### 📋 Detailed Analysis")

tab1, tab2, tab3 = st.tabs(["🏢 By Ownership", "📄 By Document Type", "📊 Timeline Analysis"])

with tab1:
    st.subheader("Ownership Breakdown")
    if not filtered_df.empty:
        ownership_summary = []
        for owner in filtered_df["Ownership"].unique():
            owner_expired = len(expired_df[expired_df["Ownership"] == owner]) if not expired_df.empty else 0
            owner_renewal = len(renewal_df[renewal_df["Ownership"] == owner]) if not renewal_df.empty else 0
            owner_pending = len(pending_df[pending_df["Ownership"] == owner]) if not pending_df.empty else 0
            owner_equipment = len(filtered_df[filtered_df["Ownership"] == owner])
            
            ownership_summary.append({
                "Ownership": owner,
                "Total Equipment": owner_equipment,
                "Expired Documents": owner_expired,
                "Renewal Documents": owner_renewal,
                "Pending Documents": owner_pending
            })
        
        ownership_df = pd.DataFrame(ownership_summary)
        if not ownership_df.empty:
            ownership_df.index = ownership_df.index + 1
            st.dataframe(ownership_df, use_container_width=True)

with tab2:
    st.subheader("Document Type Analysis")
    if not filtered_df.empty:
        doc_summary = []
        for doc_type in exp_date_columns:
            if doc_type in filtered_df.columns:
                doc_expired = len(expired_df[expired_df["Document Type"] == doc_type]) if not expired_df.empty else 0
                doc_renewal = len(renewal_df[renewal_df["Document Type"] == doc_type]) if not renewal_df.empty else 0
                doc_pending = len(pending_df[pending_df["Document Type"] == doc_type]) if not pending_df.empty else 0
                
                doc_summary.append({
                    "Document Type": doc_type,
                    "Expired": doc_expired,
                    "For Renewal": doc_renewal,
                    "Pending": doc_pending,
                    "Total Critical": doc_expired + doc_renewal + doc_pending
                })
        
        doc_summary_df = pd.DataFrame(doc_summary)
        if not doc_summary_df.empty:
            doc_summary_df.index = doc_summary_df.index + 1
            st.dataframe(doc_summary_df, use_container_width=True)

with tab3:
    st.subheader("Expiry Timeline")
    if not expired_df.empty or not renewal_df.empty:
        timeline_data = []
        
        if not expired_df.empty:
            for _, row in expired_df.iterrows():
                if pd.notna(row["Expiry Date"]):
                    timeline_data.append({
                        "Date": row["Expiry Date"],
                        "Status": "Expired",
                        "Document Type": row["Document Type"],
                        "Registration": row["Registration Number"]
                    })
        
        if not renewal_df.empty:
            for _, row in renewal_df.iterrows():
                if pd.notna(row["Expiry Date"]):
                    timeline_data.append({
                        "Date": row["Expiry Date"],
                        "Status": "For Renewal",
                        "Document Type": row["Document Type"],
                        "Registration": row["Registration Number"]
                    })
        
        if timeline_data:
            timeline_df = pd.DataFrame(timeline_data)
            timeline_df["Date"] = pd.to_datetime(timeline_df["Date"])
            timeline_df = timeline_df.sort_values("Date")
            
            fig_timeline = px.scatter(
                timeline_df,
                x="Date",
                y="Document Type",
                color="Status",
                hover_data=["Registration"],
                title="Document Expiry Timeline",
                color_discrete_map={"Expired": "#e74c3c", "For Renewal": "#f39c12"},
                height=400
            )
            fig_timeline.update_layout(xaxis_title="Expiry Date", yaxis_title="Document Type")
            st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info("No timeline data available for current filters.")

# =====================
# FOOTER
# =====================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #7f8c8d; font-size: 0.9rem;'>
        📊 JGCP-HE Document Management Dashboard | Last Updated: {} | 
        Showing {} equipment items
    </div>
    """.format(
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        len(filtered_df)
    ),
    unsafe_allow_html=True
)
