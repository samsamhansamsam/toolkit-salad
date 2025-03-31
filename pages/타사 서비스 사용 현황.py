# streamlit_app.py

import streamlit as st
import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt

# --- Page Setup ---
st.set_page_config(page_title="Service Usage Dashboard", layout="wide")
st.title("📈 Weekly Service Usage Dashboard")

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

# --- Pivot Table: Weekly service usage ---
pivot = df.groupby(['snapshot_date', 'service_name'])['shop_id'].nunique().unstack(fill_value=0)

# --- Line Chart: Trend by service ---
st.subheader("📉 Weekly Trend by Service")
fig, ax = plt.subplots(figsize=(10, 6))
for service in pivot.columns:
    ax.plot(pivot.index, pivot[service], marker='o', label=service)

ax.set_title("Weekly Active Shops per Service")
ax.set_xlabel("Snapshot Date")
ax.set_ylabel("Number of Shops")
ax.legend(title="Service", bbox_to_anchor=(1.05, 1), loc='upper left')
ax.grid(True)
st.pyplot(fig)

# --- Bar Chart: Most recent week ---
st.subheader("📊 Latest Week Snapshot")
recent = pivot.iloc[-1].sort_values()
fig2, ax2 = plt.subplots(figsize=(8, 5))
recent.plot(kind='barh', ax=ax2)
ax2.set_title("Latest Week - Active Shops by Service")
ax2.set_xlabel("Number of Shops")
st.pyplot(fig2)
