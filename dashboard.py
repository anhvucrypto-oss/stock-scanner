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

    try:
        df = pd.read_csv("trades_log.csv")

        if not df.empty:

            if "time" in df.columns:
                df["time"] = pd.to_datetime(df["time"], errors="coerce")
                df = df.sort_values(by="time", ascending=False)

            st.dataframe(df, width="stretch")

        else:
            st.warning("Trades log rỗng")

    except Exception as e:
        st.error(f"Lỗi đọc trades_log.csv: {e}")

else:
    st.warning("Chưa có trades_log.csv")


# ==============================
# 📊 FORECAST
# ==============================
st.subheader("📊 Forecast (TOP PICK)")

if os.path.exists("forecast.csv"):

    try:
        df_f = pd.read_csv("forecast.csv")

        if not df_f.empty:

            # đảm bảo có time
            if "time" in df_f.columns:
                df_f["time"] = pd.to_datetime(df_f["time"], errors="coerce")
                df_f = df_f.sort_values(by="time", ascending=False)

            # hiển thị top 1
            row = df_f.iloc[0]

            st.markdown("### 🔥 Best Pick")

            col1, col2, col3 = st.columns(3)

            col1.metric("Symbol", row.get("symbol", "-"))
            col2.metric("Entry", row.get("entry", "-"))
            col3.metric("Score", row.get("score", "-"))

            col1, col2, col3 = st.columns(3)

            col1.metric("SL", row.get("sl", "-"))
            col2.metric("TP", row.get("tp", "-"))
            col3.metric("Winrate", f"{round(row.get('winrate',0)*100,1)}%")

            if "max_dd" in row:
                st.metric("Max Drawdown", f"{round(row['max_dd']*100,1)}%")

            if "equity" in row:
                st.metric("Equity", f"{row['equity']}x")

        else:
            st.warning("Forecast rỗng")

    except Exception as e:
        st.error(f"Lỗi đọc forecast.csv: {e}")

else:
    st.warning("Chưa có forecast.csv")
