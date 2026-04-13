import streamlit as st
import pandas as pd
import requests
from io import StringIO

st.title("Dashboard")

url = "https://raw.githubusercontent.com/anhvucrypto-oss/stock-scanner/main/trades_log.csv"

res = requests.get(url, timeout=10)

if res.status_code != 200:
    st.error("Không load được data")
    st.stop()

df = pd.read_csv(StringIO(res.text))

st.dataframe(df.tail(20))

st.caption("Auto refresh 5s")

import time
time.sleep(5)
st.rerun()
