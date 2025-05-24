import streamlit as st
import pandas as pd
from datetime import date, datetime
import os

# --- File paths ---
CUSTOMERS_CSV = "customers.csv"
VISITS_CSV = "visits.csv"

# --- Load customers data ---
try:
    customers = pd.read_csv(CUSTOMERS_CSV)
except Exception as e:
    st.error(f"Error loading customers.csv: {e}")
    st.stop()

# --- Load or create visits data ---
if os.path.exists(VISITS_CSV):
    visits = pd.read_csv(VISITS_CSV)
    if 'Visit Date' in visits.columns:
        visits['Visit Date'] = pd.to_datetime(visits['Visit Date'], errors='coerce')
else:
    visits = pd.DataFrame(columns=['Agent Name', 'Trading Name', 'Area', 'Visit Date'])

tab1, tab2 = st.tabs(["➕ Log a Visit", "📊 Dashboard"])

# --- Tab 1: Agent Visit Entry ---
with tab1:
    st.header("Agent: Log a New Visit")

    with st.form("visit_entry_form"):
        agent_name = st.selectbox("Agent Name", customers["Agent Name"].dropna().unique())
        # Trading Names only for this agent
        agent_customers = customers[customers["Agent Name"] == agent_name]
        trading_name = st.selectbox("Trading Name", agent_customers["Trading Name"].dropna().unique())
        area = agent_customers[agent_customers["Trading Name"] == trading_name]["Area"].values[0]
        st.text_input("Area", area, disabled=True)
        visit_date = st.date_input("Visit Date", date.today())
        submit_visit = st.form_submit_button("Add Visit")

    if submit_visit:
        new_visit = pd.DataFrame([{
            "Agent Name": agent_name,
            "Trading Name": trading_name,
            "Area": area,
            "Visit Date": visit_date
        }])
        # Append to CSV
        if os.path.exists(VISITS_CSV):
            new_visit.to_csv(VISITS_CSV, mode="a", header=False, index=False)
        else:
            new_visit.to_csv(VISITS_CSV, mode="w", header=True, index=False)
        st.success("Visit logged successfully! Please refresh the Dashboard tab to see new data.")

# --- Tab 2: Dashboard ---
with tab2:
    st.header("Customer Visit Dashboard")

    # Reload visits in case new data was added
    if os.path.exists(VISITS_CSV):
        visits = pd.read_csv(VISITS_CSV)
        if 'Visit Date' in visits.columns:
            visits['Visit Date'] = pd.to_datetime(visits['Visit Date'], errors='coerce')
    else:
        visits = pd.DataFrame(columns=['Agent Name', 'Trading Name', 'Area', 'Visit Date'])

    # Filters
    agent_list = ['All'] + sorted(customers['Agent Name'].dropna().astype(str).unique().tolist())
    area_list = ['All'] + sorted(customers['Area'].dropna().astype(str).unique().tolist())
    agent = st.sidebar.selectbox('Select Agent', agent_list, key='dashboard_agent')
    area = st.sidebar.selectbox('Select Area', area_list, key='dashboard_area')
    if not visits.empty and 'Visit Date' in visits.columns:
        year_list = sorted(visits['Visit Date'].dropna().dt.year.unique().tolist())
        year = st.sidebar.selectbox('Select Year', year_list, key='dashboard_year')
    else:
        year = datetime.now().year
    quarter = st.sidebar.selectbox('Select Quarter', [1, 2, 3, 4], key='dashboard_quarter')

    # Filtering
    def filter_data(agent, area, year, quarter):
        df = visits.copy()
        if agent != 'All':
            df = df[df['Agent Name'] == agent]
        if area != 'All':
            df = df[df['Area'] == area]
        if 'Visit Date' in df.columns:
            df = df[df['Visit Date'].dt.year == year]
            df = df[df['Visit Date'].dt.quarter == quarter]
        return df

    months_quarters = {1: ['Jan','Feb','Mar'], 2: ['Apr','May','Jun'], 3: ['Jul','Aug','Sep'], 4: ['Oct','Nov','Dec']}
    months_numbers = {1: [1,2,3], 2: [4,5,6], 3: [7,8,9], 4: [10,11,12]}
    filtered_visits = filter_data(agent, area, year, quarter)

    # Prepare report
    report = []
    for _, cust in customers.iterrows():
        if (agent != 'All' and str(cust['Agent Name']) != str(agent)) or \
           (area != 'All' and str(cust['Area']) != str(area)):
            continue
        row = [cust['Agent Name'], cust['Trading Name'], cust['Area']]
        for m in months_numbers[quarter]:
            month_visits = filtered_visits[
                (filtered_visits['Trading Name'] == cust['Trading Name']) &
                (filtered_visits['Agent Name'] == cust['Agent Name']) &
                (filtered_visits['Area'] == cust['Area']) &
                (filtered_visits['Visit Date'].dt.month == m)
            ]
            if not month_visits.empty:
                days = month_visits['Visit Date'].dt.day.astype(str).tolist()
                row.append(f"{len(days)} ({', '.join(days)})")
            else:
                row.append("0")
        report.append(row)
    columns = ['Agent Name', 'Trading Name', 'Area'] + months_quarters[quarter]
    report_df = pd.DataFrame(report, columns=columns)

    st.markdown("**Filter by agent, area, year, quarter. Download the report below.**")
    st.dataframe(report_df)

    csv = report_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Download filtered report as CSV",
        csv,
        "filtered_report.csv",
        "text/csv",
        key='download-csv'
    )
