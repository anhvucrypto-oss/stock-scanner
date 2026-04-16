import time
from datetime import datetime
import subprocess
import threading
import sys

import forecast_scan
import auto_trade_meta_ai


# ===== CONFIG =====
last_special_run = None


# ===== STOP =====
def stop_listener():
    input()
    print("⛔ STOP SYSTEM")
    sys.exit()


# ===== DASHBOARD =====
def start_dashboard():
    subprocess.Popen(
        ["python", "-m", "streamlit", "run", "dashboard.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    print("🌐 Dashboard started")


# ===== CHECK WEEKDAY =====
def is_weekday():
    return datetime.now().weekday() < 5  # 0=Mon


# ===== TIME LOGIC =====
def should_run():

    now = datetime.now()
    h = now.hour
    m = now.minute

    # STOP HẲN
    if h >= 15:
        return False

    # NGHỈ
    if h == 11 and m >= 30:
        return False

    if h == 12 and m >= 5:
        return False

    if h == 14 and m >= 30:
        return False

    # NGHỈ TRƯA
    if h == 12:
        return False

    return True


# ===== SPECIAL RUN =====
def is_special_time():

    now = datetime.now()
    h = now.hour
    m = now.minute

    return (h == 12 and m == 0) or (h == 15 and m == 0)


# ===== MAIN =====
def run():

    global last_special_run

    print("🚀 SYSTEM START")
    print("👉 Enter để dừng")

    threading.Thread(target=stop_listener, daemon=True).start()

    start_dashboard()

    while True:

        now = datetime.now()

        if not is_weekday():
            time.sleep(60)
            continue

        # ===== SPECIAL =====
        if is_special_time():

            key = now.strftime("%H:%M")

            if key != last_special_run:

                print(f"\n🔥 SPECIAL RUN {key}")

                forecast_scan.scan()   # luôn chạy
                auto_trade_meta_ai.run()

                last_special_run = key

            time.sleep(60)
            continue

        # ===== NORMAL RUN =====
        if should_run():

            print(f"\n⏰ RUN {now.strftime('%H:%M:%S')}")

            try:
                forecast_scan.scan()
                auto_trade_meta_ai.run()
            except Exception as e:
                print("❌ Lỗi:", e)

            time.sleep(60)

        else:
            time.sleep(10)


# ===== START =====
if __name__ == "__main__":
    run()
