import subprocess

print("🚀 START BOT + DASHBOARD")

# chạy bot
subprocess.Popen(["python", "auto_trade_meta_ai.py"])

# chạy dashboard (QUAN TRỌNG: dùng python -m)
subprocess.Popen(["python", "-m", "streamlit", "run", "dashboard.py"])

input("Press Enter to stop...")
