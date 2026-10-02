import pandas as pd
import ta
import time
from decimal import Decimal, ROUND_DOWN
from binance.client import Client
from binance.enums import *
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import threading
import traceback
from binance.exceptions import BinanceAPIException
import functools
import requests
from termcolor import colored
import numpy as np

def calculate_dema(series, period):
    ema = series.ewm(span=period, adjust=False).mean()
    dema = 2 * ema - ema.ewm(span=period, adjust=False).mean()
    return dema

def refresh_df_and_indicators(symbol, interval="1m", limit=100):
    try:
        klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close',
            'volume', 'close_time', 'quote_asset_volume',
            'number_of_trades', 'taker_buy_base_volume',
            'taker_buy_quote_volume', 'ignore'
        ])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        # Konwersje
        df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(float)

        # Dodaj DEMA
        df['DEMA_short'] = calculate_dema(df['close'], 20)
        df['DEMA_medium'] = calculate_dema(df['close'], 50)
        df['DEMA_long'] = calculate_dema(df['close'], 100)

        return df

    except Exception as e:
        print(f"[❌ BŁĄD] Nie udało się pobrać i przeliczyć df dla {symbol}: {e}")
        return None

# Ładowanie kluczy API z pliku .env
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Inicjalizacja klienta giełdy (np. Binance)

def retry_on_time_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        for attempt in range(3):
            try:
                return func(*args, **kwargs)
            except BinanceAPIException as e:
                if "-1021" in str(e):
                    print("🕒 API -1021: czas systemowy za szybki – retry za 3s...")
                    time.sleep(3)
                else:
                    raise
        raise Exception("Zbyt wiele prób po błędzie czasu (-1021)")
    return wrapper

# Funkcja do pobrania salda z konta Futures na Binance
@retry_on_time_error
def get_balance():
    balance = client.futures_account_balance()
    for b in balance:
        if b['asset'] == 'USDT':  # Zmienna 'USDT' można zamienić na inną walutę, jeżeli jest potrzeba
            return float(b['balance'])
    return 0.0

# === KONFIGURACJA API ===
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")

client = Client(api_key, api_secret)
client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'
# Parametry transakcji
symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "AVAXUSDT"]  # Możesz dodać więcej par walutowych
position_locks = {symbol: threading.Lock() for symbol in symbols}
entry_price = 0
initial_balance = None

# === OBLICZANIE FRACTALI ===
import pandas as pd
import numpy as np


# Ustawienie wartości okresu (n) do obliczeń fraktali
n = 2

# === Szukanie fractala up ===
def detect_fractals(df):
    if df is None or len(df) < 5:
        print(f"[BŁĄD DEBUG] Brak wystarczających danych do liczenia fraktali.")
        df['upFractal'] = [False] * len(df)
        df['downFractal'] = [False] * len(df)
        return df

    up_fractals = [False, False]  # padding left
    down_fractals = [False, False]

    for i in range(2, len(df) - 2):
        highs = df['high'].iloc[i - 2:i + 3].values
        lows = df['low'].iloc[i - 2:i + 3].values

        center_high = highs[2]
        center_low = lows[2]

        next_high = df['high'].iloc[i + 1]
        next_low = df['low'].iloc[i + 1]

        # DOWN fractal (highest candle)
        if all(center_high > h for j, h in enumerate(highs) if j != 2) and next_high < center_high:
            down_fractals.append(True)
        else:
            down_fractals.append(False)

        # UP fractal (lowest candle)
        if all(center_low < l for j, l in enumerate(lows) if j != 2) and next_low > center_low:
            up_fractals.append(True)
        else:
            up_fractals.append(False)

    # Final padding to match dataframe length
    pad_right = [False] * (len(df) - len(up_fractals))
    df['upFractal'] = up_fractals + pad_right
    df['downFractal'] = down_fractals + pad_right
    return df
# === POBIERANIE DANYCH ===
def get_futures_klines(symbol, interval="1m", limit=500):
    klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)

    df.index = df.index.tz_localize('UTC').tz_convert('Europe/Warsaw')

    for col in ['open', 'high', 'low', 'close']:
        df[col] = df[col].astype(float)
    return df

# === SPRAWDZENIE CZY POZYCJA JEST OTWARTA ===
@retry_on_time_error
def is_position_open(symbol):
    positions = client.futures_position_information(symbol=symbol)
    for pos in positions:
        amt = float(pos['positionAmt'])
        if abs(amt) > 0.0001:  # dokładniejsza kontrola
            return True
    return False


