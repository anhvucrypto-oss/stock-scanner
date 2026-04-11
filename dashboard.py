import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("📊 TRADING SYSTEM DASHBOARD (REALTIME)")

# ===== LOAD DATA FROM GITHUB =====
url = "https://raw.githubusercontent.com/YOUR_USERNAME/stock-scanner/main/trades_log.csv"

try:
    df = pd.read_csv(url)
except:
    st.error("❌ Không load được dữ liệu từ GitHub")
    st.stop()

# ===== CHECK DATA =====
df = df[df["result"].notna()]

if len(df) == 0:
    st.warning("⚠️ Chưa có dữ liệu trade")
    st.stop()

# ===== CONVERT =====
df["result"] = pd.to_numeric(df["result"], errors="coerce")
df = df.dropna()

# ===== EQUITY =====
equity = [0]
for r in df["result"]:
    equity.append(equity[-1] + r)

df["equity"] = equity[1:]

# ===== NAV =====
INITIAL_CAPITAL = 100000000
df["nav"] = INITIAL_CAPITAL * (1 + df["equity"] * 0.01)

# ===== DRAWDOWN =====
df["peak"] = df["equity"].cummax()
df["drawdown"] = df["equity"] - df["peak"]
max_dd = df["drawdown"].min()

# ===== STATS =====
total = len(df)
win = len(df[df["result"] > 0])
winrate = round(win / total * 100, 2)
pnl = df["result"].sum()

# ===== UI =====
col1, col2, col3, col4 = st.columns(4)

col1.metric("Trades", total)
col2.metric("Winrate", f"{winrate}%")
col3.metric("PnL (R)", round(pnl, 2))
col4.metric("Max DD", round(max_dd, 2))

# ===== EQUITY CHART =====
st.subheader("📈 Equity Curve")

fig1, ax1 = plt.subplots()
ax1.plot(df["equity"])
ax1.set_title("Equity Growth")
ax1.grid()

st.pyplot(fig1)

# ===== NAV CHART =====
st.subheader("💰 NAV (Account Growth)")

fig2, ax2 = plt.subplots()
ax2.plot(df["nav"])
ax2.set_title("NAV")
ax2.grid()

st.pyplot(fig2)

# ===== DRAWDOWN CHART =====
st.subheader("📉 Drawdown")

fig3, ax3 = plt.subplots()
ax3.plot(df["drawdown"])
ax3.set_title("Drawdown")
ax3.grid()

st.pyplot(fig3)

# ===== TABLE =====
st.subheader("📋 Trades Log")

st.dataframe(df.tail(20))

# ===== AUTO REFRESH =====
st.caption("🔄 Auto refresh mỗi 60s")
st.experimental_rerun()
