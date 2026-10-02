import pandas as pd
import plotly.graph_objects as go
import sys
import os
import numpy as np


def generate_chart(file_path):
    if not os.path.exists(file_path):
        print(f"❌ Plik nie istnieje: {file_path}")
        return

    df = pd.read_csv(file_path)

    # =========================
    # 🔥 CLEANING (KLUCZOWE)
    # =========================
    df = df.replace("none", np.nan)

    # =========================
    # 🔹 DEMA rename
    # =========================
    df = df.rename(columns={
        'DEMA_20': 'DEMA_short',
        'DEMA_50': 'DEMA_medium',
        'DEMA_100': 'DEMA_long'
    })

    # =========================
    # 🔹 TIME INDEX
    # =========================
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)

    # =========================
    # 🔹 FRACTALS (twoje dane: up/down)
    # =========================
    df['upFractal'] = df['fractal'] == 'up'
    df['downFractal'] = df['fractal'] == 'down'

    offset = 0.0005

    # =========================
    # 🔹 FIGURE
    # =========================
    fig = go.Figure()

    # Candles
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Candles'
    ))

    # DEMA
    for col, name, color in [
        ("DEMA_short", "DEMA 20", "green"),
        ("DEMA_medium", "DEMA 50", "deepskyblue"),
        ("DEMA_long", "DEMA 100", "#C9A800"),
    ]:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df[col],
                mode='lines',
                name=name,
                line=dict(color=color)
            ))

    # Fractals UP
    if "upFractal" in df.columns:
        fig.add_trace(go.Scatter(
            x=df[df['upFractal']].index,
            y=df[df['upFractal']]['low'] * (1 - offset),
            mode='markers',
            name='Fractal UP',
            marker=dict(symbol='triangle-down', color='lime', size=10)
        ))

    # Fractals DOWN
    if "downFractal" in df.columns:
        fig.add_trace(go.Scatter(
            x=df[df['downFractal']].index,
            y=df[df['downFractal']]['high'] * (1 + offset),
            mode='markers',
            name='Fractal DOWN',
            marker=dict(symbol='triangle-up', color='red', size=10)
        ))

    # =========================
    # 🔹 SL / TP / ENTRY FIX
    # =========================
    for col, name, color, dash in [
        ("sl", "SL", "red", "dash"),
        ("tp", "TP", "green", "dash"),
        ("entry", "ENTRY", "blue", "dot")
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

            valid = df[col].dropna()
            if not valid.empty:
                start_index = valid.index[0]   # 🔥 moment wejścia
                last_val = valid.iloc[-1]

                df_segment = df[df.index >= start_index]

                fig.add_trace(go.Scatter(
                    x=df_segment.index,
                    y=[last_val] * len(df_segment),
                    mode='lines',
                    name=name,
                    line=dict(color=color, dash=dash)
                ))

    # =========================
    # 🔹 LAYOUT
    # =========================
    fig.update_layout(
        title="Chart",
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False
    )

    # =========================
    # 🔥 OUTPUT = NAZWA CSV -> HTML
    # =========================
    output = os.path.join(
        os.path.dirname(file_path),
        os.path.basename(file_path).replace(".csv", ".html")
    )

    fig.write_html(output)

    print(f"✅ Gotowe: {output}")


# =========================
# CLI
# =========================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Użycie: python generate.py practice/long/csv_0001.csv   ")
    else:
        generate_chart(sys.argv[1])