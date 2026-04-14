import schedule
import time
import subprocess

def job():
    subprocess.run(["python", "forecast_scan.py"])

# 12h & 15h (T2–T6)
schedule.every().monday.at("12:00").do(job)
schedule.every().monday.at("15:00").do(job)

schedule.every().tuesday.at("12:00").do(job)
schedule.every().tuesday.at("15:00").do(job)

schedule.every().wednesday.at("12:00").do(job)
schedule.every().wednesday.at("15:00").do(job)

schedule.every().thursday.at("12:00").do(job)
schedule.every().thursday.at("15:00").do(job)

schedule.every().friday.at("12:00").do(job)
schedule.every().friday.at("15:00").do(job)

print("⏰ Scheduler running...")

while True:
    schedule.run_pending()
    time.sleep(30)