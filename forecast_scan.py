HISTORY_FILE = "forecast_history.csv"

def save_history(df):

    df = df.copy()
    df["time"] = datetime.now()

    if os.path.exists(HISTORY_FILE):
        old = pd.read_csv(HISTORY_FILE)
        df = pd.concat([old, df], ignore_index=True)

    # ===== FIFO 7 NGÀY =====
    df["time"] = pd.to_datetime(df["time"])
    cutoff = datetime.now() - pd.Timedelta(days=7)

    df = df[df["time"] >= cutoff]

    df.to_csv(HISTORY_FILE, index=False)
