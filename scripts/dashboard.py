import streamlit as st
import pandas as pd
from datetime import date

CUSTOMERS_CSV = "customers.csv"

def load_customers():
    try:
        return pd.read_csv(CUSTOMERS_CSV)
    except Exception as e:
        st.error(f"Error loading {CUSTOMERS_CSV}: {e}")
        return pd.DataFrame(columns=['Agent Name', 'Trading Name', 'Area', 'Province'])

customers = load_customers()

st.title("Demo: Area Filters Per Agent")

# Agent filter
agent_list = customers["Agent Name"].dropna().unique().tolist()
agent = st.selectbox("Agent Name", agent_list, key="agent_select")

# Area filter, filtered by Agent
areas = customers[customers["Agent Name"] == agent]["Area"].dropna().unique().tolist()
area = st.selectbox("Area", areas, key="area_select")

# Province filter, filtered by Agent and Area
provinces = customers[(customers["Agent Name"] == agent) & (customers["Area"] == area)]["Province"].dropna().unique().tolist()
if len(provinces) == 1:
    st.text_input("Province", provinces[0], key="province_display", disabled=True)
elif len(provinces) > 1:
    st.selectbox("Province", provinces, key="province_select")

# (Rest of your form...)
