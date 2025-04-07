import streamlit as st
import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import PercentFormatter
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

# Calculate percentage for each snapshot (row normalized to 100%)
pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

# 자동 정렬: 전체 주차에 걸친 각 서비스의 평균 비중 기준 내림차순 정렬
avg_proportions = pivot_pct.mean(axis=0)
sorted_services = avg_proportions.sort_values(ascending=False).index.tolist()
pivot_pct = pivot_pct[sorted_services]

# --- Stacked Bar Chart: Weekly Service Usage Distribution (100% Stacked) ---
st.subheader("Weekly Service Usage Distribution (100% Stacked)")
fig_stacked, ax_stacked = plt.subplots(figsize=(10, 6))
bottom = np.zeros(len(pivot_pct))
for service in pivot_pct.columns:
    ax_stacked.bar(pivot_pct.index, pivot_pct[service], bottom=bottom, label=service)
    bottom += pivot_pct[service].values

ax_stacked.set_title("Weekly Active Shops Distribution by Service (Normalized to 100%)")
ax_stacked.set_xlabel("Snapshot Date")
ax_stacked.set_ylabel("Percentage (%)")
ax_stacked.yaxis.set_major_formatter(plt.matplotlib.ticker.PercentFormatter(decimals=0))

min_date = pivot_pct.index.min()
max_date = pivot_pct.index.max()
ax_stacked.set_xlim([min_date, max_date])
ax_stacked.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
ax_stacked.xaxis.set_major_locator(mdates.DayLocator(interval=7))
plt.xticks(rotation=45)

ax_stacked.legend(title="Service", bbox_to_anchor=(1.05, 1), loc='upper left')
st.pyplot(fig_stacked)

# --- 2. (기존 Snapshot Comparison Bar Chart: 그대로 유지) ---
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
