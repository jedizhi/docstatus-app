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
    page_title="JGCP Document Expiry Dashboard",
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
    url = "https://docs.google.com/spreadsheets/d/12UG2ofCyDGNl8jUKbuxMZrcTQJHh5G4Ypv_6FUc1luk/edit?gid=1073396090#gid=1073396090"
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
st.sidebar.markdown(
    '<div class="sidebar-header">🎛️ Dashboard Controls</div>',
    unsafe_allow_html=True
)

# -------------------------------------------------
# CLEAN TEXT COLUMNS FIRST (IMPORTANT)
# -------------------------------------------------
TEXT_COLUMNS = [
    "Ownership",
    "Equipment_Type",
    "Registration_Number",
    "Location",
    "Company Name"
]

for col in TEXT_COLUMNS:
    if col in df.columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            #.str.title()
        )

# -------------------------------------------------
# OWNERSHIP FILTER
# -------------------------------------------------
ownership = st.sidebar.radio(
    "📋 Filter By Ownership:",
    ["All", "Rental", "Subcontractor", "Company", "Unknown"],
    help="Select equipment ownership type"
)

# -------------------------------------------------
# Registration_Number FILTER
# -------------------------------------------------
registration_numbers = sorted(
    df["Registration_Number"]
    .dropna()
    .unique()
)

selected_registration = st.sidebar.selectbox(
    "🔍 Registration_Number:",
    ["All"] + registration_numbers,
    help="Filter by specific Registration_Number"
)

# -------------------------------------------------
# Equipment Type FILTER
# -------------------------------------------------
Equipment_Type = sorted(
    df["Equipment_Type"]
    .dropna()
    .unique()
)

selected_equipment = st.sidebar.selectbox(
    "⚙️ Equipment_Type:",
    ["All"] + Equipment_Type,
    help="Filter by Equipment_Type"
)

# -------------------------------------------------
# LOCATION FILTER (MUST COME AFTER CLEANING)
# -------------------------------------------------
if "Location" in df.columns:
    locations = sorted(
        df["Location"]
        .dropna()
        .unique()
    )
else:
    locations = []

selected_location = st.sidebar.selectbox(
    "📍 Location:",
    ["All"] + locations,
    help="Filter by equipment location"
)

# -------------------------------------------------
# Company Name FILTER
# -------------------------------------------------
if "Company_Name" in df.columns:
    company = sorted(
        df["Company_Name"]
        .dropna()
        .unique()
    )
else:
    company = []

selected_company = st.sidebar.selectbox(
    "📰 Company_Name:",
    ["All"] + company,
    help="Filter by Company_Name"
)

# =====================
# APPLY FILTERS
# =====================
filtered_df = df.copy()

# Track whether any filter was actually applied
filters_applied = False

if ownership != "All":
    filtered_df = filtered_df[filtered_df["Ownership"] == ownership]
    filters_applied = True

if selected_registration != "All":
    filtered_df = filtered_df[
        filtered_df["Registration_Number"] == selected_registration
    ]
    filters_applied = True

if selected_equipment != "All":
    filtered_df = filtered_df[
        filtered_df["Equipment_Type"] == selected_equipment
    ]
    filters_applied = True

if selected_location != "All" and "Location" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["Location"] == selected_location
    ]
    filters_applied = True

if selected_company != "All" and "Company_Name" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["Company_Name"] == selected_company]
    filters_applied = True

# Refresh button
if st.sidebar.button("🔄 Refresh Data", type="primary"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("📊 **EQUIPMENT AND VEHICLE DETAILS**")

# ────────────────────────────────────────────────
# Only show table / message if at least one filter was applied
# ────────────────────────────────────────────────
if filters_applied:
    if not filtered_df.empty:
        # Prepare 5-column display
        display_cols = [
            "Equipment_Type",
            "Registration_Number",
            "Location",
            "Company_Name"
        
        ]

        # Only keep columns that exist
        available_cols = [col for col in display_cols if col in filtered_df.columns]

        if available_cols:
            table_df = filtered_df[available_cols].copy()
            table_df.insert(0, "No.", range(1, len(table_df) + 1))

            # Nicer column names
            table_df = table_df.rename(columns={
                "Equipment_Type": "Equipment Type",
                "Registration_Number": "Plate No.",
                "Location": "Location",
                "Company_Name": "Company"
           
            })

            st.sidebar.markdown("**Filtered Results**")
            st.sidebar.dataframe(
                table_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "No.": st.column_config.NumberColumn("No.", width="small"),
                    "Equipment Type": st.column_config.TextColumn("Equipment Type", width="medium"),
                    "Plate No.": st.column_config.TextColumn("Plate No.", width="small"),
                    "Location": st.column_config.TextColumn("Location", width="small"),
                    "Company": st.column_config.TextColumn("Company", width="medium")                  
                }
            )
        else:
            st.sidebar.info("No suitable columns found for display")
    else:
        st.sidebar.warning("No items match the selected filters")
