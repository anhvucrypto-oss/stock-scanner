import time
from datetime import datetime
import threading
import sys
import os

# ===== IMPORT MODULE =====
import forecast_scan
import auto_trade_meta_ai

running = True


# ===== STOP HANDLER =====
def stop_listener():
    global running
    input()
    print("\n⛔ Dừng hệ thống...")
    running = False


# ===== CHECK TIME WINDOW =====
def in_trading_time():

    now = datetime.now()
    h = now.hour
    m = now.minute

    # 12:00 → 12:05
    if h == 12 and m <= 5:
        return True

    # 13:00 → 15:05
    if (h == 13) or (h == 14) or (h == 15 and m <= 5):
        return True

    return False


# ===== MAIN LOOP =====
def run():

    global running

    print("🚀 SYSTEM START")
    print("👉 Bấm Enter để dừng")

    # thread nghe stop
    threading.Thread(target=stop_listener, daemon=True).start()

    while running:

        now = datetime.now()

        # ===== STOP SAU 15:05 =====
        if now.hour == 15 and now.minute > 5:
            print("🛑 Hết giờ → dừng hệ thống")
            break

        if in_trading_time():

            print(f"\n⏰ RUN @ {now.strftime('%H:%M:%S')}")

            try:
                forecast_scan.scan()
                auto_trade_meta_ai.run()
            except Exception as e:
                print("❌ Lỗi:", e)

            time.sleep(60)  # chạy mỗi phút

        else:
            # ngoài giờ → ngủ nhẹ
            time.sleep(10)

    print("✅ SYSTEM STOPPED")


# ===== RUN =====
if __name__ == "__main__":
    run()
