import streamlit as st
import pandas as pd
import requests
from io import StringIO

st.title("Dashboard")

url = "https://raw.githubusercontent.com/anhvucrypto-oss/stock-scanner/main/trades_log.csv"

try:
    res = requests.get(url, timeout=10)

    if res.status_code != 200:
        st.error(f"Lỗi GitHub: {res.status_code}")
        st.stop()

    df = pd.read_csv(StringIO(res.text))

except Exception as e:
    st.error(f"Lỗi load: {e}")
    st.stop()

if df.empty:
    st.warning("Chưa có data")
    st.stop()

st.write(df.tail(10))