# === DEBUGOWANIE ===
def log_positions():
    for symbol in symbols:
        positions = client.futures_position_information(symbol=symbol)
        for pos in positions:
            amt = float(pos["positionAmt"])
            if abs(amt) > 0.0001:
                print(f"{symbol} => Open Position: {amt} at entry price {pos['entryPrice']}")
    
# === WSKAŹNIKI ===
def apply_dema_indicators(df):
    for period, label in [(20, "short"), (50, "medium"), (100, "long")]:
        ema1 = df["close"].ewm(span=period, adjust=False).mean()
        ema2 = ema1.ewm(span=period, adjust=False).mean()
        df[f"DEMA_{label}"] = 2 * ema1 - ema2
    return df  
# === POZYCJA Z TP I SL ===
def calculate_sl_from_dema(df, side):
    if len(df) < 1:
        return None

    low = df["low"].iloc[-1]
    high = df["high"].iloc[-1]

    dema_values = {
        "short": df["DEMA_short"].iloc[-1],
        "medium": df["DEMA_medium"].iloc[-1],
        "long": df["DEMA_long"].iloc[-1]
    }

    if side == 'BUY':
        valid = [v for v in dema_values.values() if v < low and v != low]
        if valid:
            return round(max(valid), 2)
        else:
            # fallback: bierz najniższą DEMA
            sorted_demas = sorted(dema_values.items(), key=lambda x: x[1], reverse=True)
            for i, (label, val) in enumerate(sorted_demas):
                if val < low and i + 1 < len(sorted_demas):
                    fallback_val = sorted_demas[i + 1][1]
                    return round(fallback_val, 2)
            return None

    elif side == 'SELL':
        valid = [v for v in dema_values.values() if v > high and v != high]
        if valid:
            return round(min(valid), 2)
        else:
            # fallback: bierz najwyższą DEMA
            sorted_demas = sorted(dema_values.items(), key=lambda x: x[1])
            for i, (label, val) in enumerate(sorted_demas):
                if val > high and i + 1 < len(sorted_demas):
                    fallback_val = sorted_demas[i + 1][1]
                    return round(fallback_val, 2)
            return None
    return None


def place_futures_order_with_tp_sl(symbol, side, quantity, entry_price, sl_price):
    try:
        print(f"[ZLECENIE DEBUG] {symbol} | side={side} | qty={quantity} | entry={entry_price} | SL={sl_price}")

        # === WALIDACJA PODSTAWOWA ===
        if sl_price is None or entry_price is None:
            print(f"[❌ BŁĄD LOGICZNY] Brak SL lub ENTRY — nie składam TP/SL")
            return None, None

        if side == 'BUY':
            if sl_price >= entry_price:
                print(f"[❌ BŁĄD LOGICZNY] SL >= ENTRY przy LONG — nie składam")
                return None, None
            tp_price = round(entry_price + 1.5 * (entry_price - sl_price), 2)
            opposite = 'SELL'

        elif side == 'SELL':
            if sl_price <= entry_price:
                print(f"[❌ BŁĄD LOGICZNY] SL <= ENTRY przy SHORT — nie składam")
                return None, None
            tp_price = round(entry_price - 1.5 * (sl_price - entry_price), 2)
            opposite = 'BUY'

        else:
            print(f"[❌ NIEZNANY KIERUNEK] {side}")
            return None, None

        print(f"[✅ PRÓBA TP/SL] side={side} | entry={entry_price} | sl={sl_price} | tp={tp_price}")

        # === MARKET ENTRY ===
        client.futures_create_order(
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=quantity
        )

        # ⏱️ (opcjonalnie) małe opóźnienie na ustawienie pozycji
        import time
        time.sleep(0.5)

        # === TAKE PROFIT ===
        try:
            client.futures_create_order(
                symbol=symbol,
                side=opposite,
                type='TAKE_PROFIT_MARKET',
                stopPrice=str(tp_price),
                closePosition=True,
                timeInForce='GTC'
            )
            print(f"[✅ TP ZLECONE] {tp_price}")
        except Exception as e:
            print(f"[❌ BŁĄD TP] {e}")

        # === STOP LOSS ===
        try:
            client.futures_create_order(
                symbol=symbol,
                side=opposite,
                type='STOP_MARKET',
                stopPrice=str(round(sl_price, 2)),
                closePosition=True,
                timeInForce='GTC'
            )
            print(f"[✅ SL ZLECONE] {sl_price}")
        except Exception as e:
            print(f"[❌ BŁĄD SL] {e}")
    
            if "code=-2021" in str(e):
                print(f"[⛔ AUTO-ZAMKNIĘCIE] SL dla {symbol} nie działa (order would trigger) — zamykam pozycję MARKET")
                try:
                    client.futures_create_order(
                        symbol=symbol,
                        side=side,  # ta sama strona, bo zamykamy
                        type='MARKET',
                        quantity=quantity,
                        reduceOnly=True  # tylko zamyka istniejącą
                    )
                    print(f"[✅ ZAMKNIĘTO] {symbol} zamknięte awaryjnie z powodu błędu SL")
                except Exception as close_e:
                    print(f"[❌ BŁĄD ZAMYKANIA] {symbol}: {close_e}")
    
            return None, None

        print(f"[📥 OTWARTA POZYCJA] {side} {symbol} | ENTRY: {entry_price} | SL: {sl_price} | TP: {tp_price}")
        return tp_price, sl_price

    except Exception as e:
        print(f"[BŁĄD ZLECENIA] {symbol} | {side} | {e}")
        return None, None

