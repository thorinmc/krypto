import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

BASE_PATH = "practice/long"

X = []
y = []

def load_data(folder_name, label):

    folder_path = os.path.join(BASE_PATH, folder_name)

    for file in os.listdir(folder_path):

        if not file.endswith(".csv"):
            continue

        file_path = os.path.join(folder_path, file)

        df = pd.read_csv(file_path)

        df = df.replace("none", 0)
        df = df.replace("None", 0)

        df = df.apply(pd.to_numeric, errors="coerce")

        df = df.fillna(0)

        # usuwamy timestamp jeśli istnieje
        if "timestamp" in df.columns:
            df = df.drop(columns=["timestamp"])

        # zamiana całego csv na 1 wektor
        features = df.to_numpy().flatten()

        print(file, len(features))

        X.append(features)
        y.append(label)

# TP = 1
load_data("tp", 1)

# SL = 0
load_data("sl", 0)

print(f"Próbek: {len(X)}")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    random_state=42
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print(f"Accuracy: {accuracy:.2f}")

joblib.dump(model, "long_model.pkl")

print("LONG MODEL SAVED")