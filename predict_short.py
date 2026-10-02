import joblib
import pandas as pd

model = joblib.load("short_model.pkl")

CSV_PATH = "ohlc_last.csv"

FEATURE_COLUMNS = [
    "open",
    "high",
    "low",
    "close",
    "entry",
    "sl",
    "tp",
    "DEMA_20",
    "DEMA_50",
    "DEMA_100",
    "fractal"
]

FRACTAL_MAP = {
    "none": 0,
    "up": 1,
    "down": -1
}

def predict_short():

    try:

        ai_df = pd.read_csv(CSV_PATH)

        ai_df = ai_df.tail(50)

        ai_df = ai_df[FEATURE_COLUMNS]

        ai_df = ai_df.replace(
            ["none", "None"],
            0
        ).infer_objects(copy=False)

        ai_df["fractal"] = ai_df["fractal"].map(FRACTAL_MAP)

        ai_df = ai_df.apply(
            pd.to_numeric,
            errors="coerce"
        )

        ai_df = ai_df.fillna(0)

        features = ai_df.to_numpy().flatten()

        ai_df.to_csv("ai_debug_short.csv", index=False)

        print("=" * 50)
        print("AI DF SHAPE:", ai_df.shape)
        print("AI FEATURES:", len(features))
        print("AI COLUMNS:")
        print(ai_df.columns.tolist())
        print("=" * 50)

        prediction = model.predict([features])[0]

        return "tp" if prediction == 1 else "sl"

    except Exception as e:

        print(f"SHORT AI ERROR: {e}")

        return "error"