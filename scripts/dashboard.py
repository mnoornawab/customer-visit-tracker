import streamlit as st
import pandas as pd
from datetime import date

CUSTOMERS_CSV = "customers.csv"
VISITS_CSV = "visits.csv"
CLOSED_ACCOUNTS_CSV = "closed_accounts.csv"

def load_customers():
    df = pd.read_csv(CUSTOMERS_CSV, dtype=str)
    for col in ['Agent Name', 'Trading Name', 'Area', 'Province']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    # Remove rows with missing agent or area
    df = df[df['Agent Name'].notna() & (df['Agent Name'] != "")]
    df = df[df['Area'].notna() & (df['Area'] != "")]
    return df

def load_closed_accounts():
    if not pd.io.common.file_exists(CLOSED_ACCOUNTS_CSV):
        return pd.DataFrame(columns=['Agent Name', 'Trading Name', 'Area'])
    df = pd.read_csv(CLOSED_ACCOUNTS_CSV, dtype=str)
    for col in ['Agent Name', 'Trading Name', 'Area']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    return df

def is_customer_closed(agent, trading_name, area, closed_accounts_df):
    if closed_accounts_df.empty:
        return False
    mask = (
        (closed_accounts_df['Agent Name'] == agent) &
        (closed_accounts_df['Trading Name'] == trading_name) &
        (closed_accounts_df['Area'] == area)
    )
    return closed_accounts_df[mask].shape[0] > 0

def log_visits(rows):
    visits_exist = pd.io.common.file_exists(VISITS_CSV)
    new_visits_df = pd.DataFrame(rows)
    if visits_exist:
        new_visits_df.to_csv(VISITS_CSV, mode="a", header=False, index=False)
    else:
        new_visits_df.to_csv(VISITS_CSV, mode="w", header=True, index=False)

st.set_page_config(page_title="SIMA Customer Visits", layout="wide", page_icon="👁️")

st.title("Log a Visit")

customers = load_customers()
closed_accounts_df = load_closed_accounts()

# --- Step 1: Select Agent ---
agent_list = customers["Agent Name"].dropna().unique().tolist()
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

selected_customers = st.multiselect("Select Customers (multiple)", open_customers, key="customer_multi")
visit_date = st.date_input("Visit Date", date.today(), key="visit_date")
notes = st.text_input("Notes (optional)", placeholder="Add notes about this visit", key="visit_notes")
closed_account = st.selectbox("Closed Account (applies to ALL selected)", ["No", "Yes"], key="close_select")

# --- Step 5: Add Visit Button (enabled only if customers selected) ---
add_visit_disabled = not selected_customers

if st.button("Add Visit", disabled=add_visit_disabled):
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
    log_visits(visit_rows)
    st.success(f"Logged {len(visit_rows)} visits for {agent_name} in {area}.")
    st.balloons()
