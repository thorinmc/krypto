import pandas as pd
import plotly.graph_objects as go

# Wczytanie pliku
df = pd.read_csv("ohlc_tv.csv")

# Konwersja timestamp (obsłuży strefę czasową)
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Tworzenie wykresu świecowego
fig = go.Figure(data=[go.Candlestick(
    x=df["timestamp"],
    open=df["open"],
    high=df["high"],
    low=df["low"],
    close=df["close"]
)])

# Ustawienia wykresu
fig.update_layout(
    title="Wykres świecowy z pliku ohlc_tv.csv",
    xaxis_title="Czas",
    yaxis_title="Cena",
    xaxis_rangeslider_visible=False
)

fig.show()