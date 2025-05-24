import streamlit as st
import pandas as pd
from datetime import date, datetime
import os

st.set_page_config(page_title="SIMA Customer Visits", layout="wide", page_icon="👁️")

CUSTOMERS_CSV = "customers.csv"
VISITS_CSV = "visits.csv"
CLOSED_ACCOUNTS_CSV = "closed_accounts.csv"

def load_visits():
    if os.path.exists(VISITS_CSV):
        visits = pd.read_csv(VISITS_CSV)
        if 'Visit Date' in visits.columns:
            visits['Visit Date'] = pd.to_datetime(visits['Visit Date'], errors='coerce')
        if 'Notes' not in visits.columns:
            visits['Notes'] = ""
        if 'Closed Account' not in visits.columns:
            visits['Closed Account'] = "No"
    else:
        visits = pd.DataFrame(columns=['Agent Name', 'Trading Name', 'Area', 'Visit Date', 'Notes', 'Closed Account'])
    return visits

def load_closed_accounts():
    if os.path.exists(CLOSED_ACCOUNTS_CSV):
        return pd.read_csv(CLOSED_ACCOUNTS_CSV)
    else:
        return pd.DataFrame(columns=['Agent Name', 'Trading Name', 'Area'])

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

try:
    customers = pd.read_csv(CUSTOMERS_CSV)
except Exception as e:
    st.error(f"Error loading customers.csv: {e}")
    st.stop()

# --- Simple page navigation buttons ---
if "page" not in st.session_state:
    st.session_state["page"] = "visit"

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Log a Visit"):
        st.session_state["page"] = "visit"
with col2:
    if st.button("Dashboard"):
        st.session_state["page"] = "dashboard"
with col3:
    if st.button("Closed Accounts"):
        st.session_state["page"] = "closed"

# --- Log a Visit Page ---
if st.session_state["page"] == "visit":
    st.markdown("<h2 style='color:#ff3c00; text-align:center; font-weight:900;'>LOG A VISIT</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Log your customer visits below. If a customer account is closed, select \"Yes\" and add a note.</p>", unsafe_allow_html=True)
    st.write("")

    visits = load_visits()
    closed_accounts_df = load_closed_accounts()

    cols = st.columns([1,1,1])
    agent_name = cols[0].selectbox("Agent Name", customers["Agent Name"].dropna().unique(), key="visit_agent")

    agent_customers_all = customers[customers["Agent Name"] == agent_name]
    trading_names_open = []
    areas_open = []
    for _, row in agent_customers_all.iterrows():
        if not is_customer_closed(row['Agent Name'], row['Trading Name'], row['Area'], closed_accounts_df):
            trading_names_open.append(row['Trading Name'])
            areas_open.append(row['Area'])

    if trading_names_open:
        trading_name = cols[1].selectbox(
            "Trading Name (type to search)", trading_names_open, key="visit_trading"
        )
        idx = trading_names_open.index(trading_name)
        area = areas_open[idx]
        can_submit = True
    else:
        trading_name = ""
        area = ""
        cols[1].selectbox("Trading Name (type to search)", ["No open customers"], key="visit_trading_disabled", disabled=True)
        can_submit = False

    cols[2].text_input("Area", area, disabled=True, key="area_text")

    visit_date = st.date_input("Visit Date", date.today())
    notes = st.text_input("Notes (optional)", key="visit_notes", placeholder="Add any notes about this visit")
    closed_account = st.selectbox("Closed Account", ["No", "Yes"], key="closed_account_select")

    add_btn = st.button("Add Visit", disabled=not can_submit)
    if not can_submit and agent_name:
        st.warning("All customers for this agent are marked as closed. You cannot log further visits for closed customers.")

    if add_btn and can_submit:
        visits = load_visits()
        new_visit = pd.DataFrame([{
            "Agent Name": agent_name,
            "Trading Name": trading_name,
            "Area": area,
            "Visit Date": visit_date,
            "Notes": notes,
            "Closed Account": closed_account
        }])
        for col in ['Notes', 'Closed Account']:
            if col not in visits.columns:
                visits[col] = ""
        if os.path.exists(VISITS_CSV):
            new_visit.to_csv(VISITS_CSV, mode="a", header=False, index=False)
        else:
            new_visit.to_csv(VISITS_CSV, mode="w", header=True, index=False)
        # If closed, add to closed_accounts.csv
        if closed_account == "Yes":
            add_closed_account(agent_name, trading_name, area)
            st.success("✅ Visit logged successfully and marked as closed. This customer will no longer appear in the list.")
        else:
            st.success("✅ Visit logged successfully!")
        st.balloons()

# --- Dashboard Page ---
elif st.session_state["page"] == "dashboard":
    st.markdown("<h2 style='color:#145DA0; text-align:center; font-weight:900;'>DASHBOARD</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Analyze and download customer visit records. Use filters below.</p>", unsafe_allow_html=True)
    st.write("")

    visits = load_visits()
    closed_accounts_df = load_closed_accounts()

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
        view_mode = st.selectbox("View by", ["Day", "Date Range", "Quarter"], key="view_mode_select")
    with filter4:
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
    with filter5:
        pass

    filtered = visits.copy()
    if agent != 'All':
        filtered = filtered[filtered['Agent Name'] == agent]
    if area != 'All':
        filtered = filtered[filtered['Area'] == area]

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
                # Mark as closed if in closed_accounts.csv
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
            styled_df = styled_df[['Agent Name', 'Trading Name', 'Area', 'Visit Date', 'Notes', 'Closed Account']]
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
            row = [cust['Agent Name'], row_name, cust['Area']]
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

# --- Closed Accounts Page ---
elif st.session_state["page"] == "closed":
    st.markdown("<h2 style='color:#a94442; text-align:center; font-weight:900;'>CLOSED ACCOUNTS</h2>", unsafe_allow_html=True)
    st.write("")
    closed_accounts_df = load_closed_accounts()
    if closed_accounts_df.empty:
        st.info("No closed accounts.")
    else:
        st.dataframe(closed_accounts_df.style.apply(lambda row: ['background-color: #ffebe6; color: #a94442']*len(row), axis=1),
                     use_container_width=True, hide_index=True)
