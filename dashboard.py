import streamlit as st
import pandas as pd
import os
import time

st.set_page_config(layout="wide")

st.title("📊 TRADING DASHBOARD")

# ===== AUTO REFRESH =====
st.caption("Auto refresh mỗi 5 giây")
time.sleep(5)
st.rerun()

# ==============================
# 📈 TRADES LOG
# ==============================
st.subheader("📈 Trades Log")

if os.path.exists("trades_log.csv"):

    df = pd.read_csv("trades_log.csv")

    if not df.empty:

        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"], errors="coerce")
            df = df.sort_values(by="time", ascending=False)

        st.dataframe(df, width="stretch")

    else:
        st.warning("Trades log rỗng")

else:
    st.warning("Chưa có trades_log.csv")


# ==============================
# 📊 FORECAST T+4
# ==============================
st.subheader("📊 T+4 Forecast")

if os.path.exists("forecast.csv"):

    df_f = pd.read_csv("forecast.csv")

    if not df_f.empty:

        if "time" in df_f.columns:
            df_f["time"] = pd.to_datetime(df_f["time"], errors="coerce")
            df_f = df_f.sort_values(by="time", ascending=False)

        # chỉ lấy lần scan mới nhất
        latest_time = df_f["time"].max()
        df_f = df_f[df_f["time"] == latest_time]

        st.dataframe(df_f, width="stretch")

    else:
        st.warning("Forecast rỗng")

else:
    st.warning("Chưa có forecast.csv")
