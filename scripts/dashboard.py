import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.message import EmailMessage
import ssl

# --- Load Data ---
try:
    customers = pd.read_csv('customers.csv')
    visits = pd.read_csv('visits.csv', parse_dates=['Visit Date'])
except Exception as e:
    st.error(f"Error loading CSV files: {e}")
    st.stop()

# --- Sidebar Filters ---
agent_list = ['All'] + sorted(customers['Agent Name'].dropna().astype(str).unique().tolist())
area_list = ['All'] + sorted(customers['Area'].dropna().astype(str).unique().tolist())

agent = st.sidebar.selectbox('Select Agent', agent_list)
area = st.sidebar.selectbox('Select Area', area_list)
if not visits.empty and 'Visit Date' in visits.columns:
    year_list = sorted(visits['Visit Date'].dropna().dt.year.unique().tolist())
    year = st.sidebar.selectbox('Select Year', year_list)
else:
    year = datetime.now().year
quarter = st.sidebar.selectbox('Select Quarter', [1, 2, 3, 4])

# --- Filtering Logic ---
def filter_data(agent, area, year, quarter):
    df = visits.copy()
    if agent != 'All':
        df = df[df['Agent Name'] == agent]
    if area != 'All':
        df = df[df['Area'] == area]
    if 'Visit Date' in df.columns:
        df = df[df['Visit Date'].dt.year == year]
        df = df[df['Visit Date'].dt.quarter == quarter]
    return df

months_quarters = {1: ['Jan','Feb','Mar'], 2: ['Apr','May','Jun'], 3: ['Jul','Aug','Sep'], 4: ['Oct','Nov','Dec']}
months_numbers = {1: [1,2,3], 2: [4,5,6], 3: [7,8,9], 4: [10,11,12]}
filtered_visits = filter_data(agent, area, year, quarter)

# --- Prepare Report Table ---
report = []
for _, cust in customers.iterrows():
    if (agent != 'All' and str(cust['Agent Name']) != str(agent)) or \
       (area != 'All' and str(cust['Area']) != str(area)):
        continue
    row = [cust['Agent Name'], cust['Trading Name'], cust['Area']]
    for m in months_numbers[quarter]:
        month_visits = filtered_visits[
            (filtered_visits['Trading Name'] == cust['Trading Name']) &
            (filtered_visits['Agent Name'] == cust['Agent Name']) &
            (filtered_visits['Area'] == cust['Area']) &
            (filtered_visits['Visit Date'].dt.month == m)
        ]
        if not month_visits.empty:
            days = month_visits['Visit Date'].dt.day.astype(str).tolist()
            row.append(f"{len(days)} ({', '.join(days)})")
        else:
            row.append("0")
    report.append(row)
columns = ['Agent Name', 'Trading Name', 'Area'] + months_quarters[quarter]
report_df = pd.DataFrame(report, columns=columns)

st.title("Customer Visit Dashboard")
st.markdown("**Filter by agent, area, year, quarter. Download or email the report below.**")
st.dataframe(report_df)

# --- Download Button ---
csv = report_df.to_csv(index=False).encode('utf-8')
st.download_button(
    "Download filtered report as CSV",
    csv,
    "filtered_report.csv",
    "text/csv",
    key='download-csv'
)

# --- Email Report Section ---
st.markdown("### Email This Report")
with st.form("email_form"):
    email_to = st.text_input("Recipient Email")
    email_from = st.text_input("Your Email (Gmail recommended)")
    email_password = st.text_input("Your Email Password (App Password recommended)", type="password")
    submit_email = st.form_submit_button("Send report by email")
    email_status = st.empty()

if submit_email:
    if not email_to or not email_from or not email_password:
        st.error("Please enter all email details.")
    else:
        try:
            msg = EmailMessage()
            msg["Subject"] = "Your Customer Visit Report"
            msg["From"] = email_from
            msg["To"] = email_to
            msg.set_content("Attached is your requested customer visit report.")
            msg.add_attachment(csv, maintype='text', subtype='csv', filename="filtered_report.csv")

            context = ssl.create_default_context()
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
                server.login(email_from, email_password)
                server.send_message(msg)
            st.success(f"Report sent to {email_to}")
        except Exception as e:
            st.error(f"Error sending email: {e}")
