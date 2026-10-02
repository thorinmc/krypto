import os
import pandas as pd
import numpy as np
import time

WARSAW = "Europe/Warsaw"

class TradeSampleCollector:
    def __init__(self, csv_path="ohlc_last.csv"):
        self.csv_path = csv_path
        self.last_state = "IDLE"
        self.open_idx = None
        self.open_side = None

    def load_df(self):
        df = pd.read_csv(self.csv_path)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.set_index("timestamp").tz_convert(WARSAW)
        return df

    def step(self):
        df = self.load_df()
        last = df.iloc[-1]
        side = last["side"]

        if self.last_state == "IDLE" and side != "none":
            self.last_state = "OPEN"
            self.open_idx = df.index[-1]
            self.open_side = side
            return

        if self.last_state == "OPEN" and side == "none":
            self.handle_close(df)
            self.last_state = "IDLE"
            self.open_idx = None
            self.open_side = None

    def handle_close(self, df):
        start_pos = df.index.get_loc(self.open_idx)
        start = max(0, start_pos - 50)
        sample = df.iloc[start:]

        label = self.detect_sl_tp(sample)
        features = self.compute_features(sample)

        folder = f"sl_tp/{label}"
        os.makedirs(folder, exist_ok=True)

        ts = self.open_idx.strftime("%Y%m%d_%H%M")
        sample.to_csv(f"{folder}/sample_{ts}.csv")
        features.to_csv(f"{folder}/features_{ts}.csv")

    # ================= FEATURES =================

    def detect_sl_tp(self, df):
        side = self.open_side
        entry = df.iloc[50]["entry"]
        sl = df.iloc[50]["sl"]
        tp = df.iloc[50]["tp"]

        for _, r in df.iloc[50:].iterrows():
            if side == "long":
                if r["low"] <= sl:
                    return "sl"
                if r["high"] >= tp:
                    return "tp"
            else:
                if r["high"] >= sl:
                    return "sl"
                if r["low"] <= tp:
                    return "tp"
        return "unknown"

    def compute_features(self, df):
        feats = {}

        # zakres ceny
        feats["price_range"] = df["high"].max() - df["low"].min()

        # DEMA distances
        feats["dema_20_100"] = abs(df["DEMA_20"] - df["DEMA_100"]).mean()
        feats["dema_20_50"] = abs(df["DEMA_20"] - df["DEMA_50"]).mean()

        # ruch kierunkowy (segmentowany)
        diffs = df["close"].diff().fillna(0)
        segments = []
        cur = 0

        for d in diffs:
            if np.sign(d) == np.sign(cur) or cur == 0:
                cur += d
            else:
                segments.append(cur)
                cur = d
        segments.append(cur)

        segments = sorted(segments, key=lambda x: abs(x), reverse=True)[:5]
        feats["trend_segments"] = segments

        return pd.DataFrame([feats])
    
collector = TradeSampleCollector()

while True:
    collector.step()
    time.sleep(60)
