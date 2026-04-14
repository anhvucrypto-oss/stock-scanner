import subprocess
import time
from datetime import datetime
import os

print("🚀 START FULL SYSTEM")

# ===== START BOT =====
bot = subprocess.Popen(
    ["python", "auto_trade_meta_ai.py"],
    creationflags=subprocess.CREATE_NEW_CONSOLE
)

time.sleep(2)

# ===== START DASHBOARD =====
dashboard = subprocess.Popen(
    ["python", "-m", "streamlit", "run", "dashboard.py"],
    creationflags=subprocess.CREATE_NEW_CONSOLE
)

print("✅ BOT + DASHBOARD RUNNING")

# ===== TIME CONTROL =====
last_run = None

def is_weekday():
    return datetime.now().weekday() < 5  # T2–T6

def is_target_time():
    now = datetime.now().strftime("%H:%M")
    return now in ["12:00", "15:00"]

# ===== LOOP =====
try:
    while True:

        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        if is_weekday() and is_target_time():

            if last_run != now:
                print(f"⏰ RUN FORECAST {now}")

                subprocess.Popen(
                    ["python", "forecast_scan.py"],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )

                last_run = now

        time.sleep(30)

except KeyboardInterrupt:
    print("\n🛑 STOP SYSTEM")
    bot.terminate()
    dashboard.terminate()
