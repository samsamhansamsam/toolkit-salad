import streamlit as st
import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt

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
# Convert snapshot_date to datetime if not already
df['snapshot_date'] = pd.to_datetime(df['snapshot_date'])

# Create pivot table: count of unique shop_id per snapshot_date per service
pivot = df.groupby(['snapshot_date', 'service_name'])['shop_id'].nunique().unstack(fill_value=0)

# --- 1. Weekly Trend by Service (Last 2 Weeks, Percentage) ---
# Subset for the last 2 weeks
two_week_pivot = pivot.tail(2)

# Calculate row-wise percentages (each week totals 100%)
two_week_pct = two_week_pivot.div(two_week_pivot.sum(axis=1), axis=0) * 100

st.subheader("Weekly Trend by Service (Last 2 Weeks, Percentage)")
fig, ax = plt.subplots(figsize=(10, 6))
for service in two_week_pct.columns:
    ax.plot(two_week_pct.index, two_week_pct[service], marker='o', label=service)

ax.set_title("Percentage of Active Shops per Service (Last 2 Weeks)")
ax.set_xlabel("Snapshot Date")
ax.set_ylabel("Percentage (%)")
ax.legend(title="Service", bbox_to_anchor=(1.05, 1), loc='upper left')
ax.grid(True)
st.pyplot(fig)

# --- 2. Snapshot Comparison: Latest vs Previous vs Before Previous vs Overall Average ---
st.subheader("Snapshot Comparison")

# Check if there are at least 3 snapshots; if not, use available data
if len(pivot) >= 3:
    latest = pivot.iloc[-1]
    previous = pivot.iloc[-2]
    before_previous = pivot.iloc[-3]
else:
    latest = pivot.iloc[-1]
    previous = pivot.iloc[-2] if len(pivot) >= 2 else latest
    before_previous = latest

overall_avg = pivot.mean()  # overall average across all snapshots

# Combine into a DataFrame for easier plotting
comparison_df = pd.DataFrame({
    'Latest': latest,
    'Previous': previous,
    'Before Previous': before_previous,
    'Overall Average': overall_avg
})

# Plot grouped bar chart for each service
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
