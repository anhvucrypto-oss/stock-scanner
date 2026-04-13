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
                placeholder.dataframe(df.tail(20), use_container_width=True)

    except Exception as e:
        placeholder.error(f"Lỗi: {e}")

    time.sleep(2)
    st.rerun()