else:
    # No filters applied → do NOT show table or message
    st.sidebar.info("Apply filters to see matching items")

#st.sidebar.markdown("• Real-time document status tracking")
#st.sidebar.markdown("• Interactive filtering options")
#st.sidebar.markdown("• Visual status distribution")
#st.sidebar.markdown("• Detailed expiry management")

# =====================
# APPLY FILTERS
# =====================
# Make a copy of the original data for debugging purposes
original_df = df.copy()

# Clean the data first - remove header rows and invalid entries
df = df.dropna(subset=["Equipment_Type"])
df = df[df["Equipment_Type"].astype(str).str.strip() != ""]
df = df[df["Equipment_Type"].astype(str).str.upper() != "Equipment_Type"]

# Try to find the serial number column
#serial_col = None
#possible_serial_cols = ["S.NO.", "S.No.", "S.No", "Serial No.", "Serial No", "SNo", "Index", "No.", "S. No."]

#for col in possible_serial_cols:
#    if col in df.columns:
#        serial_col = col
#        break

#if serial_col:
#    df = df[df[serial_col].notna() & (df[serial_col].astype(str).str.strip() != "") & (df[serial_col].astype(str).str.upper() != serial_col.upper())]
#    st.sidebar.info(f"📊 Using '{serial_col}' column for equipment counting")
#else:
#    st.sidebar.warning("⚠️ Serial number column not found. Using all rows with Equipment_Type.")

# Clean ownership data and remove header-like entries
df.loc[:, "Ownership"] = df["Ownership"].astype(str).str.strip().str.title()
df = df[df["Ownership"].fillna("").str.upper() != "ownership"]

filtered_df = df.copy()

if ownership != "All":
    filtered_df = filtered_df[filtered_df["Ownership"] == ownership]

if selected_registration != "All":
    filtered_df = filtered_df[filtered_df["Registration_Number"] == selected_registration]

if selected_equipment != "All":
    filtered_df = filtered_df[filtered_df["Equipment_Type"] == selected_equipment]

if selected_location != "All":
    filtered_df = filtered_df[filtered_df["Location"] == selected_location]

if selected_company != "All":
    filtered_df = filtered_df[filtered_df["Company_Name"] == selected_company]

# =====================
# DATE HANDLING & STATUS CLASSIFICATION  
# =====================
exp_date_columns = [
    "Registration_Expiry", "MVPI_Expiry", "Equipment_Insurance_Expiry", 
    "Third_Party_Expiry", "License_Expiry", 
    "Cert_Expiry", "Medical_Insurance_Expiry 1", "Fitness_Expiry 1",
    "Certificate_Expiry", "Medical_Insurance_Expiry 2", "Fitness_Expiry 2"
]

# First, clean N/A and NA values before datetime conversion
for col in exp_date_columns:
    if col in filtered_df.columns:
        filtered_df[col] = filtered_df[col].replace(['N/A', 'NA', 'n/a', 'na'], pd.NaT)
        filtered_df[col] = pd.to_datetime(filtered_df[col], errors="coerce")

today = pd.to_datetime(datetime.today().date())
expiring_today = pd.to_datetime('today').date()  # Use just the date part

def classify_date(expiry_date):
    if pd.isna(expiry_date):
        return "No Date"
    elif expiry_date.date() == expiring_today:  # Compare date parts only
        return "Expiring Today"
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


#st.sidebar.write(f"Debug - Target date: {expiring_today}")
#st.sidebar.write(f"Debug - Target date type: {type(expiring_today)}")


# =====================
# MAIN DASHBOARD
# =====================
st.markdown('<div class="main-header">📆 Heavy Equipment/Vehicles Document Expiry Status - PH III</div>', unsafe_allow_html=True)

# =====================
# BUILD DETAILED LISTS AND COUNT DOCUMENTS CONSISTENTLY
# =====================
expired_details = []
renewal_details = []
expiring_today_details = []

# Counters for total documents in each category
expired_count = 0
renewal_count = 0
expiring_today_count = 0

# Debug section - FIXED to use date comparison
#st.sidebar.write("Debug - Document counts by column:")
expiring_today_by_column = {}

for col in exp_date_columns:
    if col in filtered_df.columns:
        # FIX: Compare date parts only, handle NaT values properly
        expiring_today_count_col = 0
        for _, row in filtered_df.iterrows():
            if pd.notna(row[col]) and row[col].date() == expiring_today:
                expiring_today_count_col += 1
        
        expiring_today_by_column[col] = expiring_today_count_col
        st.sidebar.write(f"• {col}: {expiring_today_count_col} expiring today")

