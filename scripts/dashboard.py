import streamlit as st
import pandas as pd
from datetime import date, datetime
import os

CUSTOMERS_CSV = "customers.csv"
VISITS_CSV = "visits.csv"
CLOSED_ACCOUNTS_CSV = "closed_accounts.csv"

def load_customers():
    try:
        df = pd.read_csv(CUSTOMERS_CSV, dtype=str)
        for col in ['Agent Name', 'Trading Name', 'Area', 'Province']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        df = df[df['Agent Name'].notna() & (df['Agent Name'] != "")]
        df = df[df['Area'].notna() & (df['Area'] != "")]
        return df
    except Exception as e:
        st.error(f"Error loading {CUSTOMERS_CSV}: {e}")
        return pd.DataFrame(columns=['Agent Name', 'Trading Name', 'Area', 'Province'])

def load_closed_accounts():
    if os.path.exists(CLOSED_ACCOUNTS_CSV):
        df = pd.read_csv(CLOSED_ACCOUNTS_CSV, dtype=str)
        for col in ['Agent Name', 'Trading Name', 'Area']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        return df
    else:
        df = pd.DataFrame(columns=['Agent Name', 'Trading Name', 'Area'])
        df.to_csv(CLOSED_ACCOUNTS_CSV, index=False)
        return df

def add_closed_account(agent, trading_name, area):
    df = load_closed_accounts()
    exists = ((df['Agent Name'] == agent) &
              (df['Trading Name'] == trading_name) &
              (df['Area'] == area)).any()
    if not exists:
        df2 = pd.DataFrame([{'Agent Name': agent, 'Trading Name': trading_name, 'Area': area}])
        df = pd.concat([df, df2], ignore_index=True)
        df.to_csv(CLOSED_ACCOUNTS_CSV, index=False)

def is_customer_closed(agent, trading_name, area, closed_accounts_df):
    if closed_accounts_df.empty:
        return False
    q = (closed_accounts_df['Agent Name'] == agent) & \
        (closed_accounts_df['Trading Name'] == trading_name) & \
        (closed_accounts_df['Area'] == area)
    return closed_accounts_df[q].shape[0] > 0

def load_visits():
    if os.path.exists(VISITS_CSV):
        visits = pd.read_csv(VISITS_CSV, dtype=str)
        if 'Visit Date' in visits.columns:
            visits['Visit Date'] = pd.to_datetime(visits['Visit Date'], errors='coerce')
        for col in ['Notes', 'Closed Account']:
            if col not in visits.columns:
                visits[col] = ""
        if 'Province' not in visits.columns:
            visits['Province'] = ""
        for col in ['Agent Name', 'Trading Name', 'Area', 'Province']:
            if col in visits.columns:
                visits[col] = visits[col].astype(str).str.strip()
    else:
        visits = pd.DataFrame(columns=['Agent Name', 'Trading Name', 'Area', 'Province', 'Visit Date', 'Notes', 'Closed Account'])
    return visits

def log_visits(rows):
    visits_exist = os.path.exists(VISITS_CSV)
    new_visits_df = pd.DataFrame(rows)
    if visits_exist:
        new_visits_df.to_csv(VISITS_CSV, mode="a", header=False, index=False)
    else:
        new_visits_df.to_csv(VISITS_CSV, mode="w", header=True, index=False)

st.set_page_config(page_title="SIMA Customer Visits", layout="wide", page_icon="👁️")
if "page" not in st.session_state:
    st.session_state["page"] = "visit"

nav1, nav2, nav3 = st.columns(3)
with nav1:
    if st.button("Log a Visit"):
        st.session_state["page"] = "visit"
with nav2:
    if st.button("Dashboard"):
        st.session_state["page"] = "dashboard"
with nav3:
    if st.button("Closed Accounts"):
        st.session_state["page"] = "closed"

# === Log a Visit Page ===
if st.session_state["page"] == "visit":
    st.markdown("<h2 style='color:#ff3c00; text-align:center; font-weight:900;'>LOG A VISIT</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Log your customer visits below. Select multiple customers for the same agent/area/date.</p>", unsafe_allow_html=True)
    st.write("")

    customers = load_customers()
    closed_accounts_df = load_closed_accounts()
    agent_list = customers["Agent Name"].dropna().unique().tolist()

    # --- Step 1: Select Agent ---
    agent_name = st.selectbox("Agent Name", agent_list, key="agent_select")

    # --- Step 2: Select Area (filtered by agent) ---
    areas = customers[customers["Agent Name"] == agent_name]["Area"].dropna().unique().tolist()
    area = st.selectbox("Area", areas, key=f"area_select_{agent_name}")

    # --- Step 3: Province (filtered by agent and area) ---
    provinces = customers[
        (customers["Agent Name"] == agent_name) & (customers["Area"] == area)
    ]["Province"].dropna().unique().tolist()
    province = provinces[0] if len(provinces) == 1 else st.selectbox("Province", provinces, key=f"province_select_{agent_name}_{area}")

    # --- Step 4: Customers in Area ---
    customers_in_area = customers[
        (customers["Agent Name"] == agent_name) & (customers["Area"] == area)
    ].drop_duplicates(subset=["Trading Name"])
    open_customers = [
        row['Trading Name']
        for idx, row in customers_in_area.iterrows()
        if not is_customer_closed(row['Agent Name'], row['Trading Name'], row['Area'], closed_accounts_df)
    ]

    with st.form("visit_form", clear_on_submit=True):
        selected_customers = st.multiselect("Select Customers (multiple)", open_customers, key="customer_multi")
        visit_date = st.date_input("Visit Date", date.today(), key="visit_date")
        notes = st.text_input("Notes (optional)", placeholder="Add notes about this visit", key="visit_notes")
        closed_account = st.selectbox("Closed Account (applies to ALL selected)", ["No", "Yes"], key="close_select")
		
     submitted = st.form_submit_button("Add Visit")
