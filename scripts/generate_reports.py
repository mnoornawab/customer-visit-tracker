import pandas as pd
import os
from datetime import datetime

# Read data
customers = pd.read_csv('customers.csv')
visits = pd.read_csv('visits.csv', parse_dates=['Visit Date'])

# Helper functions
def get_quarter(month):
    return ((month - 1) // 3) + 1

def filter_data(agent=None, area=None, province=None, year=None, quarter=None):
    df = visits.copy()
    if agent:
        df = df[df['Agent Name'] == agent]
    if area:
        df = df[df['Area'] == area]
    if province:
        df = df[df['Province'] == province]
    if year:
        df = df[df['Visit Date'].dt.year == year]
    if quarter:
        df = df[df['Visit Date'].dt.quarter == quarter]
    return df

def make_report(filtered_visits, customers, months_in_quarter, output_file):
    # Merge to include all customers (even those with 0 visits)
    merged = pd.merge(customers, filtered_visits, on=['Agent Name','Trading Name','Area','Province'], how='left')

    report_rows = []
    for _, row in merged.iterrows():
        customer_info = [row['Agent Name'], row['Trading Name'], row['Area'], row['Province']]
        visits_per_month = []
        for m in months_in_quarter:
            month_visits = merged[(merged['Trading Name'] == row['Trading Name']) &
                                  (merged['Agent Name'] == row['Agent Name']) &
                                  (merged['Area'] == row['Area']) &
                                  (merged['Province'] == row['Province']) &
                                  (merged['Visit Date'].dt.month == m) if pd.notnull(row['Visit Date']) else False]
            if not month_visits.empty:
                # List visit days
                days = month_visits['Visit Date'].dt.day.dropna().astype(int).tolist()
                visits_per_month.append(f"{len(days)} ({', '.join(map(str, days))})")
            else:
                visits_per_month.append("0")
        report_rows.append(customer_info + visits_per_month)
    
    # Write to CSV
    columns = ['Agent Name', 'Trading Name', 'Area', 'Province'] + [datetime(2000, m, 1).strftime('%b') for m in months_in_quarter]
    df_report = pd.DataFrame(report_rows, columns=columns)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df_report.to_csv(output_file, index=False)
    print(f"Report saved to {output_file}")

# Example usage (for Q1 2025, Karachi area)
if __name__ == "__main__":
    # Change these as needed
    AGENT = None        # e.g., 'Agent1' or None for all
    AREA = None         # e.g., 'Karachi' or None for all
    PROVINCE = None     # e.g., 'Sindh' or None for all
    YEAR = 2025
    QUARTER = 1         # 1=Q1, 2=Q2, etc.

    # Months in the selected quarter
    months_quarters = {1: [1,2,3], 2: [4,5,6], 3: [7,8,9], 4: [10,11,12]}
    months = months_quarters[QUARTER]

    filtered = filter_data(AGENT, AREA, PROVINCE, YEAR, QUARTER)
    make_report(filtered, customers, months, f'reports/{AREA or "all"}_{PROVINCE or "all"}_{AGENT or "all"}_Q{QUARTER}_{YEAR}.csv')