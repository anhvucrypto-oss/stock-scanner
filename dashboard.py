import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")

st.title("📊 TRADING DASHBOARD")

FILE = "forecast.csv"
HISTORY_FILE = "forecast_history.csv"


# ===== CURRENT =====
st.subheader("🔥 CURRENT PICKS")

if os.path.exists(FILE):
    df = pd.read_csv(FILE)

    if not df.empty:
        df["winrate"] = (df["winrate"]*100).round(1).astype(str) + "%"
        st.dataframe(df, use_container_width=True)


# ===== COLOR =====
def color_status(val):
    if val == "WIN":
        return "background-color: #d4edda"
    if val == "LOSS":
        return "background-color: #f8d7da"
    if val == "HOLD":
        return "background-color: #fff3cd"
    return ""


# ===== HISTORY =====
st.subheader("📜 HISTORY (7 DAYS)")

if os.path.exists(HISTORY_FILE):

    df = pd.read_csv(HISTORY_FILE)

    if not df.empty:

        df["time"] = pd.to_datetime(df["time"])
        df = df.sort_values(by="time", ascending=False)

        df["winrate"] = (df["winrate"]*100).round(1).astype(str) + "%"

        st.dataframe(
            df.style.applymap(color_status, subset=["status"]),
            use_container_width=True
        )
