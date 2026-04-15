import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(layout="wide")

st.title("📊 TRADING DASHBOARD")

# ===== REFRESH BUTTON (ổn định hơn sleep + rerun) =====
if st.button("🔄 Refresh"):
    st.rerun()

st.caption(f"Cập nhật lúc: {datetime.now().strftime('%H:%M:%S')}")

# ==============================
# 📊 FORECAST
# ==============================
st.subheader("📊 TOP 3 T+4 PICKS")

FILE = "forecast.csv"

# DEBUG
st.write("📂 File tồn tại:", os.path.exists(FILE))

if os.path.exists(FILE):

    try:
        df = pd.read_csv(FILE)

        st.write("📊 Raw data:")
        st.dataframe(df)   # 👉 DEBUG xem có data không

        if not df.empty:

            df = df.reset_index(drop=True)

            weights = [0.5, 0.3, 0.2]

            for i in range(min(3, len(df))):

                row = df.iloc[i]

                st.markdown(f"### 🔥 {row['symbol']}")

                col1, col2, col3 = st.columns(3)
                col1.metric("Entry", row["entry"])
                col2.metric("SL", row["sl"])
                col3.metric("TP", row["tp"])

                col1, col2, col3 = st.columns(3)
                col1.metric("Score", row["score"])
                col2.metric("Winrate", f"{round(row['winrate']*100,1)}%")

                capital = int(100_000_000 * weights[i])
                col3.metric("Vốn", f"{capital:,}")

                st.markdown("---")

        else:
            st.warning("⚠️ forecast.csv rỗng")

    except Exception as e:
        st.error(f"❌ Lỗi đọc file: {e}")

else:
    st.warning("❌ Không tìm thấy forecast.csv")
