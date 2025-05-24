import streamlit as st
import pandas as pd
from datetime import date, datetime
import os

CUSTOMERS_CSV = "customers.csv"
VISITS_CSV = "visits.csv"

# Load customers
try:
    customers = pd.read_csv(CUSTOMERS_CSV)
except Exception as e:
    st.error(f"Error loading customers.csv: {e}")
    st.stop()

# Load or create visits
if os.path.exists(VISITS_CSV):
    visits = pd.read_csv(VISITS_CSV)
    if 'Visit Date' in visits.columns:
        visits['Visit Date'] = pd.to_datetime(visits['Visit Date'], errors='coerce')
else:
    visits = pd.DataFrame(columns=['Agent Name', 'Trading Name', 'Area', 'Visit Date', 'Notes', 'Closed Account'])

tab1, tab2 = st.tabs(["➕ Log a Visit", "📊 Dashboard"])

with tab1:
    st.header("Agent: Log a New Visit")

    agent_name = st.selectbox("Agent Name", customers["Agent Name"].dropna().unique())
    # Dynamically filter customers for the selected agent
    agent_customers = customers[customers["Agent Name"] == agent_name]
    trading_name = st.selectbox("Trading Name", agent_customers["Trading Name"].dropna().unique())
    area = agent_customers[agent_customers["Trading Name"] == trading_name]["Area"].values[0]
    st.text_input("Area", area, disabled=True)
    visit_date = st.date_input("Visit Date", date.today())
    notes = st.text_input("Notes (optional)")
    closed_account = st.selectbox("Closed Account", ["No", "Yes"])
    if st.button("Add Visit"):
        new_visit = pd.DataFrame([{
            "Agent Name": agent_name,
            "Trading Name": trading_name,
            "Area": area,
            "Visit Date": visit_date,
            "Notes": notes,
            "Closed Account": closed_account
        }])
        if os.path.exists(VISITS_CSV):
            new_visit.to_csv(VISITS_CSV, mode="a", header=False, index=False)
        else:
            new_visit.to_csv(VISITS_CSV, mode="w", header=True, index=False)
        st.success("Visit logged successfully! Please refresh the Dashboard tab to see new data.")

