import streamlit as st
import pandas as pd
import os
import time

st.set_page_config(layout="wide")

st.title("📊 TRADING DASHBOARD")

time.sleep(5)
st.rerun()

st.subheader("📊 TOP 3 T+4 PICKS")

if os.path.exists("forecast.csv"):

    try:
        df = pd.read_csv("forecast.csv")

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

                capital = int(100_000_000 * [0.5,0.3,0.2][i])
                col3.metric("Vốn", f"{capital:,}")

                st.markdown("---")

        else:
            st.warning("Forecast rỗng")

    except Exception as e:
        st.error(f"Lỗi đọc forecast.csv: {e}")

else:
    st.warning("Chưa có forecast.csv")
