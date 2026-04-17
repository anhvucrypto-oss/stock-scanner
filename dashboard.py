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

        for i, row in df.iterrows():

            st.markdown(f"### {row['symbol']}")

            col1, col2, col3 = st.columns(3)
            col1.metric("Entry", row["entry"])
            col2.metric("SL", row["sl"])
            col3.metric("TP", row["tp"])

            col1, col2, col3 = st.columns(3)
            col1.metric("Score", row["score"])
            col2.metric("Winrate", f"{round(row['winrate']*100,1)}%")

            st.markdown("---")

# ===== HISTORY =====
st.subheader("📜 HISTORY (7 DAYS FIFO)")

if os.path.exists(HISTORY_FILE):

    df = pd.read_csv(HISTORY_FILE)

    if not df.empty:

        df["time"] = pd.to_datetime(df["time"])

        # mới nhất lên trên
        df = df.sort_values(by="time", ascending=False)

        st.dataframe(df, use_container_width=True)

    else:
        st.warning("No history")

else:
    st.warning("No history file")
