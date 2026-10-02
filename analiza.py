import pandas as pd
import gc
import plotly.graph_objects as go
import os
import time
from openpyxl import load_workbook


def delete_trade_log():
    file_path = 'excel/trade_log.xlsx'
    max_retries = 5

    for attempt in range(1, max_retries + 1):
        try:
            # Próbujemy załadować i od razu "zamknąć" workbook, jeśli otwarty
            wb = load_workbook(file_path)
            wb.close()
            del wb
            gc.collect()  # Wymusza usunięcie referencji

            os.remove(file_path)
            print("[🗑️ USUNIĘTO] trade_log.xlsx został usunięty.")
            return
        except PermissionError:
            print(f"[⚠️] Próba {attempt}: Plik zablokowany, czekam 2s...")
            time.sleep(2)
        except FileNotFoundError:
            print("[ℹ️] Plik już nie istnieje — nie trzeba usuwać.")
            return
        except Exception as e:
            print(f"[❌ BŁĄD USUWANIA] {e}")
            return

    print("[❌ BŁĄD USUWANIA] Nie udało się usunąć pliku excel/trade_log.xlsx po 5 próbach.")


def draw_excel_charts(excel_path):
    with pd.ExcelFile(excel_path) as excel_data:
        sheet_names = excel_data.sheet_names.copy()  # <-- kopiujemy listę nazw arkuszy
        offset_factor = 0.0005  # dla przesunięcia fraktali

    for sheet in sheet_names:
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet)

            # Upewnij się, że kolumna 'time' jest datetime
            if 'time' in df.columns:
                df['time'] = pd.to_datetime(df['time'])
            if 'time' not in df.columns and 'timestamp' in df.columns:
                df['time'] = pd.to_datetime(df['timestamp'])
            
            # Usuń wiersze z NaN w świecach i wskaźnikach
            df = df.dropna(subset=['open', 'high', 'low', 'close', 'DEMA_short', 'DEMA_medium', 'DEMA_long'])

            # Filtruj fraktale
            up_fractals = df[df['upFractal']]
            down_fractals = df[df['downFractal']]

            # Tworzenie wykresu
            fig = go.Figure(data=[
                go.Candlestick(
                    x=df['time'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name='Candles'
                ),
                go.Scatter(x=df['time'], y=df['DEMA_short'], mode='lines', name='DEMA 20', line=dict(color='green')),
                go.Scatter(x=df['time'], y=df['DEMA_medium'], mode='lines', name='DEMA 50', line=dict(color='deepskyblue')),
                go.Scatter(x=df['time'], y=df['DEMA_long'], mode='lines', name='DEMA 100', line=dict(color='#C9A800')),

                # Fraktale UP
                go.Scatter(
                    x=up_fractals['time'],
                    y=up_fractals['low'] - (up_fractals['low'] * offset_factor),
                    mode='markers',
                    name='Fractal UP',
                    marker=dict(symbol='triangle-down', color='lime', size=12)
                ),
                # Fraktale DOWN
                go.Scatter(
                    x=down_fractals['time'],
                    y=down_fractals['high'] + (down_fractals['high'] * offset_factor),
                    mode='markers',
                    name='Fractal DOWN',
                    marker=dict(symbol='triangle-up', color='red', size=12)
                ),
            ])    
            candle_0 = df[df['candle_offset'] == 0]

            if not candle_0.empty:
                entry_price = candle_0['entry_price'].values[0]
                sl_price = candle_0['sl'].values[0]
                tp_price = candle_0['tp'].values[0]

                # Znajdź czas od candle_offset == 0 do candle_offset == 3
                time_slice = df[(df['candle_offset'] >= 0) & (df['candle_offset'] <= 3)]['time']
                if len(time_slice) >= 2:
                    line_x = [time_slice.iloc[0], time_slice.iloc[-1]]

                    fig.add_trace(go.Scatter(
                        x=line_x,
                        y=[entry_price, entry_price],
                        mode='lines',
                        name='Entry',
                        line=dict(color='blue', dash='dash')
                    ))
 
                    fig.add_trace(go.Scatter(
                        x=line_x,
                        y=[sl_price, sl_price],
                        mode='lines',
                        name='SL',
                        line=dict(color='red', dash='dot')
                    ))
 
                    fig.add_trace(go.Scatter(
                        x=line_x,
                        y=[tp_price, tp_price],
                        mode='lines',
                        name='TP',
                        line=dict(color='green', dash='dot')
                    ))

            fig.update_layout(
                title=f"{sheet} — Trade Log Chart",
                xaxis_title='Time',
                yaxis_title='Price',
                xaxis_rangeslider_visible=False
            )

            # Zapisz wykres do HTML
            folder_path = os.path.join('charts')
            os.makedirs(folder_path, exist_ok=True)
            html_file = os.path.join(folder_path, f"chart_{sheet}.html")
            fig.write_html(html_file)

            print(f"[✅ ZAPISANO] Wykres zapisany: {html_file}")
        except Exception as e:
            print(f"[❌ BŁĄD] {sheet}: {e}")
    delete_trade_log()

# Przykładowe wywołanie
draw_excel_charts('excel/trade_log.xlsx')
