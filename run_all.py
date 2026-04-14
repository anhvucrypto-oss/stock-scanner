import subprocess
import time
import os

print("🚀 START FULL SYSTEM")

# ===== CHECK FILE =====
required_files = [
    "auto_trade_meta_ai.py",
    "dashboard.py",
    "forecast_scan.py",
    "scheduler.py"
]

for f in required_files:
    if not os.path.exists(f):
        print(f"❌ Thiếu file: {f}")
        exit()

# ===== START BOT =====
print("▶️ Starting BOT...")
bot = subprocess.Popen(
    ["python", "auto_trade_final.py"],
    creationflags=subprocess.CREATE_NEW_CONSOLE
)

time.sleep(2)

# ===== START DASHBOARD =====
print("▶️ Starting DASHBOARD...")
dashboard = subprocess.Popen(
    ["python", "-m", "streamlit", "run", "dashboard.py"],
    creationflags=subprocess.CREATE_NEW_CONSOLE
)

time.sleep(2)

# ===== START SCHEDULER =====
print("▶️ Starting SCHEDULER...")
scheduler = subprocess.Popen(
    ["python", "scheduler.py"],
    creationflags=subprocess.CREATE_NEW_CONSOLE
)

# ===== MONITOR =====
print("✅ SYSTEM RUNNING (BOT + DASHBOARD + SCHEDULER)")

try:
    while True:
        time.sleep(5)

        # check bot sống không
        if bot.poll() is not None:
            print("⚠️ BOT bị tắt → restart")
            bot = subprocess.Popen(
                ["python", "auto_trade_final.py"],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )

        # check scheduler
        if scheduler.poll() is not None:
            print("⚠️ SCHEDULER bị tắt → restart")
            scheduler = subprocess.Popen(
                ["python", "scheduler.py"],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )

except KeyboardInterrupt:
    print("\n🛑 STOP SYSTEM")

    bot.terminate()
    dashboard.terminate()
    scheduler.terminate()
