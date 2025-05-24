import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import os
import hashlib

# ====================== CONFIGURATION ======================
CUSTOMERS_CSV = "customers.csv"
VISITS_CSV = "visits.csv"
PAGE_TITLE = "SIMA Customer Visits"
PAGE_ICON = "👁️"
DATE_FORMAT = "%Y-%m-%d"

# ====================== SESSION STATE ======================
if "custom_tab" not in st.session_state:
    st.session_state["custom_tab"] = "visit"
if "filter_visits" not in st.session_state:
    st.session_state["filter_visits"] = None

# ====================== CSS STYLING ======================
def inject_css():
    st.markdown(f"""
    <style>
        /* Base Styles */
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #333;
        }}
        
        /* Header Styles */
        .big-title {{
            font-size: 2.3rem !important; 
            color: #ff3c00 !important; 
            font-weight: 900;
            text-align: center; 
            margin-bottom: 0.5rem; 
            margin-top: 1.1rem;
            letter-spacing: 0.03em;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.1);
        }}
        
        .subtitle {{
            font-size: 1.1rem; 
            color: #0C2D48; 
            text-align: center;
            margin-bottom: 2rem; 
            margin-top: 0.6rem;
            opacity: 0.9;
        }}
        
        /* Tab Styles */
        .my-tabs-container {{
            display: flex;
            justify-content: center;
            align-items: end;
            gap: 32px;
            margin-top: 32px;
            margin-bottom: 0px;
            border-bottom: 1px solid #e1e4e8;
            padding-bottom: 4px;
        }}
        
        .my-tab {{
            background: none;
            border: none;
            outline: none;
            font-size: 1.15rem;
            font-weight: 700;
            color: #145DA0;
            padding: 8px 34px 4px 34px;
            margin-bottom: 0;
            cursor: pointer;
            position: relative;
            transition: all 0.2s ease;
            border-radius: 4px 4px 0 0;
        }}
        
        .my-tab.selected {{
            color: #ff3c00;
            font-weight: 900;
            background-color: rgba(255, 60, 0, 0.08);
        }}
        
        .my-tab.selected:after {{
            content: "";
            display: block;
            margin: 0 auto;
            margin-top: 5px;
            width: 50%;
            height: 3px;
            background: #ff3c00;
            border-radius: 2px;
            box-shadow: 0 2px 4px rgba(255, 60, 0, 0.2);
        }}
        
        .my-tab:not(.selected):hover {{
            color: #2e86de;
            background-color: rgba(46, 134, 222, 0.08);
        }}
        
        /* Form Styles */
        .form-container {{
            background: #f8fafc;
            border-radius: 12px;
            padding: 1.8rem 2rem;
            margin: 0 auto 2rem auto;
            max-width: 950px;
            width: 100%;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid #e1e4e8;
        }}
        
        /* Button Styles */
        .stButton>button, .stDownloadButton>button {{
            background: linear-gradient(90deg, #145DA0 0%, #0C2D48 100%);
            color: white; 
            font-size: 16px; 
            font-weight: 600;
            border-radius: 8px; 
            padding: 10px 24px; 
            border: none; 
            margin: 8px 0px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: all 0.15s;
        }}
        
        .stButton>button:hover, .stDownloadButton>button:hover {{
            background: linear-gradient(90deg, #2e86de 0%, #0C2D48 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .stButton>button:active, .stDownloadButton>button:active {{
            transform: translateY(0);
        }}
        
        /* Data Table Styles */
        .stDataFrame {{
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        /* Input Styles */
        .stSelectbox, .stTextInput, .stDateInput {{
            margin-bottom: 1rem;
        }}
        
        label, .css-1c7y2kd, .css-1ofwbyh, .css-1q8dd3e {{
            color: #145DA0 !important;
            font-weight: 600 !important;
        }}
        
        .stSelectbox>div>div>div>div {{
            background-color: #f4f8fc !important;
            border: 1px solid #d0d7de !important;
        }}
        
        /* Closed Account Styles */
        .closed-account-row {{
            background-color: #fff0f0 !important;
            color: #d32f2f !important;
            font-weight: 500;
        }}
        
        .warning-box {{
            background-color: #fff8e1;
            border-left: 4px solid #ffc107;
            padding: 12px 16px;
            border-radius: 0 4px 4px 0;
            margin: 1rem 0;
        }}
        
        /* Responsive Styles */
        @media (max-width: 900px) {{
            .form-container {{
                padding: 1.2rem;
            }}
            
            .my-tabs-container {{
                gap: 16px;
            }}
        }}
        
        @media (max-width: 600px) {{
            .form-container {{
                padding: 0.8rem;
            }}
            
            .big-title {{
                font-size: 1.8rem !important;
            }}
            
            .my-tab {{
                font-size: 1rem; 
                padding: 6px 12px;
            }}
            
            .stButton>button, .stDownloadButton>button {{
                width: 100%;
            }}
        }}
    </style>
    """, unsafe_allow_html=True)

