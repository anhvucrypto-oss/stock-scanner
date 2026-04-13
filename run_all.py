import subprocess

print("🚀 START BOT + DASHBOARD")

# chạy bot
subprocess.Popen(["python", "auto_trade_meta_ai.py"])

# chạy dashboard
subprocess.Popen(["streamlit", "run", "dashboard.py"])

input("Press Enter to stop...")
