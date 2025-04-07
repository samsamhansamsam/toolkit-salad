import streamlit as st
import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# --- Page Setup ---
st.set_page_config(page_title="Service Usage Dashboard", layout="wide")
st.title("Weekly Service Usage Dashboard")

# --- Connect to Railway MySQL ---
@st.cache_data
def load_data():
    conn = mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        port=st.secrets["mysql"]["port"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"]
    )
    
    query = """
    SELECT
        msu.shop_id,
        s.service_name,
        snap.snapshot_date
    FROM mall_service_usage msu
    JOIN services s ON msu.service_id = s.service_id
    JOIN snapshots snap ON msu.snapshot_id = snap.snapshot_id
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

df = load_data()

# --- Data Preparation ---
df['snapshot_date'] = pd.to_datetime(df['snapshot_date'])
pivot = df.groupby(['snapshot_date', 'service_name'])['shop_id'].nunique().unstack(fill_value=0)

# Calculate percentage for each snapshot (each row sums to 100%)
pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

# --- 1. Line Chart: Weekly Trend by Service (Percentage) ---
st.subheader("Weekly Trend by Service (Percentage)")
fig, ax = plt.subplots(figsize=(10, 6))
for service in pivot_pct.columns:
    ax.plot(pivot_pct.index, pivot_pct[service], marker='o', label=service)

ax.set_title("Percentage of Active Shops per Service (Weekly)")
ax.set_xlabel("Snapshot Date")
ax.set_ylabel("Percentage (%)")
ax.legend(title="Service", bbox_to_anchor=(1.05, 1), loc='upper left')
ax.grid(True)

# Limit the x-axis to the actual data range
min_date = pivot_pct.index.min()
max_date = pivot_pct.index.max()
ax.set_xlim([min_date, max_date])

# Format the x-axis to show dates at 7-day intervals
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
plt.xticks(rotation=45)

st.pyplot(fig)

# --- 2. Bar Chart: Snapshot Comparison ---
st.subheader("Snapshot Comparison")
if len(pivot) >= 3:
    latest = pivot.iloc[-1]
    previous = pivot.iloc[-2]
    before_previous = pivot.iloc[-3]
else:
    latest = pivot.iloc[-1]
    previous = pivot.iloc[-2] if len(pivot) >= 2 else latest
    before_previous = latest

overall_avg = pivot.mean()

comparison_df = pd.DataFrame({
    'Latest': latest,
    'Previous': previous,
    'Before Previous': before_previous,
    'Overall Average': overall_avg
})

services = comparison_df.index.tolist()
x = range(len(services))
width = 0.2

fig2, ax2 = plt.subplots(figsize=(12, 6))
ax2.bar([p - 1.5*width for p in x], comparison_df['Latest'], width, label='Latest')
ax2.bar([p - 0.5*width for p in x], comparison_df['Previous'], width, label='Previous')
ax2.bar([p + 0.5*width for p in x], comparison_df['Before Previous'], width, label='Before Previous')
ax2.bar([p + 1.5*width for p in x], comparison_df['Overall Average'], width, label='Overall Average')

ax2.set_xticks(x)
ax2.set_xticklabels(services, rotation=45, ha="right")
ax2.set_xlabel("Service")
ax2.set_ylabel("Number of Active Shops")
ax2.set_title("Service Usage Comparison Across Snapshots")
ax2.legend()
ax2.grid(True)
st.pyplot(fig2)