# ====================== HELPER FUNCTIONS ======================
@st.cache_data(ttl=300)
def load_customers():
    try:
        if os.path.exists(CUSTOMERS_CSV):
            return pd.read_csv(CUSTOMERS_CSV)
        return pd.DataFrame(columns=['Agent Name', 'Trading Name', 'Area'])
    except Exception as e:
        st.error(f"Error loading customers: {e}")
        return pd.DataFrame(columns=['Agent Name', 'Trading Name', 'Area'])

@st.cache_data(ttl=60)
def load_visits():
    try:
        if os.path.exists(VISITS_CSV):
            visits = pd.read_csv(VISITS_CSV)
            # Ensure required columns exist
            required_cols = ['Agent Name', 'Trading Name', 'Area', 'Visit Date', 'Notes', 'Closed Account']
            for col in required_cols:
                if col not in visits.columns:
                    visits[col] = "" if col == "Notes" else "No" if col == "Closed Account" else pd.NA
            
            # Convert and validate dates
            if 'Visit Date' in visits.columns:
                visits['Visit Date'] = pd.to_datetime(visits['Visit Date'], errors='coerce')
                today = pd.Timestamp.now().normalize()
                visits = visits[visits['Visit Date'] <= today]
            
            return visits
        return pd.DataFrame(columns=['Agent Name', 'Trading Name', 'Area', 'Visit Date', 'Notes', 'Closed Account'])
    except Exception as e:
        st.error(f"Error loading visits: {e}")
        return pd.DataFrame(columns=['Agent Name', 'Trading Name', 'Area', 'Visit Date', 'Notes', 'Closed Account'])

def save_visit(new_visit):
    try:
        if os.path.exists(VISITS_CSV):
            new_visit.to_csv(VISITS_CSV, mode='a', header=False, index=False)
        else:
            new_visit.to_csv(VISITS_CSV, mode='w', header=True, index=False)
        st.session_state["filter_visits"] = None  # Clear cached filtered visits
        return True
    except Exception as e:
        st.error(f"Error saving visit: {e}")
        return False

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

def generate_visit_id(visit_data):
    """Generate a unique ID for each visit based on its data"""
    data_str = f"{visit_data['Agent Name']}_{visit_data['Trading Name']}_{visit_data['Area']}_{visit_data['Visit Date']}"
    return hashlib.md5(data_str.encode()).hexdigest()

# ====================== PAGE SETUP ======================
st.set_page_config(page_title=PAGE_TITLE, layout="wide", page_icon=PAGE_ICON)
inject_css()

# ====================== TAB NAVIGATION ======================
st.markdown("""
<style>
    .tab-row {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin: 20px 0;
    }
    .tab-button {
        background: none;
        border: none;
        font-size: 1.1rem;
        font-weight: 600;
        padding: 8px 20px;
        cursor: pointer;
        color: #145DA0;
        border-bottom: 3px solid transparent;
        transition: all 0.2s;
    }
    .tab-button.active {
        color: #ff3c00;
        border-bottom: 3px solid #ff3c00;
    }
    .tab-button:hover:not(.active) {
        color: #2e86de;
    }
</style>
""", unsafe_allow_html=True)

# Create tabs
col1, col2 = st.columns(2)
with col1:
    if st.button("Log a Visit", key="tab_visit"):
        st.query_params["tab"] = "visit"
