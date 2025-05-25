import streamlit as st
import pandas as pd
from datetime import date
import os

CUSTOMERS_CSV = "customers.csv"
VISITS_CSV = "visits.csv"
CLOSED_ACCOUNTS_CSV = "closed_accounts.csv"

def load_customers():
    return pd.read_csv(CUSTOMERS_CSV)

def load_closed_accounts():
    if os.path.exists(CLOSED_ACCOUNTS_CSV):
        return pd.read_csv(CLOSED_ACCOUNTS_CSV)
    else:
        return pd.DataFrame(columns=['Agent Name', 'Trading Name', 'Area'])

def is_customer_closed(agent, trading_name, area, closed_accounts_df):
    if closed_accounts_df.empty:
        return False
    q = (closed_accounts_df['Agent Name'] == agent) & \
        (closed_accounts_df['Trading Name'] == trading_name) & \
        (closed_accounts_df['Area'] == area)
    return closed_accounts_df[q].shape[0] > 0

def add_closed_account(agent, trading_name, area):
    df = load_closed_accounts()
    exists = ((df['Agent Name'] == agent) &
              (df['Trading Name'] == trading_name) &
              (df['Area'] == area)).any()
    if not exists:
        df2 = pd.DataFrame([{'Agent Name': agent, 'Trading Name': trading_name, 'Area': area}])
        df = pd.concat([df, df2], ignore_index=True)
        df.to_csv(CLOSED_ACCOUNTS_CSV, index=False)

def log_visits(rows):
    visits_exist = os.path.exists(VISITS_CSV)
    new_visits_df = pd.DataFrame(rows)
    if visits_exist:
        new_visits_df.to_csv(VISITS_CSV, mode="a", header=False, index=False)
    else:
        new_visits_df.to_csv(VISITS_CSV, mode="w", header=True, index=False)

# --- UI ---
st.markdown("<h2 style='color:#ff3c00; text-align:center; font-weight:900;'>LOG A VISIT</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Log your customer visits below. Select multiple customers for the same agent/area/date.</p>", unsafe_allow_html=True)
st.write("")

customers = load_customers()
closed_accounts_df = load_closed_accounts()

# Step 1: Agent Name
agent_name = st.selectbox("Agent Name", customers["Agent Name"].dropna().unique())

# Step 2: Area (per Agent)
areas = customers[customers["Agent Name"] == agent_name]["Area"].dropna().unique()
area = st.selectbox("Area", areas)

# Step 3: Customer Multi-select (only open customers for agent+area, no duplicates)
customers_in_area = customers[
    (customers["Agent Name"] == agent_name) & (customers["Area"] == area)
]

# Remove duplicates by Trading Name (keep only first occurrence)
customers_in_area = customers_in_area.drop_duplicates(subset=["Trading Name"])

# Only include open customers
open_customers = [
    row['Trading Name']
    for idx, row in customers_in_area.iterrows()
    if not is_customer_closed(row['Agent Name'], row['Trading Name'], row['Area'], closed_accounts_df)
]

selected_customers = st.multiselect("Select Customers (multiple)", open_customers)

# Step 4: Visit Date / Notes / Closed Account
visit_date = st.date_input("Visit Date", date.today())
notes = st.text_input("Notes (optional)", placeholder="Add notes about this visit")
closed_account = st.selectbox("Closed Account (applies to ALL selected)", ["No", "Yes"])

add_btn = st.button("Add Visit", disabled=not selected_customers)

if add_btn:
    visit_rows = []
    for trading_name in selected_customers:
        visit_rows.append({
            "Agent Name": agent_name,
            "Trading Name": trading_name,
            "Area": area,
            "Visit Date": visit_date,
            "Notes": notes,
            "Closed Account": closed_account
        })
        if closed_account == "Yes":
            add_closed_account(agent_name, trading_name, area)
    log_visits(visit_rows)
    st.success(f"Logged {len(visit_rows)} visits for {agent_name} in {area}.")
    st.balloons()
