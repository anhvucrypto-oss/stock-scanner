import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")

st.title("📊 TRADING DASHBOARD")

FILE = "forecast.csv"
HISTORY_FILE = "forecast_history.csv"

# ===== CURRENT PICKS =====
st.subheader("🔥 CURRENT PICKS")

if os.path.exists(FILE):

    df = pd.read_csv(FILE)

    if not df.empty:

        # format đẹp hơn
        df_display = df.copy()

        df_display["winrate"] = (df_display["winrate"] * 100).round(1).astype(str) + "%"
        df_display["score"] = df_display["score"].round(3)

        st.dataframe(df_display, use_container_width=True)

    else:
        st.warning("No current data")

else:
    st.warning("forecast.csv not found")


# ===== HISTORY =====
st.subheader("📜 HISTORY (7 DAYS)")

if os.path.exists(HISTORY_FILE):

    df = pd.read_csv(HISTORY_FILE)

    if not df.empty:

        df["time"] = pd.to_datetime(df["time"])
        df = df.sort_values(by="time", ascending=False)

        # format
        df["winrate"] = (df["winrate"] * 100).round(1).astype(str) + "%"
        df["score"] = df["score"].round(3)

        st.dataframe(df, use_container_width=True)

    else:
        st.warning("No history data")

else:
    st.warning("No history file")