with col2:
    if st.button("Dashboard", key="tab_dashboard"):
        st.query_params["tab"] = "dashboard"

# Get current tab from query params
current_tab = st.query_params.get("tab", ["visit"])[0]

# ====================== VISIT LOGGING TAB ======================
if current_tab == "visit":
    st.markdown('<div class="big-title">LOG A VISIT</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Track your customer interactions. Mark accounts as closed when needed.</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        
        customers = load_customers()
        visits = load_visits()
        closed_accounts_df = get_closed_accounts_df(visits)
        
        # Form Columns
        cols = st.columns([1, 1, 1])
        agent_name = cols[0].selectbox(
            "Agent Name *",
            customers["Agent Name"].dropna().unique(),
            key="visit_agent",
            help="Select the agent who made the visit"
        )
        
        # Get customers for selected agent
        agent_customers = customers[customers["Agent Name"] == agent_name]
        
        # Separate open and closed accounts
        trading_names_open = []
        trading_names_closed = []
        
        for _, row in agent_customers.iterrows():
            if is_customer_closed(row['Agent Name'], row['Trading Name'], row['Area'], closed_accounts_df):
                trading_names_closed.append(row['Trading Name'])
            else:
                trading_names_open.append(row['Trading Name'])
        
        # Format display names
        trading_names_display = trading_names_open.copy()
        if trading_names_closed:
            trading_names_display += [f"❌ {name} (Closed)" for name in trading_names_closed]
        
        trading_name = cols[1].selectbox(
            "Trading Name *",
            trading_names_display,
            key="visit_trading",
            help="Select the customer visited. Closed accounts are marked with ❌"
        )
        
        # Determine if selected customer is closed
        is_closed = trading_name.startswith("❌")
        original_name = trading_name.replace("❌ ", "").replace(" (Closed)", "") if is_closed else trading_name
        
        # Auto-fill area
        area = agent_customers[agent_customers["Trading Name"] == original_name]["Area"].values[0] if original_name in agent_customers["Trading Name"].values else ""
        cols[2].text_input("Area", area, disabled=True, key="area_text")
        
        # Visit details
        visit_date = st.date_input("Visit Date *", date.today(), key="visit_date")
        notes = st.text_area("Notes", key="visit_notes", placeholder="Enter details about the visit...", height=100)
        closed_account = st.selectbox("Account Status *", ["No", "Yes"], key="closed_account_select", 
                                    help="Mark 'Yes' if this visit resulted in closing the account")
        
        # Validation and submission
        can_submit = not is_closed
        add_btn = st.button("📝 Log Visit", disabled=not can_submit, type="primary")
        
        if is_closed:
            st.markdown(
                '<div class="warning-box">'
                '⚠️ This is a closed account. You cannot log new visits for closed accounts.'
                '</div>', 
                unsafe_allow_html=True
            )
        
        if add_btn and can_submit:
            if visit_date > date.today():
                st.error("Visit date cannot be in the future!")
            else:
                new_visit = pd.DataFrame([{
                    "Agent Name": agent_name,
                    "Trading Name": trading_name if not is_closed else original_name,
                    "Area": area,
                    "Visit Date": visit_date.strftime(DATE_FORMAT),
                    "Notes": notes,
                    "Closed Account": closed_account
                }])
                
                if save_visit(new_visit):
                    st.success("✅ Visit logged successfully!")
                    st.balloons()
                    # Clear form
                    st.session_state["visit_notes"] = ""
                    st.session_state["closed_account_select"] = "No"
        
        st.markdown('</div>', unsafe_allow_html=True)

# ====================== DASHBOARD TAB ======================
elif current_tab == "dashboard":
    st.markdown('<div class="big-title">VISIT DASHBOARD</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Analyze and export customer visit records</div>', unsafe_allow_html=True)
    
    customers = load_customers()
    visits = load_visits()
    closed_accounts_df = get_closed_accounts_df(visits)
    
    # Dashboard Filters
    with st.container():
        filter1, filter2, filter3, filter4, filter5 = st.columns([1.8, 1.8, 1.8, 1.8, 2])
        
        with filter1:
            agent_list = ['All Agents'] + sorted(customers['Agent Name'].dropna().astype(str).unique().tolist())
            agent = st.selectbox('Agent', agent_list, key='dashboard_agent')
        
        with filter2:
            if agent != 'All Agents':
                area_list = ['All Areas'] + sorted(customers[customers['Agent Name'] == agent]['Area'].dropna().astype(str).unique().tolist())
            else:
                area_list = ['All Areas'] + sorted(customers['Area'].dropna().astype(str).unique().tolist())
            area = st.selectbox('Area', area_list, key='dashboard_area')
        
        with filter3:
            view_mode = st.selectbox("View Mode", ["Daily", "Date Range", "Quarterly"], key="view_mode_select")
        
        with filter4:
            if view_mode == "Daily":
                selected_date = st.date_input("Date", value=date.today(), key="dashboard_day")
            elif view_mode == "Date Range":
                default_end = date.today()
                default_start = default_end - timedelta(days=30)
                start_date = st.date_input("Start Date", value=default_start, key="dashboard_start")
                end_date = st.date_input("End Date", value=default_end, key="dashboard_end")
            else:
                if not visits.empty and 'Visit Date' in visits.columns:
                    year_list = sorted(visits['Visit Date'].dropna().dt.year.unique().tolist())
                    if not year_list:
                        year_list = [datetime.now().year]
                    year = st.selectbox('Year', year_list, key='dashboard_year')
                else:
                    year = datetime.now().year
                quarter = st.selectbox('Quarter', [1, 2, 3, 4], key="dashboard_quarter")
        
        with filter5:
            st.write("")  # Spacer
    
    # Apply filters
    filtered = visits.copy()
    if agent != 'All Agents':
        filtered = filtered[filtered['Agent Name'] == agent]
    if area != 'All Areas':
        filtered = filtered[filtered['Area'] == area]
    
    if view_mode == "Daily":
        filtered = filtered[filtered["Visit Date"].dt.date == selected_date]
        view_title = f"Visits on {selected_date.strftime('%B %d, %Y')}"
    elif view_mode == "Date Range":
        filtered = filtered[
            (filtered["Visit Date"].dt.date >= start_date) &
            (filtered["Visit Date"].dt.date <= end_date)
        ]
        view_title = f"Visits from {start_date.strftime('%b %d')} to {end_date.strftime('%b %d, %Y')}"
    else:
        filtered = filtered[
            (filtered["Visit Date"].dt.year == year) &
            (filtered["Visit Date"].dt.quarter == quarter)
        ]
        view_title = f"Visits for Q{quarter} {year}"
    
    # Display results
    st.subheader(view_title)
    
    if not filtered.empty:
        # Format the display DataFrame
        def format_row(row):
            is_closed = is_customer_closed(
                row['Agent Name'], 
                row['Trading Name'], 
                row['Area'], 
                closed_accounts_df
            )
            
            formatted = row.copy()
            formatted['Visit Date'] = row['Visit Date'].strftime('%Y-%m-%d')
            
            if is_closed:
                formatted['Trading Name'] = f"❌ {row['Trading Name']}"
                if row.get('Notes'):
                    formatted['Notes'] = f"(Closed) {row['Notes']}"
                else:
                    formatted['Notes'] = "(Closed account)"
            
            return formatted
        
        display_df = filtered.apply(format_row, axis=1)
        display_df = display_df[['Agent Name', 'Trading Name', 'Area', 'Visit Date', 'Notes']]
        
        # Apply styling
        def highlight_closed(row):
            is_closed = "❌" in str(row['Trading Name'])
            return ['background-color: #fff0f0; color: #d32f2f' if is_closed else ''] * len(row)
        
        # Calculate appropriate height for the dataframe
        table_height = min(600, (len(filtered) + 1) * 35 + 3)
        
        # Display the styled dataframe
        st.dataframe(
            display_df.style.apply(highlight_closed, axis=1),
            use_container_width=True,
            hide_index=True,
            height=table_height
        )
        
        # Download button
        csv = filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            "💾 Download CSV",
            csv,
            f"visits_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            "text/csv",
            key='download-csv'
        )
    else:
        st.info("No visits found matching your criteria.")