if submitted:
    if not selected_customers:
        st.error("Please select at least one customer to log a visit.")
    else:
        visit_rows = []
        for trading_name in selected_customers:
            visit_rows.append({
                "Agent Name": agent_name,
                "Trading Name": trading_name,
                "Area": area,
                "Province": province,
                "Visit Date": visit_date,
                "Notes": notes,
                "Closed Account": closed_account
            })
            if closed_account == "Yes":
                add_closed_account(agent_name, trading_name, area)
        log_visits(visit_rows)
        st.success(f"Logged {len(visit_rows)} visits for {agent_name} in {area}.")
        st.balloons()
# === Dashboard Page ===
elif st.session_state["page"] == "dashboard":
    st.markdown("<h2 style='color:#145DA0; text-align:center; font-weight:900;'>DASHBOARD</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Analyze and download customer visit records. Use filters below.</p>", unsafe_allow_html=True)
    st.write("")
    customers = load_customers()
    closed_accounts_df = load_closed_accounts()
    visits = load_visits()
    filter1, filter2, filter3, filter4, filter5 = st.columns([1.8,1.8,1.8,1.8,2])
    with filter1:
        agent_list = ['All'] + sorted(customers['Agent Name'].dropna().astype(str).unique().tolist())
        agent = st.selectbox('Agent', agent_list, key='dashboard_agent')
    with filter2:
        if agent != 'All':
            area_list = ['All'] + sorted(customers[customers['Agent Name'] == agent]['Area'].dropna().astype(str).unique().tolist())
        else:
            area_list = ['All'] + sorted(customers['Area'].dropna().astype(str).unique().tolist())
        area = st.selectbox('Area', area_list, key='dashboard_area')
    with filter3:
        if agent != 'All' and area != 'All':
            province_list = ['All'] + sorted(customers[(customers['Agent Name'] == agent) & (customers['Area'] == area)]['Province'].dropna().astype(str).unique().tolist())
        elif agent != 'All':
            province_list = ['All'] + sorted(customers[customers['Agent Name'] == agent]['Province'].dropna().astype(str).unique().tolist())
        else:
            province_list = ['All'] + sorted(customers['Province'].dropna().astype(str).unique().tolist())
        province = st.selectbox("Province", province_list, key="dashboard_province")
    with filter4:
        view_mode = st.selectbox("View by", ["Day", "Date Range", "Quarter"], key="view_mode_select")
    with filter5:
        if view_mode == "Day":
            selected_date = st.date_input("Date", value=date.today(), key="dashboard_day")
        elif view_mode == "Date Range":
            start_date = st.date_input("Start Date", value=date.today(), key="dashboard_start")
            end_date = st.date_input("End Date", value=date.today(), key="dashboard_end")
        else:
            visits_for_year = visits if visits.empty else visits.dropna(subset=['Visit Date'])
            if not visits_for_year.empty and 'Visit Date' in visits_for_year.columns:
                year_list = sorted(visits_for_year['Visit Date'].dropna().dt.year.unique().tolist())
                if not year_list:
                    year_list = [datetime.now().year]
                year = st.selectbox('Year', year_list, key='dashboard_year')
            else:
                year = datetime.now().year
            quarter = st.selectbox('Quarter', [1, 2, 3, 4], key="dashboard_quarter")

    # Apply filters
    filtered = visits.copy()
    if agent != 'All':
        filtered = filtered[filtered['Agent Name'] == agent]
    if area != 'All':
        filtered = filtered[filtered['Area'] == area]
    if province != 'All':
        filtered = filtered[filtered['Province'] == province]

    if view_mode == "Day":
        filtered = filtered[filtered["Visit Date"].dt.date == selected_date]
    elif view_mode == "Date Range":
        filtered = filtered[
            (filtered["Visit Date"].dt.date >= start_date) &
            (filtered["Visit Date"].dt.date <= end_date)
        ]
    else:
        filtered = filtered[
            (filtered["Visit Date"].dt.year == year) &
            (filtered["Visit Date"].dt.quarter == quarter)
        ]

    st.write("")
    if view_mode in ['Day', 'Date Range']:
        st.markdown("#### Customer Visits")
        if not filtered.empty:
            def format_trading_name(row):
                is_closed = is_customer_closed(
                    row['Agent Name'],
                    row['Trading Name'],
                    row['Area'],
                    closed_accounts_df
                )
                if is_closed:
                    note = f" (Closed Account: {row['Notes']})" if row.get('Notes') else " (Closed Account)"
                    return f"❌ {row['Trading Name']}{note}"
                else:
                    return row['Trading Name']

            styled_df = filtered.copy()
            styled_df['Trading Name'] = styled_df.apply(format_trading_name, axis=1)
            styled_df = styled_df[['Agent Name', 'Trading Name', 'Area', 'Province', 'Visit Date', 'Notes', 'Closed Account']]
            styled_df['Visit Date'] = styled_df['Visit Date'].astype(str)

            def highlight_closed(row):
                is_closed = is_customer_closed(
                    row['Agent Name'],
                    row['Trading Name'].replace("❌ ", "").split(" (Closed")[0],
                    row['Area'],
                    closed_accounts_df
                )
                if is_closed:
                    return ['background-color: #ffebe6; color: #a94442']*len(row)
                else:
                    return ['']*len(row)
            st.dataframe(styled_df.style.apply(highlight_closed, axis=1), use_container_width=True, hide_index=True)
        else:
            st.info("No visits found for the selected criteria.")

    else:
        months_quarters = {1: ['Jan','Feb','Mar'], 2: ['Apr','May','Jun'], 3: ['Jul','Aug','Sep'], 4: ['Oct','Nov','Dec']}
        months_numbers = {1: [1,2,3], 2: [4,5,6], 3: [7,8,9], 4: [10,11,12]}
        report = []
        customers_filtered = customers
        if agent != 'All':
            customers_filtered = customers_filtered[customers_filtered['Agent Name'] == agent]
        if area != 'All':
            customers_filtered = customers_filtered[customers_filtered['Area'] == area]
        if province != 'All':
            customers_filtered = customers_filtered[customers_filtered['Province'] == province]
        for _, cust in customers_filtered.iterrows():
            closed = is_customer_closed(cust['Agent Name'], cust['Trading Name'], cust['Area'], closed_accounts_df)
            closed_note = ""
            if closed:
                closed_visits = visits[
                    (visits['Agent Name'] == cust['Agent Name']) &
                    (visits['Trading Name'] == cust['Trading Name']) &
                    (visits['Area'] == cust['Area']) &
                    (visits['Closed Account'].astype(str).str.lower() == 'yes')
                ]
                closed_note = closed_visits.iloc[-1]['Notes'] if not closed_visits.empty and 'Notes' in closed_visits.columns else ""
            row_name = f"❌ {cust['Trading Name']}" if closed else cust['Trading Name']
            if closed:
                row_name += f" (Closed Account{': '+closed_note if closed_note else ''})"
            row = [cust['Agent Name'], row_name, cust['Area'], cust['Province']]
            for m in months_numbers[quarter]:
                month_visits = filtered[
                    (filtered['Trading Name'] == cust['Trading Name']) &
                    (filtered['Agent Name'] == cust['Agent Name']) &
                    (filtered['Area'] == cust['Area']) &
                    (filtered['Province'] == cust['Province']) &
                    (filtered['Visit Date'].dt.month == m)
                ]
                if not month_visits.empty:
                    days = month_visits['Visit Date'].dt.day.astype(str).tolist()
                    row.append(f"{len(days)} ({', '.join(days)})")
                else:
                    row.append("0")
            report.append(row)
        columns = ['Agent Name', 'Trading Name', 'Area', 'Province'] + months_quarters[quarter]
        report_df = pd.DataFrame(report, columns=columns)
        def closed_row_highlight(row):
            if str(row['Trading Name']).startswith('❌'):
                return ['background-color: #ffebe6; color: #a94442']*len(row)
            else:
                return ['']*len(row)
        st.markdown("#### Quarterly Summary")
        st.dataframe(report_df.style.apply(closed_row_highlight, axis=1), use_container_width=True, hide_index=True)

    st.write("")
    col_dl_csv, col_spacer = st.columns([1.3,7])
    with col_dl_csv:
        csv = filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            "⬇️ Download CSV",
            csv,
            "filtered_visits.csv",
            "text/csv",
            key='download-csv'
        )

# === Closed Accounts Page ===
elif st.session_state["page"] == "closed":
    st.markdown("<h2 style='color:#a94442; text-align:center; font-weight:900;'>CLOSED ACCOUNTS</h2>", unsafe_allow_html=True)
    st.write("")
    closed_accounts_df = load_closed_accounts()
    if closed_accounts_df.empty:
        st.info("No closed accounts.")
    else:
        st.dataframe(closed_accounts_df.style.apply(
            lambda row: ['background-color: #ffebe6; color: #a94442']*len(row), axis=1),
            use_container_width=True, hide_index=True)
