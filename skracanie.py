import os
import pandas as pd

FOLDER = "practice/short/tp"

FRACTAL_MAP = {
    "none": 0,
    "up": 1,
    "down": -1
}

for file in os.listdir(FOLDER):

    if not file.endswith(".csv"):
        continue

    path = os.path.join(FOLDER, file)

    df = pd.read_csv(path)

    # usuń kolumny jeśli istnieją
    df = df.drop(
        columns=["side", "symbol"],
        errors="ignore"
    )

    # fractal -> liczby
    df["fractal"] = df["fractal"].map(FRACTAL_MAP)

    # zapis
    df.to_csv(path, index=False)

    print(f"FIXED: {file}")