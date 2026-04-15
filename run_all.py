import time
from datetime import datetime
import threading
import os
import subprocess

import forecast_scan
import auto_trade_meta_ai

running = True


# ===== STOP =====
def stop_listener():
    global running
    input()
    print("\n⛔ Dừng hệ thống...")
    running = False


# ===== MỞ DASHBOARD =====
def start_dashboard():
    try:
        subprocess.Popen(
            ["python", "-m", "streamlit", "run", "dashboard.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("🌐 Dashboard started")
    except Exception as e:
        print("❌ Dashboard lỗi:", e)


# ===== TIME =====
def in_time():

    now = datetime.now()
    h = now.hour
    m = now.minute

    if h == 12 and m <= 5:
        return True

    if (h == 13) or (h == 14) or (h == 15 and m <= 5):
        return True

    return False


# ===== MAIN =====
def run():

    global running

    print("🚀 SYSTEM START")
    print("👉 Bấm Enter để dừng")

    threading.Thread(target=stop_listener, daemon=True).start()

    # ===== MỞ DASHBOARD NGAY TỪ ĐẦU =====
    start_dashboard()

    while running:

        now = datetime.now()

        if now.hour == 15 and now.minute > 5:
            print("🛑 Hết giờ → dừng")
            break

        if in_time():

            print(f"\n⏰ RUN @ {now.strftime('%H:%M:%S')}")

            try:
                forecast_scan.scan()
                auto_trade_meta_ai.run()
            except Exception as e:
                print("❌ Lỗi:", e)

            time.sleep(60)

        else:
            time.sleep(10)

    print("✅ STOPPED")


if __name__ == "__main__":
    run()
