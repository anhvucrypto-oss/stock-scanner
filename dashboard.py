import streamlit as st
import pandas as pd
import time
import os

st.set_page_config(layout="wide")
st.title("📊 LIVE DASHBOARD (LOCAL)")

FILE = "trades_log.csv"

placeholder = st.empty()

while True:

    try:
        if not os.path.exists(FILE):
            placeholder.warning("Chưa có file trades_log.csv")
        else:
            df = pd.read_csv(FILE)

            if df.empty:
                placeholder.warning("Chưa có data")
            else:
                placeholder.dataframe(df.tail(20), width="stretch")

    except Exception as e:
        placeholder.error(f"Lỗi: {e}")

    time.sleep(2)
    st.rerun()

st.subheader("📊 T+4 Forecast")

if os.path.exists("forecast.csv"):
    df_f = pd.read_csv("forecast.csv")

# convert time
df_f["time"] = pd.to_datetime(df_f["time"], errors="coerce")

# sort mới nhất lên trên
df_f = df_f.sort_values(by="time", ascending=False)

st.dataframe(df_f, width="stretch")
else:
    st.warning("Chưa có forecast")
