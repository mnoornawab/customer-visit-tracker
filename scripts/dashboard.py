import streamlit as st
import pandas as pd
from datetime import date, datetime
import os

# === File constants ===
CUSTOMERS_CSV = "customers.csv"
VISITS_CSV = "visits.csv"
CLOSED_ACCOUNTS_CSV = "closed_accounts.csv"

def load_customers():
    try:
        df = pd.read_csv(CUSTOMERS_CSV)
        return df
    except Exception as e:
        st.error(f"Error loading {CUSTOMERS_CSV}: {e}")
        return pd.DataFrame(columns=['Agent Name', 'Trading Name', 'Area', 'Province'])

def load_closed_accounts():
    if os.path.exists(CLOSED_ACCOUNTS_CSV):
        df = pd.read_csv(CLOSED_ACCOUNTS_CSV)
        for col in ['Agent Name', 'Trading Name', 'Area']:
            if col not in df.columns:
                df[col] = ""
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
        visits = pd.read_csv(VISITS_CSV)
        if 'Visit Date' in visits.columns:
            visits['Visit Date'] = pd.to_datetime(visits['Visit Date'], errors='coerce')
        for col in ['Notes', 'Closed Account']:
            if col not in visits.columns:
                visits[col] = ""
        if 'Province' not in visits.columns:
            visits['Province'] = ""
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

if st.session_state["page"] == "visit":
    st.markdown("<h2 style='color:#ff3c00; text-align:center; font-weight:900;'>LOG A VISIT</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Log your customer visits below. Select multiple customers for the same agent/area/date.</p>", unsafe_allow_html=True)
    st.write("")

    customers = load_customers()
    closed_accounts_df = load_closed_accounts()

    agent_list = customers["Agent Name"].dropna().unique()

    def clear_form():
        st.session_state.agent_select = agent_list[0] if len(agent_list) else ""
        areas = customers[customers["Agent Name"] == (agent_list[0] if len(agent_list) else "")]["Area"].dropna().unique()
        st.session_state.area_select = areas[0] if len(areas) else ""
        provinces = customers[
            (customers["Agent Name"] == (agent_list[0] if len(agent_list) else "")) &
            (customers["Area"] == (areas[0] if len(areas) else ""))
        ]["Province"].dropna().unique()
        if len(provinces) == 1:
            st.session_state.province_display = provinces[0]
        else:
            st.session_state.province_select = provinces[0] if len(provinces) else ""
        st.session_state.customer_multi = []
        st.session_state.visit_date = date.today()
        st.session_state.visit_notes = ""
        st.session_state.close_select = "No"

    with st.form("visit_form", clear_on_submit=True):
        agent_name = st.selectbox("Agent Name", agent_list if len(agent_list) else [""], key="agent_select")
        areas = customers[customers["Agent Name"] == agent_name]["Area"].dropna().unique()
        area = st.selectbox("Area", areas if len(areas) else [""], key="area_select")
        provinces = customers[(customers["Agent Name"] == agent_name) & (customers["Area"] == area)]["Province"].dropna().unique()
        if len(provinces) == 1:
            province = provinces[0]
            st.text_input("Province", province, key="province_display", disabled=True)
        else:
            province = st.selectbox("Province", provinces if len(provinces) else [""], key="province_select")
        customers_in_area = customers[
            (customers["Agent Name"] == agent_name) & (customers["Area"] == area)
        ]
        customers_in_area = customers_in_area.drop_duplicates(subset=["Trading Name"])
        open_customers = [
            row['Trading Name']
            for idx, row in customers_in_area.iterrows()
            if not is_customer_closed(row['Agent Name'], row['Trading Name'], row['Area'], closed_accounts_df)
        ]
        selected_customers = st.multiselect("Select Customers (multiple)", open_customers, key="customer_multi")
        visit_date = st.date_input("Visit Date", date.today(), key="visit_date")
        notes = st.text_input("Notes (optional)", placeholder="Add notes about this visit", key="visit_notes")
        closed_account = st.selectbox("Closed Account (applies to ALL selected)", ["No", "Yes"], key="close_select")
        submitted = st.form_submit_button("Add Visit", disabled=not selected_customers, on_click=clear_form)

    if submitted:
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

# ... (dashboard and closed accounts code remains unchanged, as above)
