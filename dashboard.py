import streamlit as st
import pandas as pd
import requests
from io import StringIO
import time
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("📊 TRADING DASHBOARD PRO")

url = "https://raw.githubusercontent.com/anhvucrypto-oss/stock-scanner/main/trades_log.csv"

refresh_interval = 10
placeholder = st.empty()

while True:

    try:
        res = requests.get(url, timeout=10)

        if res.status_code != 200:
            placeholder.error(f"Lỗi GitHub: {res.status_code}")
            time.sleep(refresh_interval)
            st.rerun()

        df = pd.read_csv(StringIO(res.text))

        if df.empty:
            placeholder.warning("Chưa có data")
            time.sleep(refresh_interval)
            st.rerun()

        df["result"] = pd.to_numeric(df["result"], errors="coerce")
        df = df.dropna(subset=["result"])

        if len(df) == 0:
            placeholder.warning("Chưa có trade hoàn thành")
            time.sleep(refresh_interval)
            st.rerun()

        # ===== METRICS =====
        total = len(df)
        win = len(df[df["result"] > 0])
        winrate = round(win / total * 100, 2)
        pnl = df["result"].sum()

        df["equity"] = df["result"].cumsum()
        df["peak"] = df["equity"].cummax()
        df["drawdown"] = df["equity"] - df["peak"]

        max_dd = round(df["drawdown"].min(), 2)

        # ===== UI =====
        with placeholder.container():

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Trades", total)
            col2.metric("Winrate", f"{winrate}%")
            col3.metric("PnL (R)", round(pnl, 2))
            col4.metric("Max DD", max_dd)

            # ===== EQUITY =====
            st.subheader("📈 Equity Curve")
            fig1, ax1 = plt.subplots()
            ax1.plot(df["equity"])
            ax1.grid()
            st.pyplot(fig1)

            # ===== DRAWDOWN =====
            st.subheader("📉 Drawdown")
            fig2, ax2 = plt.subplots()
            ax2.plot(df["drawdown"])
            ax2.grid()
            st.pyplot(fig2)

            # ===== TABLE =====
            st.subheader("📋 Trades")
            st.dataframe(df.tail(20))

    except Exception as e:
        placeholder.error(f"Lỗi: {e}")

    time.sleep(refresh_interval)
    st.rerun()
