import streamlit as st
import pandas as pd

customers = pd.read_csv("customers.csv", dtype=str)
customers['Agent Name'] = customers['Agent Name'].astype(str).str.strip()
customers['Area'] = customers['Area'].astype(str).str.strip()

agent_list = customers['Agent Name'].dropna()
agent_list = agent_list[agent_list != ''].unique().tolist()
agent = st.selectbox("Agent Name", agent_list, key="agent_select")

areas = customers[customers['Agent Name'] == agent]['Area'].dropna()
areas = areas[areas != ''].unique().tolist()
area = st.selectbox("Area", areas, key=f"area_select_{agent}")

st.write("You selected:", agent, area)
