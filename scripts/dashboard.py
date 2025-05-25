import streamlit as st
import pandas as pd

# Simulated customers data
data = [
    {"Agent Name": "Anika", "Trading Name": "CustomerA", "Area": "POLOKWANE", "Province": "LIMPOPO"},
    {"Agent Name": "Anika", "Trading Name": "CustomerB", "Area": "JOHANNESBURG", "Province": "GAUTENG"},
    {"Agent Name": "John", "Trading Name": "CustomerC", "Area": "CAPE TOWN", "Province": "WESTERN CAPE"},
    {"Agent Name": "John", "Trading Name": "CustomerD", "Area": "POLOKWANE", "Province": "LIMPOPO"},
]
customers = pd.DataFrame(data)

st.title("Demo: Dynamic Area per Agent")

customers['Agent Name'] = customers['Agent Name'].astype(str).str.strip()
customers['Area'] = customers['Area'].astype(str).str.strip()

agent_list = customers['Agent Name'].dropna().unique().tolist()
agent = st.selectbox("Agent Name", agent_list, key="agent_select")

areas = customers[customers['Agent Name'] == agent]['Area'].dropna().unique().tolist()
area = st.selectbox("Area", areas, key=f"area_select_{agent}")

st.write(f"You picked agent: {agent} and area: {area}")
