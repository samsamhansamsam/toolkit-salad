# streamlit_app.py

import streamlit as st
import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt

# Page settings
st.set_page_config(page_title="Service Usage Trend", layout="wide")

st.title("📈 Weekly Service Usage Tracker")

# 1. MySQL connection
@st.cache_data
def load_data():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='wodbs7483!',
        database='shopping_analysis'
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

# 2. Pivot table
pivot = df.groupby(['snapshot_date', 'service_name'])['shop_id'].nunique().unstack(fill_value=0)

# 3. Line Chart - weekly trend
st.subheader("Weekly Trend by Service")
fig, ax = plt.subplots(figsize=(10, 6))
for service in pivot.columns:
    ax.plot(pivot.index, pivot[service], marker='o', label=service)

ax.set_title("Weekly Active Shops per Service")
ax.set_xlabel("Date")
ax.set_ylabel("Number of Shops")
ax.legend(title="Service", bbox_to_anchor=(1.05, 1), loc='upper left')
ax.grid(True)
st.pyplot(fig)

# 4. Bar Chart - most recent week
st.subheader("Latest Week Snapshot")
recent = pivot.iloc[-1].sort_values()
fig2, ax2 = plt.subplots(figsize=(8, 5))
recent.plot(kind='barh', ax=ax2)
ax2.set_title("Latest Week - Active Shops by Service")
ax2.set_xlabel("Number of Shops")
st.pyplot(fig2)
