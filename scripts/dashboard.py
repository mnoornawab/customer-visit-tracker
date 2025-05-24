import streamlit as st
import pandas as pd
from datetime import date, datetime
import os

# --- Page settings and style ---
st.set_page_config(page_title="SIMA Customer Visits", layout="wide", page_icon="👁️")
st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-family: 'Segoe UI',sans-serif;
            background-color: #f6fafd;
        }
        .big-title {
            font-size: 2.5rem !important; 
            color: #ff3c00 !important; 
            font-weight: 900;
            text-align: center; 
            margin-bottom: 0.5rem; 
            margin-top: 0.3rem;
            letter-spacing: 0.03em;
        }
        .subtitle {
            font-size: 1.1rem; 
            color: #0C2D48; 
            text-align: center;
            margin-bottom: 2rem; 
            margin-top: 0.8rem;
        }
        .form-container {
            background: #eef6ff;
            border-radius: 16px;
            padding: 1.5rem 1.5rem 1rem 1.5rem;
            margin: 0 auto 1.5rem auto;
            max-width: 950px;
            width: 100%;
        }
        .stButton>button, .stDownloadButton>button {
            background: linear-gradient(90deg, #145DA0 0%, #0C2D48 100%);
            color: white; font-size: 16px; font-weight: 600;
            border-radius: 8px; padding: 10px 20px; border: none; margin: 8px 0px 8px 0px;
            box-shadow: 0 2px 8px #00000010;
            transition: all 0.15s;
        }
        .stButton>button:hover, .stDownloadButton>button:hover {
            background: linear-gradient(90deg, #2e86de 0%, #0C2D48 100%);
            color: #fff;
            transform: scale(1.03);
        }
        .stDataFrame {border-radius: 10px;}
        .block-container {padding-top: 0.6rem;}
        label, .css-1c7y2kd, .css-1ofwbyh, .css-1q8dd3e { color: #145DA0 !important; }
        .stSelectbox>div>div>div>div { background-color: #f4f8fc !important; }
        .closed-account-row {
            background-color: #ffebe6 !important;
            color: #a94442 !important;
        }
        @media (max-width: 900px) {
            .form-container {padding: 0.8rem;}
        }
        @media (max-width: 600px) {
            .form-container {padding: 0.3rem;}
            .big-title {font-size: 1.4rem !important;}
        }
    </style>
""", unsafe_allow_html=True)

CUSTOMERS_CSV = "customers.csv"
VISITS_CSV = "visits.csv"

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

try:
    customers = pd.read_csv(CUSTOMERS_CSV)
except Exception as e:
    st.error(f"Error loading customers.csv: {e}")
    st.stop()

def get_closed_accounts_df(visits):
    if visits.empty or "Closed Account" not in visits.columns:
        return pd.DataFrame(columns=['Agent Name', 'Trading Name', 'Area'])
    closed = visits[visits['Closed Account'].astype(str).str.lower() == "yes"]
    return closed.drop_duplicates(subset=['Agent Name', 'Trading Name', 'Area'])[['Agent Name', 'Trading Name', 'Area']]

def is_customer_closed(agent, trading_name, area, closed_accounts_df):
    if closed_accounts_df.empty:
        return False
    q = (closed_accounts_df['Agent Name'] == agent) & \
        (closed_accounts_df['Trading Name'] == trading_name) & \
        (closed_accounts_df['Area'] == area)
    return closed_accounts_df[q].shape[0] > 0

# --- Streamlit native tabs ---
tab1, tab2 = st.tabs([
    "➕ Log a Visit",
    "📊 Dashboard"
])

with tab1:
    st.markdown('<div class="big-title">LOG A VISIT</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Log your customer visits below. If a customer account is closed, select "Yes" and add a note.</div>', unsafe_allow_html=True)
    st.markdown('<div class="form-container">', unsafe_allow_html=True)

    visits = load_visits()
    closed_accounts_df = get_closed_accounts_df(visits)

    cols = st.columns([1,1,1])
    agent_name = cols[0].selectbox("Agent Name", customers["Agent Name"].dropna().unique(), key="visit_agent")

    # Only show non-closed trading names for this agent
    agent_customers_all = customers[customers["Agent Name"] == agent_name]
    trading_names_open = []
    trading_names_closed = []
    for _, row in agent_customers_all.iterrows():
        if is_customer_closed(row['Agent Name'], row['Trading Name'], row['Area'], closed_accounts_df):
            trading_names_closed.append(row['Trading Name'])
        else:
            trading_names_open.append(row['Trading Name'])

    trading_names_display = trading_names_open.copy()
    if trading_names_closed:
        trading_names_display += [f"❌ {name} (Closed)" for name in trading_names_closed]

    trading_name = cols[1].selectbox(
        "Trading Name (type to search)",
        trading_names_display,
        key="visit_trading"
    )

    if trading_name in trading_names_open:
        area = agent_customers_all[agent_customers_all["Trading Name"] == trading_name]["Area"].values[0]
        can_submit = True
    else:
        # It's a closed account; find the original name and area
        original_name = trading_name.replace("❌ ", "").replace(" (Closed)", "")
        area = agent_customers_all[agent_customers_all["Trading Name"] == original_name]["Area"].values[0] if original_name in agent_customers_all["Trading Name"].values else ""
        can_submit = False

    cols[2].text_input("Area", area, disabled=True, key="area_text")

    visit_date = st.date_input("Visit Date", date.today())
    notes = st.text_input("Notes (optional)", key="visit_notes", placeholder="Add any notes about this visit")
    closed_account = st.selectbox("Closed Account", ["No", "Yes"], key="closed_account_select")

    add_btn = st.button("Add Visit", disabled=not can_submit)
    if not can_submit and trading_name:
        st.warning("This customer is a closed account. You cannot log further visits for a closed customer.")

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
        if trading_name.startswith("❌ "):
            new_visit["Trading Name"] = trading_name.replace("❌ ", "").replace(" (Closed)", "")
        for col in ['Notes', 'Closed Account']:
            if col not in visits.columns:
                visits[col] = ""
        if os.path.exists(VISITS_CSV):
            new_visit.to_csv(VISITS_CSV, mode="a", header=False, index=False)
        else:
            new_visit.to_csv(VISITS_CSV, mode="w", header=True, index=False)
        st.success("✅ Visit logged successfully!")
        st.balloons()
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="big-title">DASHBOARD</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Analyze and download customer visit records. Use filters below.</div>', unsafe_allow_html=True)

    visits = load_visits()
    closed_accounts_df = get_closed_accounts_df(visits)

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
            if not visits.empty and 'Visit Date' in visits.columns:
                year_list = sorted(visits['Visit Date'].dropna().dt.year.unique().tolist())
                if not year_list:
                    year_list = [datetime.now().year]
                year = st.selectbox('Year', year_list, key='dashboard_year')
            else:
                year = datetime.now().year
            quarter = st.selectbox('Quarter', [1, 2, 3, 4], key='dashboard_quarter')
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
                is_closed = is_customer_closed(row['Agent Name'], row['Trading Name'], row['Area'], closed_accounts_df)
                if is_closed:
                    note = f" (Closed Account: {row['Notes']})" if row.get('Notes') else " (Closed Account)"
                    return f"❌ {row['Trading Name']}{note}"
                else:
                    return row['Trading Name']

            styled_df = filtered.copy()
            styled_df['Trading Name'] = styled_df.apply(format_trading_name, axis=1)
            styled_df = styled_df[['Agent Name', 'Trading Name', 'Area', 'Visit Date', 'Notes']]
            styled_df['Visit Date'] = styled_df['Visit Date'].astype(str)

            def highlight_closed(row):
                is_closed = is_customer_closed(row['Agent Name'], row['Trading Name'].replace("❌ ","").split(" (Closed")[0], row['Area'], closed_accounts_df)
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
