import streamlit as st
import pandas as pd
import requests
from io import StringIO
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("📊 TRADING DASHBOARD (REALTIME)")

# ===== LOAD DATA =====
url = "https://raw.githubusercontent.com/anhvucrypto-oss/stock-scanner/main/trades_log.csv"

st.write("🔗 Loading data...")

try:
    res = requests.get(url)

    if res.status_code != 200:
        st.error(f"❌ Không load được GitHub: {res.status_code}")
        st.stop()

    csv_data = StringIO(res.text)
    df = pd.read_csv(csv_data)

except Exception as e:
    st.error(f"❌ Lỗi load: {e}")
    st.stop()

# ===== CHECK DATA =====
if df.empty:
    st.warning("⚠️ File rỗng")
    st.stop()

# ===== CLEAN =====
df["result"] = pd.to_numeric(df["result"], errors="coerce")

df_all = df.copy()
df = df.dropna(subset=["result"])

if len(df) == 0:
    st.warning("⚠️ Chưa có lệnh hoàn thành")
    st.dataframe(df_all.tail(10))
    st.stop()

# ===== EQUITY =====
df["equity"] = df["result"].cumsum()

# ===== NAV =====
INITIAL_CAPITAL = 100000000
df["nav"] = INITIAL_CAPITAL * (1 + df["equity"] * 0.01)

# ===== DRAWDOWN =====
df["peak"] = df["equity"].cummax()
df["drawdown"] = df["equity"] - df["peak"]

# ===== STATS =====
total = len(df)
win = len(df[df["result"] > 0])
winrate = round(win / total * 100, 2)
pnl = df["result"].sum()
max_dd = df["drawdown"].min()

# ===== UI =====
col1, col2, col3, col4 = st.columns(4)

col1.metric("Trades", total)
col2.metric("Winrate", f"{winrate}%")
col3.metric("PnL (R)", round(pnl,2))
col4.metric("Max DD", round(max_dd,2))

# ===== EQUITY =====
st.subheader("📈 Equity Curve")
fig1, ax1 = plt.subplots()
ax1.plot(df["equity"])
ax1.grid()
st.pyplot(fig1)

# ===== NAV =====
st.subheader("💰 NAV")
fig2, ax2 = plt.subplots()
ax2.plot(df["nav"])
ax2.grid()
st.pyplot(fig2)

# ===== DD =====
st.subheader("📉 Drawdown")
fig3, ax3 = plt.subplots()
ax3.plot(df["drawdown"])
ax3.grid()
st.pyplot(fig3)

# ===== TABLE =====
st.subheader("📋 Trades")
st.dataframe(df.tail(20))