# === COŚ Z FRACTALEM ===
def fractal(symbol, df):
    df = detect_fractals(df)
    row = df.iloc[-4]
    timestamp = df.index[-4]

    if row['upFractal']:
        print(f"🟢 up fractal {symbol} NA świecy {timestamp}")
        return "upFractal", timestamp

    elif row['downFractal']:
        print(f"🔴 down fractal {symbol} NA świecy {timestamp}")
        return "downFractal", timestamp

    return None, None

# === ILE KUPUJE ===
def get_trade_quantity(symbol, price):
    if symbol == "BTCUSDT":
        usd_amount = 1000
    elif symbol == "ETHUSDT":
        usd_amount = 800 
    elif symbol == "AVAXUSDT":
        usd_amount = 400  
    elif symbol == "SOLUSDT":
        usd_amount = 600  
    else:
        usd_amount = 200  # fallback

    qty = round(usd_amount / price, 4)  # zaokrąglone do 4 miejsc
    return qty
# === BŁĄD -1111 ===
def get_symbol_precision(symbol):
    exchange_info = client.futures_exchange_info()
    for s in exchange_info['symbols']:
        if s['symbol'] == symbol:
            for f in s['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = float(f['stepSize'])
                if f['filterType'] == 'PRICE_FILTER':
                    tick_size = float(f['tickSize'])
            return step_size, tick_size
    raise ValueError(f"Brak danych precyzji dla {symbol}")

def round_to_step(value, step):
    try:
        if value is None:
            raise ValueError("Wartość do zaokrąglenia (value) jest None")
        step = Decimal(str(step))
        return float((Decimal(str(value)) // step) * step)
    except Exception as e:
        print(f"[round_to_step ERROR] value: {value}, step: {step} | {e}")
        raise

# === GŁÓWNA PĘTLA ===
def trade(symbol):
    df = refresh_df_and_indicators(symbol)
    if df is None:
        print(f"[❌] Nie mogę działać bez świeżego df dla {symbol}")
        return
    #=== resret pullbacku ===
    def reset_pullback_up():
        nonlocal pullback_up_part1, pullback_up_part2
        nonlocal waiting_20, waiting_50, waiting_20_counter, waiting_50_counter
        nonlocal waiting_pullback_up, pullback_up_counter, pullback1_up_counter
        pullback_up_part1 = False
        pullback_up_part2 = False
        waiting_20 = False
        waiting_50 = False
        waiting_20_counter = 0
        waiting_50_counter = 0
        waiting_pullback_up = False
        pullback_up_counter = 0
        pullback1_up_counter = 0
    def reset_pullback_down():
        nonlocal pullback_down_part1, pullback_down_part2
        nonlocal waiting_20_down, waiting_50_down
        nonlocal waiting_20_down_counter, waiting_50_down_counter
        nonlocal waiting_pullback_down, pullback_counter, pullback1_counter

        pullback_down_part1 = False
        pullback_down_part2 = False
        waiting_20_down = False
        waiting_50_down = False
        waiting_20_down_counter = 0
        waiting_50_down_counter = 0
        waiting_pullback_down = False
        pullback_counter = 0
        pullback1_counter = 0
    
    
    position = None
    global initial_balance 
    latest_fractal = None  
    # Flagi etapu pullbacku
    pullback_down_part1 = False
    pullback_down_part2 = False
    waiting_pullback_down = False
    pullback_counter = 0
    pullback1_counter = 0
    pullback_up_part1 = False
    pullback_up_part2 = False
    waiting_pullback_up = False
    pullback_up_counter = 0
    pullback1_up_counter = 0
    last_position_check = 0
    position_open = None
    waiting_20 = False
    waiting_50 = False
    waiting_20_counter = 0
    waiting_50_counter = 0
    waiting_20_down = False
    waiting_50_down = False
    waiting_20_down_counter = 0
    waiting_50_down_counter = 0
    last_used_fractal_time = None
    last_used_fractal_time_down = None


    
    while True:
        lock = position_locks[symbol]
        with lock:
            if initial_balance is None:
                initial_balance = get_balance()
            
            try:
                try:
                    current_price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
                except requests.exceptions.ReadTimeout:
                    print(f"[TIMEOUT] Timeout przy pobieraniu ceny {symbol}. Próbuję ponownie za chwilę.")
                    time.sleep(5)
                    continue

                df = get_futures_klines(symbol)
                df = get_futures_klines(symbol, interval="1m", limit=500)
                if df is None or df.empty:
                    print(f"[BŁĄD] Nie udało się pobrać danych dla {symbol}")
                    return
                df = apply_dema_indicators(df)
                df = detect_fractals(df)


                if df.empty:
                    print(f"[BRAK DANYCH] {symbol}")
                    time.sleep(60)
                    continue

                row = df.iloc[-1]
                latest_fractal = fractal(symbol, df)

            except Exception as e:
                print("Wystąpił wyjątek!")
                print(f"[EXCEPTION] {type(e).__name__}: {str(e) or 'brak treści'}")
                traceback.print_exc()
                reset_pullback_up()
                reset_pullback_down()
                position = None
                pullback_up_part1 = False
                pullback_down_part1 = False
                time.sleep(10)
                continue  # Pomija resztę tej iteracji

# ===================== PULLBACK WZROSTOWY (LONG) =====================
            if (not pullback_up_part1 and
                not waiting_pullback_down and
                not waiting_20 and
                not waiting_50 and
                row['low'] > row['DEMA_short'] and
                row['low'] > row['DEMA_medium'] and
                row['low'] > row['DEMA_long'] and
                row['DEMA_short'] > row['DEMA_medium'] > row['DEMA_long']):
    
                pullback_up_part1 = True
                print(f"up1 {symbol}")
                
                if pullback_down_part1 or waiting_20_down or waiting_50_down:
                    print(f"[RESET] Wykryto UP, ale aktywne DOWN → resetuję DOWN przed UP dla {symbol}")
                    reset_pullback_down()


            elif (pullback_up_part1 and not pullback_up_part2 and
                  row['high'] < row['DEMA_short'] and
                  row['high'] < row['DEMA_medium'] and
                  row['high'] < row['DEMA_long'] and
                  row['DEMA_short'] > row['DEMA_medium'] > row['DEMA_long']):

                pullback_up_part2 = True
                pullback1_up_counter = 0
                print(f"up2 {symbol}")

            if pullback_up_part1 and pullback_up_part2:
                # 🔁 RESET jeśli kolejność DEMA się rozsypała, zanim dotknęło DEMA
                if not (row['DEMA_short'] > row['DEMA_medium'] > row['DEMA_long']):
                    print(f"[RESET] Kolejność DEMA zanikła zanim dotknęło DEMA → resetuję {symbol}")
                    reset_pullback_up()
                    continue

                current_price = float(client.futures_symbol_ticker(symbol=symbol)['price'])

                dema_20 = row['DEMA_short']
                dema_50 = row['DEMA_medium']
                dema_100 = row['DEMA_long']

                dotknieto_20 = current_price <= dema_20
                dotknieto_50 = current_price <= dema_50
                dotknieto_100 = current_price <= dema_100

                # 🖨️ DEBUG PRINT
                print(
                    f"[DEMA DEBUG] {symbol} | CENA: {current_price:.4f} | "
                    f"DEMA20: {dema_20:.4f} ({'✓' if dotknieto_20 else '×'}) | "
                    f"DEMA50: {dema_50:.4f} ({'✓' if dotknieto_50 else '×'}) | "
                    f"DEMA100: {dema_100:.4f} ({'✓' if dotknieto_100 else '×'})"
                )


                # PRIORYTET: DEMA 50 > DEMA 20
                if dotknieto_20 and dotknieto_50:
                    if not waiting_50:
                        waiting_50 = True
                        waiting_50_counter = 0
                        waiting_20 = False
                        waiting_20_counter = 0
                        print(f"[PULLBACK] Dotknięto DEMA 20 i 50 — aktywuję tylko DEMA 50 na {symbol}")

                elif dotknieto_50 and not waiting_50:
                    waiting_50 = True
                    waiting_50_counter = 0
                    if waiting_20:
                        print(f"[INFO] Nadpisuję DEMA 20 → aktywuję DEMA 50 na {symbol}")
                    waiting_20 = False
                    waiting_20_counter = 0
                    print(f"[PULLBACK] waiting_pullback_up aktywowane DEMA 50 {symbol}")

                elif dotknieto_20 and not waiting_20 and not waiting_50:
                    waiting_20 = True
                    waiting_20_counter = 0
                    print(f"[PULLBACK] waiting_pullback_up aktywowane DEMA 20 {symbol}")

                # DOPIERO TERAZ sprawdź czy trzeba zresetować
                if dotknieto_100:
                    print(f"[RESET] Dotknięto DEMA 100 → resetuję {symbol}")
                    reset_pullback_up()
                    continue

            # === Czekanie na fraktala DEMA 50 ===
            if waiting_50:
                # ⛔ RESET jeśli DEMA się rozjechały
                if not (row['DEMA_short'] > row['DEMA_medium'] > row['DEMA_long']):
                    print(f"[RESET] Zmiana kolejności DEMA w trakcie oczekiwania → resetuję {symbol}")
                    reset_pullback_up()
                    continue

                waiting_50_counter += 1
                print(f"czeka na upFractal (DEMA 50) {symbol} | świeca {waiting_50_counter}/4")

                if waiting_50_counter >= 5:
                    print(f"[RESET] Brak fraktala po DEMA 50 → resetuję {symbol}")
                    reset_pullback_up()
                    continue

                new_fractal, fractal_time = fractal(symbol, df)
                if new_fractal == "upFractal" and fractal_time != last_used_fractal_time and not is_position_open(symbol):
                    last_used_fractal_time = fractal_time
                    print(f"[SYGNAŁ] upFractal z {fractal_time} — próbuję LONG na {symbol}")

                    # === OTWARCIE POZYCJI ===
                    entry_price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
                    sl_price = calculate_sl_from_dema(df, 'BUY')

                    if sl_price is None or sl_price <= 0:
                        print(f"[AWARIA SL] Standardowy SL nie działa dla {symbol}, szukam fallbacku")
                        if not dotknieto_50:
                            sl_price = row['DEMA_medium']
                            print(f"[FALLBACK SL] SL = DEMA_medium ({sl_price})")
                        elif not dotknieto_100:
                            sl_price = row['DEMA_long']
                            print(f"[FALLBACK SL] SL = DEMA_long ({sl_price})")
                        elif dotknieto_20:
                            sl_price = row['DEMA_long']
                            print(f"[AWARYJNY SL] Dotknięto 20 → SL = DEMA_long ({sl_price})")
                        else:
                            print(f"[BŁĄD SL] Nie można ustawić SL dla {symbol}")
                            reset_pullback_up()
                            continue

                    qty = get_trade_quantity(symbol, entry_price)
                    if qty <= 0:
                        print(f"[BŁĄD] Ilość pozycji = 0 — nie otwieram LONG na {symbol}")
                        reset_pullback_up()
                        continue

                    step_size, tick_size = get_symbol_precision(symbol)
                    qty = round_to_step(qty, step_size)
                    entry_price = round_to_step(entry_price, tick_size)
                    sl_price = round_to_step(sl_price, tick_size)

                    try:
                        tp, sl = place_futures_order_with_tp_sl(
                            symbol=symbol,
                            side=SIDE_BUY,
                            quantity=qty,
                            entry_price=entry_price,
                            sl_price=sl_price
                        )
                    except Exception as e:
                        print(f"[BŁĄD KRYTYCZNY] place_futures_order_with_tp_sl rzucił wyjątek na {symbol}: {e}")
                        reset_pullback_up()
                        continue

                    if tp is not None:
                        print(f"[OTWARTA POZYCJA] LONG {symbol} | TP: {tp} | SL: {sl}")
                        position = 'LONG'
                        initial_balance = get_balance()
                        reset_pullback_up()
                    else:
                        print(f"[BŁĄD] Nie udało się otworzyć pozycji LONG na {symbol}")
                        reset_pullback_up()

            # === Czekanie na fraktala DEMA 20 ===
            elif waiting_20:
                # ⛔ RESET jeśli DEMA się rozjechały
                if not (row['DEMA_short'] > row['DEMA_medium'] > row['DEMA_long']):
                    print(f"[RESET] Zmiana kolejności DEMA w trakcie oczekiwania → resetuję {symbol}")
                    reset_pullback_up()
                    continue

                waiting_20_counter += 1
                print(f"czeka na upFractal (DEMA 20) {symbol} | świeca {waiting_20_counter}/4")

                if waiting_20_counter >= 5:
                    print(f"[RESET] Brak fraktala po DEMA 20 → resetuję {symbol}")
                    reset_pullback_up()
                    continue

                new_fractal, fractal_time = fractal(symbol, df)
                if new_fractal == "upFractal" and fractal_time != last_used_fractal_time and not is_position_open(symbol):
                    last_used_fractal_time = fractal_time
                    print(f"[SYGNAŁ] upFractal z {fractal_time} — próbuję LONG na {symbol}")
                    entry_price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
                    sl_price = calculate_sl_from_dema(df, 'BUY')

                    if sl_price is None or sl_price <= 0:
                        print(f"[AWARIA SL] Standardowy SL nie działa dla {symbol}, szukam fallbacku")
                        if not dotknieto_50:
                            sl_price = row['DEMA_medium']
                            print(f"[FALLBACK SL] SL = DEMA_medium ({sl_price})")
                        elif not dotknieto_100:
                            sl_price = row['DEMA_long']
                            print(f"[FALLBACK SL] SL = DEMA_long ({sl_price})")
                        elif dotknieto_20:
                            sl_price = row['DEMA_long']
                            print(f"[AWARYJNY SL] Dotknięto 20 → SL = DEMA_long ({sl_price})")
                        else:
                            print(f"[BŁĄD SL] Nie można ustawić SL dla {symbol}")
                            reset_pullback_up()
                            continue

                    qty = get_trade_quantity(symbol, entry_price)
                    if qty <= 0:
                        print(f"[BŁĄD] Ilość pozycji = 0 — nie otwieram LONG na {symbol}")
                        reset_pullback_up()
                        continue

                    step_size, tick_size = get_symbol_precision(symbol)
                    qty = round_to_step(qty, step_size)
                    entry_price = round_to_step(entry_price, tick_size)
                    sl_price = round_to_step(sl_price, tick_size)

                    try:
                        tp, sl = place_futures_order_with_tp_sl(
                            symbol=symbol,
                            side=SIDE_BUY,
                            quantity=qty,
                            entry_price=entry_price,
                            sl_price=sl_price
                        )
                    except Exception as e:
                        print(f"[BŁĄD KRYTYCZNY] place_futures_order_with_tp_sl rzucił wyjątek na {symbol}: {e}")
                        reset_pullback_up()
                        continue

                    if tp is not None:
                        print(f"[OTWARTA POZYCJA] LONG {symbol} | TP: {tp} | SL: {sl}")
                        position = 'LONG'
                        initial_balance = get_balance()
                        reset_pullback_up()
                    else:
                        print(f"[BŁĄD] Nie udało się otworzyć pozycji LONG na {symbol}")
                        reset_pullback_up()

# ===================== PULLBACK SPADKOWY (SHORT) =====================
            if (not pullback_down_part1 and
                not waiting_pullback_up and
                not waiting_20_down and
                not waiting_50_down and
                row['low'] < row['DEMA_short'] and
                row['low'] < row['DEMA_medium'] and
                row['low'] < row['DEMA_long'] and
                row['DEMA_short'] < row['DEMA_medium'] < row['DEMA_long']):

                pullback_down_part1 = True
                print(f"down1 {symbol}")

                if pullback_up_part1 or waiting_20 or waiting_50:
                    print(f"[RESET] Wykryto DOWN, ale aktywne UP → resetuję UP przed DOWN dla {symbol}")
                    reset_pullback_up()


            elif (pullback_down_part1 and not pullback_down_part2 and
                row['high'] > row['DEMA_short'] and
                row['high'] > row['DEMA_medium'] and
                row['high'] > row['DEMA_long'] and
                row['DEMA_short'] < row['DEMA_medium'] < row['DEMA_long']):

                pullback_down_part2 = True
                pullback1_counter = 0
                print(f"down2 {symbol}")

            if pullback_down_part1 and pullback_down_part2:
                # 🔁 RESET jeśli DEMA się rozjechały zanim dotknęło DEMA
                if not (row['DEMA_short'] < row['DEMA_medium'] < row['DEMA_long']):
                    print(f"[RESET] Kolejność DEMA (SHORT) zanikła zanim dotknęło DEMA → resetuję {symbol}")
                    reset_pullback_down()
                    continue
                
                current_price = float(client.futures_symbol_ticker(symbol=symbol)['price'])

                dema_20 = row['DEMA_short']
                dema_50 = row['DEMA_medium']
                dema_100 = row['DEMA_long']
                
                dotknieto_20 = current_price >= dema_20
                dotknieto_50 = current_price >= dema_50
                dotknieto_100 = current_price >= dema_100

                print(
                    f"[DEMA DEBUG] {symbol} | CENA: {current_price:.4f} | "
                    f"DEMA20: {dema_20:.4f} ({'✓' if dotknieto_20 else '×'}) | "
                    f"DEMA50: {dema_50:.4f} ({'✓' if dotknieto_50 else '×'}) | "
                    f"DEMA100: {dema_100:.4f} ({'✓' if dotknieto_100 else '×'})"
                )

                # PRIORYTET: DEMA 50 > DEMA 20
                if dotknieto_20 and dotknieto_50:
                    if not waiting_50_down:
                        waiting_50_down = True
                        waiting_50_down_counter = 0
                        waiting_20_down = False
                        waiting_20_down_counter = 0
                        print(f"[PULLBACK] Dotknięto DEMA 20 i 50 — aktywuję tylko DEMA 50 na {symbol}")

                elif dotknieto_50 and not waiting_50_down:
                    waiting_50_down = True
                    waiting_50_down_counter = 0
                    if waiting_20_down:
                        print(f"[INFO] Nadpisuję DEMA 20 → aktywuję DEMA 50 na {symbol}")
                    waiting_20_down = False
                    waiting_20_down_counter = 0
                    print(f"[PULLBACK] waiting_pullback_down aktywowane DEMA 50 {symbol}")

                elif dotknieto_20 and not waiting_20_down and not waiting_50_down:
                    waiting_20_down = True
                    waiting_20_down_counter = 0
                    print(f"[PULLBACK] waiting_pullback_down aktywowane DEMA 20 {symbol}")

                # Dopiero NA KOŃCU sprawdź, czy resetować
                if dotknieto_100:
                    print(f"[RESET] Dotknięto DEMA 100 → resetuję {symbol}")
                    reset_pullback_down()
                    continue
            # === Czekanie na fraktala DEMA 50 ===
            if waiting_50_down:
                if not (row['DEMA_short'] < row['DEMA_medium'] < row['DEMA_long']):
                    print(f"[RESET] Zmiana kolejności DEMA (SHORT) → resetuję {symbol}")
                    reset_pullback_down()
                    continue


                waiting_50_down_counter += 1
                print(f"czeka na downFractal (DEMA 50) {symbol} | świeca {waiting_50_down_counter}/5")

                if waiting_50_down_counter >= 5:
                    print(f"[RESET] Brak fraktala po DEMA 50 → resetuję {symbol}")
                    reset_pullback_down()
                    continue

                new_fractal, fractal_time = fractal(symbol, df)
                if new_fractal == "downFractal" and fractal_time != last_used_fractal_time_down and not is_position_open(symbol):
                    last_used_fractal_time_down = fractal_time
                    print(f"[SYGNAŁ] downFractal po DEMA 50 — próbuję SHORT na {symbol}")
                    # === OTWARCIE SHORT ===
                    entry_price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
                    sl_price = calculate_sl_from_dema(df, 'SELL')

                    if sl_price is None or sl_price <= 0:
                        print(f"[AWARIA SL] Standardowy SL nie działa dla {symbol}, szukam fallbacku")
                        if not dotknieto_50:
                            sl_price = row['DEMA_medium']
                            print(f"[FALLBACK SL] SL = DEMA_medium ({sl_price})")
                        elif not dotknieto_100:
                            sl_price = row['DEMA_long']
                            print(f"[FALLBACK SL] SL = DEMA_long ({sl_price})")
                        elif dotknieto_20:
                            sl_price = row['DEMA_long']
                            print(f"[AWARYJNY SL] Dotknięto 20 → SL = DEMA_long ({sl_price})")
                        else:
                            print(f"[BŁĄD SL] Nie można ustawić SL dla {symbol}")
                            reset_pullback_down()
                            continue

                    qty = get_trade_quantity(symbol, entry_price)
                    if qty <= 0:
                        print(f"[BŁĄD] Ilość pozycji = 0 — nie otwieram SHORT na {symbol}")
                        reset_pullback_down()
                        continue

                    step_size, tick_size = get_symbol_precision(symbol)
                    qty = round_to_step(qty, step_size)
                    entry_price = round_to_step(entry_price, tick_size)
                    sl_price = round_to_step(sl_price, tick_size)

                    try:
                        tp, sl = place_futures_order_with_tp_sl(
                            symbol=symbol,
                            side=SIDE_SELL,
                            quantity=qty,
                            entry_price=entry_price,
                            sl_price=sl_price
                        )
                    except Exception as e:
                        print(f"[BŁĄD KRYTYCZNY] place_futures_order_with_tp_sl rzucił wyjątek na {symbol}: {e}")
                        reset_pullback_down()
                        continue

                    if tp is not None:
                        print(f"[OTWARTA POZYCJA] SHORT {symbol} | TP: {tp} | SL: {sl}")
                        position = 'SHORT'
                        initial_balance = get_balance()
                        reset_pullback_down()
                    else:
                        print(f"[BŁĄD] Nie udało się otworzyć pozycji SHORT na {symbol}")
                        reset_pullback_down()

            # === Czekanie na fraktala DEMA 20 ===
            elif waiting_20_down:
                # ⛔ RESET jeśli DEMA się rozjechały
                if not (row['DEMA_short'] < row['DEMA_medium'] < row['DEMA_long']):
                    print(f"[RESET] Zmiana kolejności DEMA (SHORT) → resetuję {symbol}")
                    reset_pullback_down()
                    continue


                waiting_20_down_counter += 1
                print(f"czeka na downFractal (DEMA 20) {symbol} | świeca {waiting_20_down_counter}/4")

                if waiting_20_down_counter >= 5:
                    print(f"[RESET] Brak fraktala po DEMA 20 → resetuję {symbol}")
                    reset_pullback_down()
                    continue

                new_fractal, fractal_time = fractal(symbol, df)
                if new_fractal == "downFractal" and fractal_time != last_used_fractal_time_down and not is_position_open(symbol):
                    last_used_fractal_time_down = fractal_time
                    print(f"[SYGNAŁ] downFractal po DEMA 20 — próbuję SHORT na {symbol}")
                    entry_price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
                    sl_price = calculate_sl_from_dema(df, 'SELL')

                    if sl_price is None or sl_price <= 0:
                        print(f"[AWARIA SL] Standardowy SL nie działa dla {symbol}, szukam fallbacku")
                        if not dotknieto_50:
                            sl_price = row['DEMA_medium']
                            print(f"[FALLBACK SL] SL = DEMA_medium ({sl_price})")
                        elif not dotknieto_100:
                            sl_price = row['DEMA_long']
                            print(f"[FALLBACK SL] SL = DEMA_long ({sl_price})")
                        elif dotknieto_20:
                            sl_price = row['DEMA_long']
                            print(f"[AWARYJNY SL] Dotknięto 20 → SL = DEMA_long ({sl_price})")
                        else:
                            print(f"[BŁĄD SL] Nie można ustawić SL dla {symbol}")
                            reset_pullback_down()
                            continue

                    qty = get_trade_quantity(symbol, entry_price)
                    if qty <= 0:
                        print(f"[BŁĄD] Ilość pozycji = 0 — nie otwieram SHORT na {symbol}")
                        reset_pullback_down()
                        continue

                    step_size, tick_size = get_symbol_precision(symbol)
                    qty = round_to_step(qty, step_size)
                    entry_price = round_to_step(entry_price, tick_size)
                    sl_price = round_to_step(sl_price, tick_size)

                    try:
                        tp, sl = place_futures_order_with_tp_sl(
                            symbol=symbol,
                            side=SIDE_SELL,
                            quantity=qty,
                            entry_price=entry_price,
                            sl_price=sl_price
                        )
                    except Exception as e:
                        print(f"[BŁĄD KRYTYCZNY] place_futures_order_with_tp_sl rzucił wyjątek na {symbol}: {e}")
                        reset_pullback_down()
                        continue

                    if tp is not None:
                        print(f"[OTWARTA POZYCJA] SHORT {symbol} | TP: {tp} | SL: {sl}")
                        position = 'SHORT'
                        initial_balance = get_balance()
                        reset_pullback_down()
                    else:
                        print(f"[BŁĄD] Nie udało się otworzyć pozycji SHORT na {symbol}")
                        reset_pullback_down()
                        
            if is_position_open(symbol):
                pass
            else:
                if position:
                    latest_balance = get_balance()
                    pnl = latest_balance - initial_balance
                    print(f"Pozycja zamknięta na {symbol}. Zysk/Strata: {pnl:.2f} USDT | Saldo: {latest_balance:.2f} USDT")
                    initial_balance = latest_balance
                    position = None

            time.sleep(60)


# === HANDLER Z AUTO-RESTARTEM WĄTKU ===
def start_trade_thread(symbol):
    while True:
        try:
            trade(symbol)
        except Exception as e:
            print(f"[THREAD CRASH] {symbol}: {type(e).__name__} — {e}")
            traceback.print_exc()
            print(f"[RESTART] {symbol} → wątek ruszy ponownie za 10s...\n")
            time.sleep(10)

# === URUCHOMIENIE TRADE() Z RESTARTEM ===
threads = []
for symbol in symbols:
    thread = threading.Thread(target=start_trade_thread, args=(symbol,), daemon=True)
    thread.start()
    threads.append(thread)

#=== testnet ===
while True:
    for symbol in symbols:
        try:
            pos = "OPEN" if is_position_open(symbol) else "None"
        except requests.exceptions.ReadTimeout:
            print(f"[TIMEOUT] Timeout przy sprawdzaniu pozycji {symbol}.")
            pos = "Brak danych"
        time.sleep(60)