with tab2:
    st.header("Customer Visit Dashboard")

    if os.path.exists(VISITS_CSV):
        visits = pd.read_csv(VISITS_CSV)
        if 'Visit Date' in visits.columns:
            visits['Visit Date'] = pd.to_datetime(visits['Visit Date'], errors='coerce')
    else:
        visits = pd.DataFrame(columns=['Agent Name', 'Trading Name', 'Area', 'Visit Date', 'Notes', 'Closed Account'])

    agent_list = ['All'] + sorted(customers['Agent Name'].dropna().astype(str).unique().tolist())
    area_list = ['All'] + sorted(customers['Area'].dropna().astype(str).unique().tolist())

    agent = st.sidebar.selectbox('Select Agent', agent_list, key='dashboard_agent')
    area = st.sidebar.selectbox('Select Area', area_list, key='dashboard_area')
    view_mode = st.sidebar.radio("View by", ["Day", "Date Range", "Quarter"], horizontal=True)

    # Date filtering options
    if view_mode == "Day":
        selected_date = st.sidebar.date_input("Select Date", value=date.today())
        def date_filter(df): return df['Visit Date'].dt.date == selected_date
    elif view_mode == "Date Range":
        start_date = st.sidebar.date_input("Start Date", value=date.today())
        end_date = st.sidebar.date_input("End Date", value=date.today())
        def date_filter(df): return (df['Visit Date'].dt.date >= start_date) & (df['Visit Date'].dt.date <= end_date)
    else:
        if not visits.empty and 'Visit Date' in visits.columns:
            year_list = sorted(visits['Visit Date'].dropna().dt.year.unique().tolist())
            year = st.sidebar.selectbox('Select Year', year_list, key='dashboard_year')
        else:
            year = datetime.now().year
        quarter = st.sidebar.selectbox('Select Quarter', [1, 2, 3, 4], key='dashboard_quarter')
        def date_filter(df):
            return (df['Visit Date'].dt.year == year) & (df['Visit Date'].dt.quarter == quarter)

    # Filtering
    filtered = visits.copy()
    if agent != 'All':
        filtered = filtered[filtered['Agent Name'] == agent]
    if area != 'All':
        filtered = filtered[filtered['Area'] == area]
    if not filtered.empty:
        filtered = filtered[date_filter(filtered)]
    else:
        filtered = pd.DataFrame(columns=visits.columns)

    # Show per-day table
    if view_mode in ['Day', 'Date Range']:
        st.subheader("Visits per day")
        if not filtered.empty:
            filtered['Visit Date'] = filtered['Visit Date'].dt.strftime("%Y-%m-%d")
            # Mark closed accounts with a line-through and note
            def closed_style(row):
                if str(row.get('Closed Account', 'No')).lower() == 'yes':
                    return f'color: gray; text-decoration: line-through;'
                else:
                    return ''
            styled_df = filtered.copy()
            styled_df['Trading Name'] = styled_df.apply(
                lambda row: f"~~{row['Trading Name']}~~ (closed account)" if str(row.get('Closed Account', 'No')).lower() == 'yes'
                else row['Trading Name'],
                axis=1
            )
            show_cols = ['Agent Name', 'Trading Name', 'Area', 'Visit Date', 'Notes', 'Closed Account']
            st.dataframe(styled_df[show_cols], use_container_width=True)
        else:
            st.info("No visits found for the selected criteria.")
    else:
        # Quarter view as before
        months_quarters = {1: ['Jan','Feb','Mar'], 2: ['Apr','May','Jun'], 3: ['Jul','Aug','Sep'], 4: ['Oct','Nov','Dec']}
        months_numbers = {1: [1,2,3], 2: [4,5,6], 3: [7,8,9], 4: [10,11,12]}
        report = []
        for _, cust in customers.iterrows():
            if (agent != 'All' and str(cust['Agent Name']) != str(agent)) or \
               (area != 'All' and str(cust['Area']) != str(area)):
                continue
            # Is this customer closed?
            closed = False
            closed_note = ""
            # Check if any visit for this customer is marked closed
            closed_visits = visits[
                (visits['Agent Name'] == cust['Agent Name']) &
                (visits['Trading Name'] == cust['Trading Name']) &
                (visits['Area'] == cust['Area']) &
                (visits['Closed Account'].astype(str).str.lower() == 'yes')
            ]
            if not closed_visits.empty:
                closed = True
                closed_note = " (closed account)"
            row_name = f"~~{cust['Trading Name']}~~" if closed else cust['Trading Name']
            row = [cust['Agent Name'], row_name + closed_note, cust['Area']]
            for m in months_numbers[quarter]:
                month_visits = filtered[
                    (filtered['Trading Name'] == cust['Trading Name']) &
                    (filtered['Agent Name'] == cust['Agent Name']) &
                    (filtered['Area'] == cust['Area']) &
                    (filtered['Visit Date'].dt.month == m)
                ]
                if not month_visits.empty:
                    days = month_visits['Visit Date'].dt.day.astype(str).tolist()
                    row.append(f"{len(days)} ({', '.join(days)})")
                else:
                    row.append("0")
            report.append(row)
        columns = ['Agent Name', 'Trading Name', 'Area'] + months_quarters[quarter]
        report_df = pd.DataFrame(report, columns=columns)
        st.markdown("**Quarterly Summary**")
        # Render markdown for line-through in table
        def render_markdown(row):
            # This will only work for Streamlit's st.markdown in a loop, not in st.dataframe
            return f"{row['Trading Name']}"
        st.dataframe(report_df)

    # Download button for all modes
    csv = filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Download filtered visits as CSV",
        csv,
        "filtered_visits.csv",
        "text/csv",
        key='download-csv'
    )
