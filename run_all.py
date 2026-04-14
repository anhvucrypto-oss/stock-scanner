import subprocess
import time
from datetime import datetime
import threading

print("🚀 START FULL SYSTEM")
print("👉 Bấm Ctrl + C hoặc Enter để dừng toàn bộ tiến trình\n")

# ===== START BOT =====
bot = subprocess.Popen(["python", "auto_trade_meta_ai.py"])

# ===== START DASHBOARD =====
dashboard = subprocess.Popen(["python", "-m", "streamlit", "run", "dashboard.py"])

# ===== STOP FLAG =====
stop_flag = False

# ===== ENTER LISTENER =====
def wait_for_enter():
    global stop_flag
    input()
    stop_flag = True

threading.Thread(target=wait_for_enter, daemon=True).start()

# ===== TIME CONTROL =====
last_run = None

def is_weekday():
    return datetime.now().weekday() < 5

def is_target_time():
    now = datetime.now().strftime("%H:%M")
    return now in ["12:00", "15:00"]

# ===== MAIN LOOP =====
try:
    while not stop_flag:

        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        if is_weekday() and is_target_time():

            if last_run != now:
                print(f"⏰ RUN FORECAST {now}")
                subprocess.Popen(["python", "forecast_scan.py"])
                last_run = now

        time.sleep(30)

except KeyboardInterrupt:
    pass

# ===== STOP ALL =====
print("\n🛑 STOPPING SYSTEM...")

bot.terminate()
dashboard.terminate()

print("✅ Đã dừng toàn bộ.")
