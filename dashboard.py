import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("📊 TRADING SYSTEM DASHBOARD")

FILE = "trades_log.csv"

# ===== LOAD DATA =====
try:
    df = pd.read_csv(FILE)
except:
    st.error("❌ Không tìm thấy trades_log.csv")
    st.stop()

df = df[df["result"] != ""]

if len(df) == 0:
    st.warning("Chưa có dữ liệu")
    st.stop()

df["result"] = df["result"].astype(float)

# ===== EQUITY =====
equity = [0]
for r in df["result"]:
    equity.append(equity[-1] + r)

df["equity"] = equity[1:]

# ===== STATS =====
total = len(df)
win = len(df[df["result"] > 0])
winrate = round(win / total * 100, 2)
pnl = df["result"].sum()

df["peak"] = df["equity"].cummax()
df["drawdown"] = df["equity"] - df["peak"]
max_dd = df["drawdown"].min()

# ===== UI =====
col1, col2, col3, col4 = st.columns(4)

col1.metric("Trades", total)
col2.metric("Winrate", f"{winrate}%")
col3.metric("PnL (R)", round(pnl,2))
col4.metric("Max DD", round(max_dd,2))

# ===== EQUITY CHART =====
st.subheader("📈 Equity Curve")

fig, ax = plt.subplots()
ax.plot(df["equity"])
ax.set_title("Equity Growth")
ax.grid()

st.pyplot(fig)

# ===== TABLE =====
st.subheader("📋 Trades Log")
st.dataframe(df.tail(20))