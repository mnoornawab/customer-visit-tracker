import streamlit as st
import pandas as pd
from datetime import date, datetime
import os
import smtplib
from email.message import EmailMessage
import ssl

# --- Page settings and style ---
st.set_page_config(page_title="SIMA Customer Visits", layout="wide", page_icon="👁️")
st.markdown("""
    <style>
        .main {background-color: #f6fafd;}
        .stTabs [data-baseweb="tab-list"] {justify-content: center;}
        .stTabs [data-baseweb="tab"] {font-size: 18px; padding: 12px 32px;}
        .stButton>button, .stDownloadButton>button {
            background: linear-gradient(90deg, #145DA0 0%, #0C2D48 100%);
            color: white; font-size: 17px; font-weight: 600;
            border-radius: 10px; padding: 10px 30px; border: none; margin: 6px 0px 6px 0px;
            box-shadow: 0 2px 8px #00000020;
            transition: all 0.2s;
        }
        .stButton>button:hover, .stDownloadButton>button:hover {
            background: linear-gradient(90deg, #2e86de 0%, #0C2D48 100%);
            color: #fff;
            transform: scale(1.03);
        }
        .stDataFrame {border-radius: 10px; overflow: hidden;}
        .block-container {padding-top: 2rem;}
        .big-title {
            font-size: 2.8rem !important; color: #145DA0; font-weight: 700;
            text-align: center; margin-bottom: 0.1rem;
        }
        .subtitle {
            font-size: 1.2rem; color: #0C2D48; text-align: center;
            margin-bottom: 2rem;
        }
        .stExpander, .stForm {
            border-radius: 15px !important;
            background: #f1f7ff !important;
            border: 1.5px solid #cfe2ff !important;
            padding: 10px 20px !important;
        }
        .stTextInput>div>div>input, .stTextInput>div>div>textarea {
            background-color: #f4f8fc !important;
            border-radius: 8px;
            font-size: 16px;
            color: #1a1a1a;
        }
        label, .css-1c7y2kd, .css-1ofwbyh, .css-1q8dd3e { color: #145DA0 !important; }
        .stSelectbox>div>div>div>div { background-color: #f4f8fc !important; }
        .stDownloadButton>button {margin-top: 18px;}
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

# --- EXPLANATION OF "APP PASSWORD" ---
def app_password_info():
    st.markdown("""
    <span style="color:#0C2D48; font-size:17px;">
    <b>What is a Gmail App Password?</b><br>
    Google now requires "App Passwords" for third-party apps (like this dashboard) to send email using your Gmail.<br>
    <b>How to get one:</b>
    <ol>
        <li>Go to <a href="https://myaccount.google.com/security" target="_blank">Google Account Security</a>.</li>
        <li>Turn on 2-Step Verification (if not already).</li>
        <li>Scroll down to "App passwords".</li>
        <li>Generate a new app password for "Mail".</li>
        <li>Copy the 16-digit code shown and use it as your password here.</li>
    </ol>
    <span style="font-size:15px;color:#333;">You only need to do this once per account.</span>
    </span>
    """, unsafe_allow_html=True)

# --- Load customers data ---
try:
    customers = pd.read_csv(CUSTOMERS_CSV)
except Exception as e:
    st.error(f"Error loading customers.csv: {e}")
    st.stop()

tab1, tab2 = st.tabs(["➕ Log a Visit", "📊 Dashboard"])

with tab1:
    st.markdown('<div class="big-title">SIMA Customer Visits</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Log your customer visits below. If a customer account is closed, select "Yes" and add a note.</div>', unsafe_allow_html=True)
    st.write("")

    with st.form("visit_entry_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([2,3,2])
        with col1:
            agent_name = st.selectbox("Agent Name", customers["Agent Name"].dropna().unique(), key="visit_agent")
        with col2:
            agent_customers = customers[customers["Agent Name"] == agent_name]
            trading_names = agent_customers["Trading Name"].dropna().unique().tolist()
            trading_name = st.selectbox(
                "Trading Name (type to search)", 
                trading_names,
                key="visit_trading"
            )
        with col3:
            if trading_name in agent_customers["Trading Name"].values:
                area = agent_customers[agent_customers["Trading Name"] == trading_name]["Area"].values[0]
            else:
                area = ""
            st.text_input("Area", area, disabled=True, key="area_text")

        visit_date = st.date_input("Visit Date", date.today())
        notes = st.text_input("Notes (optional)", key="visit_notes")
        closed_account = st.selectbox("Closed Account", ["No", "Yes"], key="closed_account_select")
        submit = st.form_submit_button("Add Visit")

    if submit:
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
        st.success("Visit logged! Please refresh the Dashboard tab to see new data.")

with tab2:
    st.markdown('<div class="big-title">SIMA Customer Visits</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Analyze and download customer visit records. Use filters below or email the report.</div>', unsafe_allow_html=True)

    visits = load_visits()
    filter1, filter2, filter3, filter4, filter5 = st.columns([2,2,2,2,2])
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

    # --- Filter visits ---
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

    # --- Show Table ---
    st.write("")
    if view_mode in ['Day', 'Date Range']:
        st.markdown("#### Customer Visits")
        if not filtered.empty:
            def format_trading_name(row):
                if str(row.get('Closed Account', 'No')).lower() == 'yes':
                    return f"~~{row['Trading Name']}~~ (Closed Account: {row['Notes']})" if row.get('Notes') else f"~~{row['Trading Name']}~~ (Closed Account)"
                else:
                    return row['Trading Name']
            styled_df = filtered.copy()
            styled_df['Trading Name'] = styled_df.apply(format_trading_name, axis=1)
            styled_df = styled_df[['Agent Name', 'Trading Name', 'Area', 'Visit Date', 'Notes']]
            styled_df['Visit Date'] = styled_df['Visit Date'].astype(str)
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
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
            closed = False
            closed_note = ""
            closed_visits = visits[
                (visits['Agent Name'] == cust['Agent Name']) &
                (visits['Trading Name'] == cust['Trading Name']) &
                (visits['Area'] == cust['Area']) &
                (visits['Closed Account'].astype(str).str.lower() == 'yes')
            ]
            if not closed_visits.empty:
                closed = True
                closed_note = closed_visits.iloc[-1]['Notes'] if 'Notes' in closed_visits.columns else ""
            row_name = f"~~{cust['Trading Name']}~~" if closed else cust['Trading Name']
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
        st.markdown("#### Quarterly Summary")
        st.dataframe(report_df, use_container_width=True, hide_index=True)

    # --- Download and Email Buttons ---
    st.write("")
    col_dl, col_email, col_spacer = st.columns([1.2,2,7])
    with col_dl:
        csv = filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            "⬇️ Download filtered visits as CSV",
            csv,
            "filtered_visits.csv",
            "text/csv",
            key='download-csv'
        )
    with col_email:
        with st.expander("📧 Email this report", expanded=False):
            with st.form("email_form"):
                email_to = st.text_input("Recipient Email")
                email_from = st.text_input("Your Gmail address")
                email_password = st.text_input("Your Gmail App Password", type="password")
                submit_email = st.form_submit_button("📨 Send report by email")
            app_password_info()
            if submit_email:
                if not email_to or not email_from or not email_password:
                    st.error("Please enter all email details.")
                elif filtered.empty:
                    st.error("No data to send in report.")
                else:
                    try:
                        msg = EmailMessage()
                        msg["Subject"] = "SIMA Customer Visit Report"
                        msg["From"] = email_from
                        msg["To"] = email_to
                        msg.set_content("Attached is your requested SIMA Customer Visit report.")
                        msg.add_attachment(csv, maintype='text', subtype='csv', filename="filtered_visits.csv")
                        context = ssl.create_default_context()
                        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
                            server.login(email_from, email_password)
                            server.send_message(msg)
                        st.success(f"Report sent to {email_to}")
                    except Exception as e:
                        st.error(f"Error sending email: {e}")