# Process all columns and count documents by status
for _, row in filtered_df.iterrows():
    for doc, status_col in zip(exp_date_columns, status_columns):
        if doc in filtered_df.columns and status_col in filtered_df.columns:
            detail = {
                "Equipment_Type": row["Equipment_Type"],
                "Ownership": row["Ownership"],
                "Company_Name": row["Company_Name"],
                "Registration_Number": row["Registration_Number"],
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
            elif row[status_col] == "Expiring Today":
                expiring_today_details.append(detail)
                expiring_today_count += 1

# Convert to DataFrames
expired_df = pd.DataFrame(expired_details)
renewal_df = pd.DataFrame(renewal_details)
expiring_today_df = pd.DataFrame(expiring_today_details)

#st.sidebar.write("---")
#st.sidebar.write("📊 **Document Count Summary:**")
#st.sidebar.write(f"• Expired Documents: {expired_count}")
#st.sidebar.write(f"• Renewal Documents: {renewal_count}")
#st.sidebar.write(f"• Today Documents: {expiring_today_count}")
#st.sidebar.write(f"• Total Critical Documents: {expired_count + renewal_count + expiring_today_count}")

# Verification check
#total_from_columns = sum(expiring_today_by_column.values())
#st.sidebar.write(f"• Verification - Column sum: {total_from_columns}")

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
        label="⏳ Expiring Today",
        value=expiring_today_count,
        delta=f"2.6%",
        delta_color="off",
        help="Total documents expiring Today"
    )

st.markdown("---")

# Charts row
col1, col2, col3 = st.columns(3)


with col1:
    st.subheader("📈 Document Status Distribution")
    if expired_count > 0 or renewal_count > 0 or expiring_today_count > 0:
        status_data = {
            "Status": [],
            "Count": [],
            "Color": []
        }
        
        if expired_count > 0:
            status_data["Status"].append("Expired")
            status_data["Count"].append(expired_count)
            status_data["Color"].append("#fae102")
        
        if renewal_count > 0:
            status_data["Status"].append("For Renewal")
            status_data["Count"].append(renewal_count)
            status_data["Color"].append("#fa0202")
        
        if expiring_today_count > 0:
            status_data["Status"].append("Expiring Today")
            status_data["Count"].append(expiring_today_count)
            status_data["Color"].append("#fa7602")
        
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
    st.subheader("🏗️ Equipment_Type Distribution")
    if not filtered_df.empty:
        equipment_counts = filtered_df["Equipment_Type"].value_counts().reset_index()
        equipment_counts.columns = ["Equipment_Type", "Count"]
        
        fig_equipment = px.bar(
            equipment_counts,
            x="Equipment_Type",
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
# EXPIRING TODAY DOCUMENTS SECTION
# =====================
st.markdown("---")
col1 = st.columns(1)
with col1[0]:
    st.subheader("⏳ Expiring Today's Documents")
    st.markdown(f"Total Expiring Today Documents (with placeholder date {today}): **{today}**")
    if not expiring_today_df.empty:
        today_display = expiring_today_df.copy()
        today_display["Expiry Date"] = pd.to_datetime(today_display["Expiry Date"], errors="coerce").dt.strftime("%b-%d-%Y")
        today_display.index = today_display.index + 1
        with st.expander(f"📋 View {len(expiring_today_df)} Expiring Today Document Details"):
            st.dataframe(today_display, use_container_width=True)
    else:
        st.success("🎉 No documents expiring today!")

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
            owner_expiring_today = len(expiring_today_df[expiring_today_df["Ownership"] == owner]) if not expiring_today_df.empty else 0
            owner_equipment = len(filtered_df[filtered_df["Ownership"] == owner])
            
            ownership_summary.append({
                "Ownership": owner,
                "Total Equipment": owner_equipment,
                "Expired Documents": owner_expired,
                "Renewal Documents": owner_renewal,
                "Expiring Today Documents": owner_expiring_today
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
                doc_expiring_today = len(expiring_today_df[expiring_today_df["Document Type"] == doc_type]) if not expiring_today_df.empty else 0
                
                doc_summary.append({
                    "Document Type": doc_type,
                    "Expired": doc_expired,
                    "For Renewal": doc_renewal,
                    "Expiring Today": doc_expiring_today,
                    "Total Critical": doc_expired + doc_renewal + doc_expiring_today
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
                        "Registration": row["Registration_Number"]
                    })
        
        if not renewal_df.empty:
            for _, row in renewal_df.iterrows():
                if pd.notna(row["Expiry Date"]):
                    timeline_data.append({
                        "Date": row["Expiry Date"],
                        "Status": "For Renewal",
                        "Document Type": row["Document Type"],
                        "Registration": row["Registration_Number"]
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
