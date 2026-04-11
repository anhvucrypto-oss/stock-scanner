import streamlit as st
import pandas as pd
import requests
from io import StringIO
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("📊 DASHBOARD DEBUG")

url = "https://raw.githubusercontent.com/anhvucrypto-oss/stock-scanner/main/trades_log.csv"

# ===== DEBUG STEP 1 =====
st.write("🔗 URL:", url)

try:
    res = requests.get(url)
    
    st.write("📡 Status code:", res.status_code)

    if res.status_code != 200:
        st.error("❌ GitHub không trả dữ liệu")
        st.stop()

    st.write("📄 Raw content:")
    st.code(res.text)

    # ===== LOAD CSV =====
    csv_data = StringIO(res.text)
    df = pd.read_csv(csv_data)

except Exception as e:
    st.error(f"❌ Lỗi request: {e}")
    st.stop()

# ===== DEBUG STEP 2 =====
st.write("📊 DataFrame:")
st.dataframe(df)

# ===== CLEAN =====
df["result"] = pd.to_numeric(df["result"], errors="coerce")
df = df.dropna()

if len(df) == 0:
    st.warning("⚠️ Không có dữ liệu hợp lệ")
    st.stop()

# ===== EQUITY =====
df["equity"] = df["result"].cumsum()

# ===== CHART =====
st.subheader("Equity")

fig, ax = plt.subplots()
ax.plot(df["equity"])
ax.grid()

st.pyplot(fig)
