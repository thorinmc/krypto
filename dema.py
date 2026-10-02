# region ======================================================= IMPORTY ============================================================
import pandas as pd
from decimal import Decimal, ROUND_FLOOR, InvalidOperation
import ta
import time
import random
from datetime import datetime, timedelta
import pytz
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
from collections import defaultdict
import mplfinance as mpf
import matplotlib.pyplot as plt
import matplotlib
from flask import send_file
matplotlib.use('Agg')
from threading import Thread
from flask import Flask, send_file
import datetime
import plotly.graph_objects as go
from datetime import datetime
from plyer import notification
from openpyxl import load_workbook
from requests.exceptions import RequestException, ConnectionError, Timeout
from predict import predict_image
from predict_long import predict_long
from predict_short import predict_short
import subprocess
from typing import Optional
tp_sl_cache = {}
active_trades = {}
TRADE_CONTEXT = {}
import pyautogui
import pytesseract
from PIL import Image
import re
import os
import csv
import cv2
import hashlib
from concurrent.futures import Future
import warnings
from pynput import keyboard
import sys
import shutil
pyautogui.FAILSAFE = False
global position_active
position_active = False
WARSAW = pytz.timezone("Europe/Warsaw")
first_scan_done = False
last_position_open = None
_tv_last_seen_candle = None
_tv_last_checked_candle = None
x = "tv"
kys = False
OHLC_BOX = (460, 90, 754, 110)   # obszar OHLC
CLOCK_BOX = (1569, 1010, 1592, 1025)   # obszar zegara świecy
CLICK_POINT = (1575, 300)            # punkt kliknięcia w wykres
START_X = 1575
END_X = 730
Y_POS = 300
SAVE_PATH = "ohlc_last.csv"
FOLDER = "tv_ss"
warned_dema_distance = defaultdict(lambda: {"up": False, "down": False})
warned_dema_order = defaultdict(lambda: {"up": False, "down": False})

#endregion
# region ======================================================= TIME Z TV ==========================================================
# region ========================================== TIME =====================================================

def read_clock():
    left, top, right, bottom = CLOCK_BOX

    width = right - left
    height = bottom - top

    if width <= 0 or height <= 0:
        print(f"[❌] read_clock: zły wymiar boxa CLOCK_BOX={CLOCK_BOX}")
        return ""

    # pyautogui.screenshot: region = (left, top, width, height)
    try:
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
    except Exception as e:
        print(f"[❌] read_clock: ScreenshotError: {e} dla regionu {(left, top, width, height)}")
        return ""

    img = screenshot.convert("RGB")
    text = pytesseract.image_to_string(img).strip()
    print("[⏱ OCR zegara] Odczytano:", text)
    return text

# endregion
# endregion
# region ======================================================= LOGOWANIE ==========================================================
# region ========================================== ALWAYS ===================================================

cw = False
kys1 = True
def watch_pixel():
    global cw, kys1
    x = 220
    y = 135
    TARGET_HEX = "#0f0f0f"  # kolor wykywania

    while True:
        # zrób screenshot ekranu
        img = pyautogui.screenshot()

        # pobierz kolor piksela
        r, g, b = img.getpixel((x, y))
        hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b)


        # sprawdź czy to ten kolor
        if hex_color.lower() == TARGET_HEX:
            if cw:
                cw = False
                kys1 = True
           
            do_action(1800, 50)
            time.sleep(2)
            do_action(500, 400)

            if kys1:
                cw = True
                kys1 = False

        time.sleep(30)

# endregion
# region ========================================== ONCE =====================================================

def check_pixel_once():
    global cw, kys1
    x = 220
    y = 135
    TARGET_HEX = "#0f0f0f"  # kolor wykrywania

    # zrób screenshot ekranu
    img = pyautogui.screenshot()

    # pobierz kolor piksela
    r, g, b = img.getpixel((x, y))
    hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b)

    # sprawdź czy to ten kolor
    if hex_color.lower() == TARGET_HEX:
        if cw:
            cw = False
            kys1 = True

        do_action(1750, 50)
        time.sleep(1)
        do_action(500, 400)

        if kys1:
            cw = True
            kys1 = False


# endregion
# endregion
# region ======================================================= FIX OHLC ===========================================================
# region ========================================== 3=9 ======================================================

def fix_leading_3_to_9(val):
    """
    Jeśli liczba zaczyna się od '3' zamień pierwszą cyfrę na '9'
    """
    if val is None:
        return val

    s = str(val).strip()
    if len(s) < 2:
        return val

    first, second = s[0], s[1]

    # case 1: 39...
    if first == "3" and second == "9":
        s = s[1:]  # utnij pierwszą 3 zostaje 9
        return s

    # case 2: 3[0-8]...
    if first == "3" and second in "012345678":
        s = "9" + s[1:]
        return s

    return val

# endregion
# region ========================================== ZA WYSOKA CENA 300K ======================================

def protect_x_val(val, limit=300_000):
    """
    Jeśli OCR da absurd > limit (np 899091.1),
    ucinamy pierwszą cyfrę: 899091.1 -> 89909.1
    """
    try:
        if val is None:
            return None

        f = float(val)
        if f <= limit:
            return f

        s = str(val).replace(",", ".")
        if "." in s:
            i, d = s.split(".", 1)
            if len(i) > 1:
                return float(i[1:] + "." + d)
        else:
            if len(s) > 1:
                return float(s[1:])

        return f
    except Exception:
        return val

# endregion
# region ========================================== KOLEJNOSC POD KLUCZ ======================================

def parse_ohlc_smart(line: str):
    original = line.strip().replace(",", ".").replace(" ", "").replace("\n", "")
    original = re.sub(r'([OHLC])\1+', r'\1', original)  # usuń duplikaty liter
    original = re.sub(r'([OHLC])\.', r'\g<1>0.', original) # napraw C.107 → C0.107

    if original and original[0].isdigit():
        original = "O" + original

    match = re.search(r"O(\d+\.\d+)H(\d+\.\d+)L(\d+\.\d+)C(\d+\.\d+)", original)
    if match:
        o, h, l, c = match.groups()
        return float(o), float(h), float(l), float(c)
    else:
        return None, None, None, None

# endregion
# region ========================================== ZLE LITERY OHLC ==========================================

def fix_missing_letters(raw_text: str) -> str:
    """Dodaje brakujące litery OHLC jeśli OCR je zgubił."""
    sequence = ["O", "H", "L", "C"]
    fixed = ""
    last_letter = None
    token = ""
    for ch in raw_text:
        token += ch
        if re.match(r"\d+\.\d+$", token):  # mamy liczbę z kropką
            fixed += token
            token = ""
            if last_letter in sequence:
                idx = sequence.index(last_letter)
                if idx < len(sequence) - 1:  # np. O->H, H->L, L->C
                    next_letter = sequence[idx + 1]
                    fixed += next_letter
                    last_letter = next_letter
            continue
        if ch in sequence:
            last_letter = ch
            fixed += ch
            token = ""
    fixed += token
    return fixed

# endregion
# region ========================================== KROPKI (TEKST) ===========================================

def fix_number(s: str) -> str:
    """
    Naprawia stringi z OCR, które mają kilka kropek.
    Zostawia tylko ostatnią kropkę jako separator dziesiętny.
    """
    if s is None:
        return None
    s = str(s).strip()

    # jeśli nie ma kropki zwróć jak jest
    if "." not in s:
        return s

    # jeżeli ma jedną kropkę też spoko
    if s.count(".") == 1:
        return s

    # jeżeli ma wiele kropek tylko ostatnia zostaje
    parts = s.split(".")
    int_part = "".join(parts[:-1])   # wszystko przed ostatnią
    frac_part = parts[-1]          
    return int_part + "." + frac_part

# endregion
# region ========================================== KROPKI (FLOAT) ===========================================

def fix_misplaced_dot(value):
    """
    Naprawia błędnie rozpoznane liczby z OCR, np.:
    0.110929 → 110929.0
    """
    try:
        # Konwertuj zawsze na string dla jednolitej obsługi
        s = str(value).strip()

        if s.startswith("0.") and len(s.split(".")[1]) >= 4:
            digits = s.split(".")[1]     # "110929"
            corrected = digits + ".0"    # "110929.0"
            return float(corrected)

        # float typu 0.11... który nie zaczyna się od 0.
        try:
            f = float(s)
            if f < 1 and len(s.split(".")[1]) >= 4:
                digits = s.split(".")[1]
                corrected = digits + ".0"
                print(f"[🔧] Naprawiono przesuniętą kropkę: {s} → {corrected}")
                return float(corrected)
        except:
            pass

        # nic nie zmieniaj jeśli jest normalne
        return float(s)

    except Exception as e:
        print(f"[⚠️] Nie udało się naprawić liczby {value}: {e}")
        return value

# endregion
# region ========================================== POD KLUCZ Z DODATKAMI ====================================

def extract_float_from_text(s: str, default=None):
    """
    Wyciąga pierwszą sensowną liczbę z tekstu, np.
    '76930.3.' -> 76930.3
    '76930,3 dolny.png' -> 76930.3
    'cena: 84 454.0 USDT' -> 84454.0
    '89031.1 12.' -> 89031.1
    """
    if s is None:
        return default

    s = str(s)
    # zamiana przecinka na kropkę
    s = s.replace(",", ".")

    #  NAJPIERW float, POTEM int
    m = re.search(r'[-+]?\d+\.\d+|[-+]?\d+', s)
    if not m:
        return default

    try:
        return float(m.group(0))
    except Exception:
        return default


# endregion
# region ========================================== TYLKO POD 100K ===========================================

def normalize_ohlc(values: dict) -> dict:
    """Naprawia brakującą pierwszą cyfrę w OHLC jeśli któraś ma mniej niż 7 cyfr."""
    fixed = values.copy()

    # Zamień wartości na stringi
    for k, v in fixed.items():
        if v is None:
            continue
        val_str = str(v)

        # Sprawdź czy jest kropka
        if "." not in val_str:
            continue

        przed, po = val_str.split(".")
        total_digits = len(przed + po)

        # Jeśli ma mniej niż 7 cyfr, sprawdzamy
        if total_digits < 7:
            # Zbierz pierwsze cyfry pozostałych wartości
            pierwsze = [
                str(x)[0] for kk, x in fixed.items()
                if kk != k and x is not None and str(x)[0].isdigit()
            ]

            if pierwsze and all(p == "1" for p in pierwsze):
                # Dodajemy '1' z przodu
                fixed[k] = "1" + val_str

    return fixed

# endregion
# endregion
# region ======================================================= FIX CSV ============================================================
# region ========================================== CHUJOWE LINIJKI  =========================================

def safe_read_ohlc_csv(csv_path="ohlc_last.csv", expected_cols=None):
    """
    Czyta CSV i jeśli trafi na ParserError (za dużo pól w linii),
    próbuje auto-naprawy: usuwa zepsute linie i zapisuje plik ponownie.
    Zwraca DataFrame ALBO None, jeśli nic się nie dało uratować.
    """
    try:
        df = pd.read_csv(csv_path)
        return df
    except pd.errors.ParserError as e:
        print(f"[CSV FIX] ParserError przy czytaniu {csv_path}: {e}")

        if not os.path.exists(csv_path):
            print("[CSV FIX] Plik nie istnieje, nie ma czego naprawiać.")
            return None

        # 1) Backup
        backup_path = csv_path + ".bak"
        shutil.copy(csv_path, backup_path)
        print(f"[CSV FIX] Zrobiono backup: {backup_path}")

        # 2) Ręczne filtrowanie linii
        good_lines = []
        with open(csv_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if not lines:
            print("[CSV FIX] Plik pusty.")
            return None

        header = lines[0].rstrip("\n")
        num_cols = len(header.split(","))

        good_lines.append(header + "\n")

        for i, line in enumerate(lines[1:], start=2):  # linie numerujemy od 2 (bo 1 = header)
            line_stripped = line.rstrip("\n")
            parts = line_stripped.split(",")

            if len(parts) == num_cols:
                good_lines.append(line)
            else:
                print(f"[CSV FIX] Usuwam linię {i}: {len(parts)} pól (oczekiwano {num_cols}) → '{line_stripped}'")

        # 3) Nadpisz CSV tylko dobrymi liniami
        with open(csv_path, "w", encoding="utf-8") as f:
            f.writelines(good_lines)

        print(f"[CSV FIX] Nadpisano {csv_path} tylko poprawnymi liniami ({len(good_lines)-1} świec).")

        # 4) Spróbuj jeszcze raz wczytać
        try:
            df = pd.read_csv(csv_path)
            return df
        except Exception as e2:
            print(f"[CSV FIX] Nadal nie mogę wczytać {csv_path} po naprawie: {e2}")

# endregion
# region ========================================== BRAK LINIJEK =============================================

def ensure_trade_columns(csv_path="ohlc_last.csv"):
    """
    Upewnia się, że w CSV są kolumny: side, entry, sl, tp.
    Nic nie usuwa, tylko dodaje brakujące kolumny.
    """
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)

    changed = False
    for col in ["side", "entry", "sl", "tp"]:
        if col not in df.columns:
            df[col] = "none"
            changed = True

    if changed:
        df.to_csv(csv_path, index=False)
        ensure_trade_columns("ohlc_last.csv")
        print(f"[CSV] Dodano brakujące kolumny side/entry/sl/tp w {csv_path}")

# endregion
# endregion
# region ======================================================= FIRST SCAN =========================================================
# region ========================================== FIRST PART ===============================================

def first_part():
    print("[🚀] Start first_part")
    # przygotowanie folderu
    if os.path.exists(FOLDER):
        for f in os.listdir(FOLDER):
            os.remove(os.path.join(FOLDER, f))
    else:
        os.makedirs(FOLDER)
    ohlc_counter = 1
    click_counter = 1
    last_clock_val = None
    triggered = False
    last_click_time = 0
    last_clock_shot = 0  # czas ostatniego screena zegara
    ohlc_counter = 1
    click_counter = 1
    last_clock_val = None
    triggered = False
    last_click_time = 0
    last_clock_shot = 0

    minute_val = None
    while minute_val is None:
        left, top, right, bottom = CLOCK_BOX
        width = right - left
        height = bottom - top

        if width <= 0 or height <= 0:
            print(f"[❌] minute loop: zły CLOCK_BOX={CLOCK_BOX}")
            time.sleep(0.1)
            continue

        try:
            # = (left, top, width, height)
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
        except Exception as e:
            print(f"[❌] minute loop: ScreenshotError: {e} dla regionu {(left, top, width, height)}")
            time.sleep(0.1)
            continue

        img = screenshot.convert("RGB")
        img.save("debug_clock.png")
        text = pytesseract.image_to_string(img).strip()

        try:
            minute_val = int(text[:2])
        except Exception:
            minute_val = None
        if minute_val is not None:
            if minute_val > 60:
                minute_val = None

        time.sleep(0.05)


    # --- ile czekać do minuty 05 ---
    wait_sec = (5 - minute_val) % 60
    print(f"[⏱] Czekam {wait_sec} sekund, żeby minuta była 05")
    time.sleep(wait_sec)

    # ustawiamy czas ostatniego kliknięcia
    last_click_time = time.time()
    triggered = True  # od teraz co 60s wywołuje _do_chuj_action
    for x in range(START_X, END_X - 1, -1):
        pyautogui.moveTo(x, Y_POS)
        now = time.time()
        if now - last_click_time >= 60:
            last_click_time = now
            _do_chuj_action(FOLDER, click_counter)
            click_counter += 1


        # --- zrzut OHLC (co 0.05s) ---
        left, top, right, bottom = OHLC_BOX

        # żadnego map_x, wszystko 1:1
        width = right - left
        height = bottom - top

        if width <= 0 or height <= 0:
            print(f"[❌] OHLC: zły OHLC_BOX={OHLC_BOX} → real=({left},{top},{right},{bottom})")
        else:
            try:
                # pyautogui: region = (left, top, width, height)
                screenshot = pyautogui.screenshot(region=(left, top, width, height))
            except Exception as e:
                print(f"[❌] OHLC: ScreenshotError: {e} dla regionu {(left, top, width, height)}")
            else:
                img = screenshot.convert("RGB")
                fname = os.path.join(FOLDER, f"ohlc_{ohlc_counter:04d}.png")
                img.save(fname)
                ohlc_counter += 1

        time.sleep(0.05)  # pauza między OHLC

# endregion
# region ========================================== AKTUALNA POZ =============================================

def _do_chuj_action(folder, click_counter):
    # zapisz aktualną pozycję
    pos = pyautogui.position()

    time.sleep(0.1)
    pyautogui.moveTo(CLICK_POINT[0], CLICK_POINT[1])

    # screenshot OHLC przy triggerze
    left, top, right, bottom = OHLC_BOX

    width = right - left
    height = bottom - top

    if width <= 0 or height <= 0:
        print(f"[❌] CLICK: zły OHLC_BOX={OHLC_BOX} → region=({left}, {top}, {right}, {bottom})")
    else:
        try:
            # pyautogui.screenshot: region = (left, top, width, height)
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
        except Exception as e:
            print(f"[❌] CLICK: ScreenshotError: {e} dla regionu {(left, top, width, height)}")
        else:
            img = screenshot.convert("RGB")
            fname = os.path.join(folder, f"click_{click_counter:04d}.png")
            img.save(fname)


    # wróć do poprzedniej pozycji -2px
    pyautogui.moveTo(pos.x - 2, pos.y)

#endregion
# region ========================================== TEST FLOAT ===============================================

def is_valid_number(x):
    """Sprawdza, czy wartość to poprawna liczba (float/int) i nie jest None."""
    try:
        return x is not None and float(x) == float(x)
    except:
        return False

# endregion
# region ========================================== DEF FIRST SCAN ===========================================

def first_scan():
    first_part()
    global kys

    rows = []

    # =========================
    # 1️⃣ LIVE SCREENSHOT LOOP
    # =========================
    def ss_loop():
        last_minute = None
        print("[SS] Loop start")

        while not kys:
            now = datetime.now(WARSAW)

            if now.second == 5 and now.minute != last_minute:
                last_minute = now.minute
                time.sleep(0.15)

                try:
                    do_action(START_X, Y_POS)

                    left, top, right, bottom = OHLC_BOX
                    screenshot = pyautogui.screenshot(
                        region=(left, top, right - left, bottom - top)
                    )

                    fname = os.path.join(
                        "tv_ss", f"live_{now.strftime('%H%M')}.png"
                    )
                    screenshot.convert("RGB").save(fname)

                    print(f"[📸 SS] {fname}")

                except Exception as e:
                    print(f"[❌ SS] {e}")

            time.sleep(0.2)

        print("[SS] Loop stop")

    threading.Thread(target=ss_loop, daemon=True).start()

    # =========================
    # 2️⃣ FIRST PASS: OHLC + CLICK
    # =========================
    folder = "tv_ss"
    files = sorted(os.listdir(folder))

    ohlc_files  = sorted([f for f in files if f.startswith("ohlc_")])
    click_files = sorted([f for f in files if f.startswith("click_")])

    base_ts = pd.Timestamp.now(tz="Europe/Warsaw").floor("min") - pd.Timedelta(minutes=1)

    ts_ohlc  = base_ts
    ts_click = base_ts + pd.Timedelta(minutes=1)

    ordered_files = ohlc_files + click_files

    last_ohlc = None

    for fname in ordered_files:
        fpath = os.path.join(folder, fname)

        img = Image.open(fpath)
        custom_config = r'--psm 6 -c tessedit_char_whitelist=OHLCE0123456789.,€'
        text = pytesseract.image_to_string(img, config=custom_config)

        text = text.replace(",", ".")
        text = fix_missing_letters(text)
        text = text.replace("C€", "C").replace("C €", "C")
        text = re.sub(r'([OHLC])\1+', r'\1', text)

        if re.search(r'\d+\.\d+\.\d+', text):
            text = re.sub(r'(\d+\.\d+)(\d+\.\d+)', r'\1 H\2', text)

        values = {}

        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue

            if line[0] == "0":
                line = "O" + line[1:]

            if re.search(r"\d\.\d+$", line):
                last_num = re.search(r"(\d+\.\d+)$", line).group(1)
                line = line + " C" + last_num

            o, h, l, c = parse_ohlc_smart(line)

            if o is not None:
                values["O"] = fix_misplaced_dot(fix_number(fix_leading_3_to_9(o)))
            if h is not None:
                values["H"] = fix_misplaced_dot(fix_number(fix_leading_3_to_9(h)))
            if l is not None:
                values["L"] = fix_misplaced_dot(fix_number(fix_leading_3_to_9(l)))
            if c is not None:
                values["C"] = fix_misplaced_dot(fix_number(fix_leading_3_to_9(c)))

        if len(values) == 4 and all(is_valid_number(v) for v in values.values()):
            floats = list(map(float, values.values()))
            if max(floats) - min(floats) <= 400 and all(v >= 50000 for v in floats):

                current = f"O{values['O']}_H{values['H']}_L{values['L']}_C{values['C']}"

                if current != last_ohlc:
                    if fname.startswith("ohlc_"):
                        ts = ts_ohlc
                        ts_ohlc -= pd.Timedelta(minutes=1)
                    else:
                        ts = ts_click
                        ts_click += pd.Timedelta(minutes=1)

                    rows.append({
                        "open": values["O"],
                        "high": values["H"],
                        "low": values["L"],
                        "close": values["C"],
                        "timestamp": ts,
                    })

                    last_ohlc = current

        if os.path.exists(fpath):
            os.remove(fpath)

    # =========================
    # 3️⃣ SECOND PASS: LIVE FILES
    # =========================
    print("[FIRST_SCAN] Second pass – live_")

    files_after = sorted(os.listdir(folder))
    live_files = [f for f in files_after if f.startswith("live_")]

    ts_live = ts_click

    for fname in live_files:
        fpath = os.path.join(folder, fname)

        img = Image.open(fpath)
        text = pytesseract.image_to_string(
            img,
            config=r'--psm 6 -c tessedit_char_whitelist=OHLCE0123456789.,€'
        )

        text = text.replace(",", ".")
        text = fix_missing_letters(text)
        text = re.sub(r'([OHLC])\1+', r'\1', text)

        values = {}

        for line in text.splitlines():
            o, h, l, c = parse_ohlc_smart(line)
            if o: values["O"] = fix_number(o)
            if h: values["H"] = fix_number(h)
            if l: values["L"] = fix_number(l)
            if c: values["C"] = fix_number(c)

        if len(values) == 4:
            rows.append({
                "open": values["O"],
                "high": values["H"],
                "low": values["L"],
                "close": values["C"],
                "timestamp": ts_live,
            })

            print(f"[FIRST_SCAN LIVE ADD] {fname} ts={ts_live}")
            ts_live += pd.Timedelta(minutes=1)

        if os.path.exists(fpath):
            os.remove(fpath)

    # =========================
    # 4️⃣ SAVE CSV
    # =========================
    if rows:
        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.sort_values("timestamp").tail(500)

        df.to_csv(SAVE_PATH, index=False)

        recalc_fractals_in_csv(SAVE_PATH)
        ensure_trade_columns(SAVE_PATH)

        kys = True
        print(f"[✅] Zapisano {len(df)} świec do {SAVE_PATH}")
    else:
        print("[⚠️] Brak poprawnych świec do zapisania")


#endregion
# endregion
# region ======================================================= DODATKI OHLC =======================================================
# region ========================================== SCREEN ENTRY =============================================


def read_number_from_image(image_path):
    if not os.path.exists(image_path):
        print(f"[⚠️] Brak pliku {image_path} – nic nie zwracam.")
        return None

    img = Image.open(image_path)
    custom_config = r'--psm 6 -c tessedit_char_whitelist=0123456789,'
    text = pytesseract.image_to_string(img, config=custom_config)

    # Zamiana przecinka na kropkę i usunięcie spacji
    text = text.replace(",", ".").strip()

    # Wyciągnięcie pierwszej liczby z tekstu
    match = re.search(r"\d+(\.\d+)?", text)
    if match:
        number = float(match.group())
        return number
    else:
        print(f"[⚠️] Nie udało się znaleźć liczby w '{text}' z pliku {image_path}")
        close_position_tv()
        close_position()
        return None

# endregion
# endregion
# region ======================================================= ZAPIS CSV ==========================================================
# region ========================================== ZAPIS OTWARTEJ POZYCJI ===================================

def save_trade_to_csv(
    symbol,
    side,
    entry_price,
    sl_price,
    tp_price,
    csv_path="ohlc_last.csv"
):
    """
    Jedna funkcja:
    - bierze ostatnią świecę z csv_path
    - dopisuje: symbol, side, entry, sl, tp
    - tworzy brakujące kolumny jeśli trzeba
    - ZAWSZE zapisuje CSV bez indexu
    - ZAWSZE używa kolumny 'timestamp'
    """

    try:
        if not os.path.exists(csv_path):
            print(f"[CSV ⚠️] Brak pliku {csv_path} — nie zapisuję trade info.")
            return

        # --- Wczytaj CSV ---
        df = pd.read_csv(csv_path)

        # --- 🔥 usuń przypadkowy index ---
        for col in ("Unnamed: 0", "index"):
            if col in df.columns:
                df = df.drop(columns=[col])

        if "timestamp" not in df.columns:
            print(f"[CSV ⚠️] Brak kolumny 'timestamp' w {csv_path} — nie zapisuję trade info.")
            return

        # --- parsuj czas i sortuj ---
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            format="%Y-%m-%d %H:%M:%S%z",
            utc=True,
            errors="coerce"
        )
        df = df.dropna(subset=["timestamp"]).sort_values("timestamp")

        if df.empty:
            print("[CSV ⚠️] CSV pusty po filtrowaniu — nie zapisuję trade info.")
            return

        # --- zapewnij kolumny ---
        for col in ("symbol", "side", "entry", "sl", "tp"):
            if col not in df.columns:
                df[col] = "none"

        # --- ostatnia świeca ---
        idx = df.index[-1]

        # --- sprawdź czy pozycja otwarta ---
        try:
            position_open = is_position_open(symbol)
        except Exception as e:
            print(f"[CSV ⚠️] Błąd sprawdzania pozycji {symbol}: {e}")
            position_open = False

        # =========================================================
        # ❌ BRAK POZYCJI → wymuś "none"
        # =========================================================
        if not position_open:
            df.at[idx, "symbol"] = symbol
            df.at[idx, "side"]   = "none"
            df.at[idx, "entry"]  = "none"
            df.at[idx, "sl"]     = "none"
            df.at[idx, "tp"]     = "none"

            df.tail(500).to_csv(csv_path, index=False)
            ensure_trade_columns(csv_path)

            print(f"[CSV ✅] Brak pozycji — zapisano 'none' dla {symbol}")
            return

        # =========================================================
        # ✅ POZYCJA OTWARTA
        # =========================================================
        cached = tp_sl_cache.get(symbol)

        if cached:
            side_src  = cached.get("side", side)
            entry_src = cached.get("entry", entry_price)
            sl_src    = cached.get("sl", sl_price)
            tp_src    = cached.get("tp", tp_price)
        else:
            side_src  = side
            entry_src = entry_price
            sl_src    = sl_price
            tp_src    = tp_price

        # --- normalizacja side ---
        if isinstance(side_src, str):
            s = side_src.upper()
            if s in ("BUY", "LONG"):
                side_csv = "long"
            elif s in ("SELL", "SHORT"):
                side_csv = "short"
            else:
                side_csv = side_src
        else:
            side_csv = str(side_src)

        # --- zapis wartości ---
        df.at[idx, "symbol"] = symbol
        df.at[idx, "side"]   = side_csv
        df.at[idx, "entry"]  = "none" if entry_src is None else float(entry_src)
        df.at[idx, "sl"]     = "none" if sl_src is None else float(sl_src)
        df.at[idx, "tp"]     = "none" if tp_src is None else float(tp_src)

        # --- ZAPIS ---
        df.tail(500).to_csv(csv_path, index=False)
        ensure_trade_columns(csv_path)

        print(
            f"[CSV ✅] Trade zapisany: {symbol} | {side_csv} | "
            f"entry={entry_src}, sl={sl_src}, tp={tp_src}"
        )

    except Exception as e:
        print(f"[CSV ❌] Błąd zapisu trade do {csv_path}: {e}")


# endregion
# region ========================================== ZATRZYMANIE TRADE ========================================
# endregion
# region ========================================== ZATRZYMANIE TRADE END ====================================

def clear_trade_in_csv(csv_path="ohlc_last.csv"):
    """
    Czyści INFORMACJE o trade (side/entry/sl/tp) w OSTATNIEJ świecy,
    ale nie usuwa świecy ani kolumn.
    """
    if not os.path.exists(csv_path):
        print(f"[⚠️] clear_trade_in_csv: brak pliku {csv_path}")
        return

    df = pd.read_csv(csv_path)

    # upewnij się, że kolumny istnieją
    for col in ["side", "entry", "sl", "tp"]:
        if col not in df.columns:
            df[col] = "none"

    if df.empty:
        print("[⚠️] clear_trade_in_csv: pusty df")
        df.to_csv(csv_path, index=False)
        return

    idx = df.index[-1]  # ostatnia świeca

    df.at[idx, "side"] = "none"
    df.at[idx, "entry"] = "none"
    df.at[idx, "sl"] = "none"
    df.at[idx, "tp"] = "none"

    df.to_csv(csv_path, index=False)
    print(f"[CSV] Wyczyszczono trade w ostatniej świecy ({csv_path})")

# endregion
# endregion
# region ======================================================= TRENING AI =========================================================

def training():
    print_once("startuje training")
    csv_path = "ohlc_last.csv"

    last_side = "none"
    file_index = 1

    start_time = None
    start_time_minus_50 = None

    while True:
        data = pd.read_csv(csv_path)

        if len(data) < 2:
            time.sleep(50)
            continue

        # 🔹 konwersja czasu
        data["timestamp"] = pd.to_datetime(data["timestamp"])

        i = len(data) - 1
        row = data.iloc[i]

        side = row["side"]
        current_time = row["timestamp"]



        # =========================
        # 🔹 START TRADE
        # =========================
        if last_side == "none" and side in ["long", "short"]:
            start_time = current_time
            start_time_minus_50 = start_time - pd.Timedelta(minutes=50)

            print("START:", side, "|", start_time)

        # =========================
        # 🔹 KONIEC TRADE
        # =========================
        if last_side in ["long", "short"] and side == "none":
            end_time = current_time

            # 🔥 KLUCZ — filtr po czasie
            fragment = data[
                (data["timestamp"] >= start_time_minus_50) &
                (data["timestamp"] <= end_time)
            ]

            folder = f"practice/{last_side}"
            os.makedirs(folder, exist_ok=True)

            filename = f"{folder}/csv_{file_index:04d}.csv"
            while os.path.exists(filename):
                file_index += 1
                filename = f"{folder}/csv_{file_index:04d}.csv"

            fragment.to_csv(filename, index=False)

            print("ZAPIS:", filename)
            print("OD:", start_time_minus_50, "DO:", end_time)
            print("ILE ŚWIEC:", len(fragment))
            print("-" * 40)

            file_index += 1

        last_side = side

        time.sleep(50)

# endregion
# region ======================================================= DODATKI ============================================================
# region ========================================== DO ACTION ================================================

def do_action(*args, save_path="screenshot.png"):
    """
    args:
      - (x, y) -> klik / move w punkt (DOKŁADNIE takie x, y jak podasz)
      - (left, top, right, bottom) -> screenshot
        (DOKŁADNIE takie współrzędne jak podasz)
    """
    # 🔹 2 argumenty → klik / move
    if len(args) == 2:
        x, y = args  # nic nie zmieniamy

        if cw:
            pyautogui.moveTo(x, y)
        else:
            pyautogui.click(x, y)

    # 🔹 4 argumenty → screenshot
    elif len(args) == 4:
        left, top, right, bottom = args  # nic nie zmieniamy

        width = right - left
        height = bottom - top

        if width <= 0 or height <= 0:
            print(f"[⚠] Zły region screena: width={width}, height={height}")
            return None

        region = (left, top, width, height)

        try:
            img = pyautogui.screenshot(region=region)
        except Exception as e:
            print(f"[❌] ScreenshotError (pyautogui): {e} dla regionu {region}")
            return None

        img = img.convert("RGB")
        img.save(save_path)
        return img

    else:
        raise ValueError("Podaj 2 liczby (x, y) dla kliknięcia albo 4 liczby (left, top, right, bottom) dla screena.")


# endregion
# region ========================================== PRINT ONCE ===============================================

_printed_messages = set()

def print_once(msg):
    if msg not in _printed_messages:
        print(msg)
        _printed_messages.add(msg)

# endregion
# region ========================================== CTRL Q ===================================================

def setup_exit_shortcut():
    def on_press(key):
        pass  # nie potrzebujemy

    def on_release(key):
        # CTRL+Q: ctrl musi być wciśnięty, a teraz wychodzi 'q'
        try:
            if key.char == 'q' and ctrl_pressed[0]:
                print("\n[🛑] Wciśnięto CTRL+Q → wyłączam bota.")
                os._exit(0)
        except:
            pass

        # sprawdzamy, czy puściliśmy ctrl
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            ctrl_pressed[0] = False

    def on_press_ctrl(key):
        # jeśli wciśnięty ctrl
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            ctrl_pressed[0] = True

    ctrl_pressed = [False]

    listener = keyboard.Listener(
        on_press=on_press_ctrl,
        on_release=on_release
    )
    listener.daemon = True
    listener.start()

    print("[⌨️] Skrót CTRL+Q aktywny — użyj go aby zakończyć bota.")

# endregion
# region ========================================== OPEN TV ==================================================

def open_tv():
    do_action(2200, 1100)
    time.sleep(10)
    do_action(1300, 100)
    for _ in range(10):
        pyautogui.press('left')

    pyautogui.scroll(-3)  

# endregion
# endregion
# region ======================================================= DF/CSV =============================================================
# region ========================================== TEST DF + CSV  ===========================================
# endregion
# region ========================================== TIMESTAMP ================================================

def ensure_datetime_index(df, tz=WARSAW):
    """
    Zapewnia, że DF ma DatetimeIndex w zadanej strefie czasowej.
    UWAGA: Po tej funkcji 'timestamp' NIE JEST kolumną.
    TYLKO do obliczeń / analizy / wykresów.
    """
    if isinstance(df.index, pd.DatetimeIndex):
        if df.index.tz is None:
            df.index = df.index.tz_localize(tz)
        else:
            df.index = df.index.tz_convert(tz)
        return df

    if "timestamp" in df.columns:
        ts = pd.to_datetime(
            df["timestamp"],
            format="%Y-%m-%d %H:%M:%S%z",
            utc=True,
            errors="coerce"
        )
        ts = ts.dropna()

        if ts.dt.tz is None:
            ts = ts.dt.tz_localize(tz)
        else:
            ts = ts.dt.tz_convert(tz)

        df = df.loc[ts.index].copy()
        df.drop(columns=["timestamp"], inplace=True)
        df.index = ts
        return df

    raise ValueError("DF nie ma timestamp ani w kolumnie ani w indexie")

# endregion
# region ========================================== FRACTAL CSV ==============================================
# region ================================================= FRACTAL 1 ====================================================

def sync_fractals_from_df_to_csv(df_with_fractals, csv_path="ohlc_last.csv"):
    """
    df_with_fractals – DF, na którym draw chart pokazuje fractale.
    Zakładamy, że ma timestamp (w indexie albo jako kolumna) i kolumny upFractal / downFractal.
    Przepisujemy to do ohlc_last.csv -> kolumna 'fractal': 'up' / 'down' / 'none'.
    """
    import pandas as pd
    import os

    if not os.path.exists(csv_path):
        print("[fractals->csv] Brak pliku CSV, przerywam.")
        return

    df_csv = pd.read_csv(csv_path)

    if 'timestamp' not in df_csv.columns:
        print("[fractals->csv] Brak timestamp w CSV.")
        return

    # przygotuj timestampy w CSV
    df_csv['timestamp'] = pd.to_datetime(df_csv['timestamp'], utc=True, errors="coerce")
    df_csv = df_csv.dropna(subset=['timestamp'])

    # przygotuj df fractali
    df_f = df_with_fractals.copy()
    if 'timestamp' in df_f.columns:
        df_f['timestamp'] = pd.to_datetime(df_f['timestamp'], utc=True, errors="coerce")
        df_f = df_f.dropna(subset=['timestamp'])
        df_f = df_f.set_index('timestamp')
    else:
        df_f.index = pd.to_datetime(df_f.index, utc=True, errors="coerce")
        df_f = df_f.dropna(axis=0, how="any")

    if 'upFractal' not in df_f.columns and 'downFractal' not in df_f.columns:
        print("[fractals->csv] df_with_fractals nie ma upFractal/downFractal.")
        return

    # przygotuj mapę timestamp -> 'up'/'down'
    fractal_map = {}
    for ts, row in df_f.iterrows():
        if bool(row.get('upFractal', False)):
            fractal_map[ts] = "up"
        elif bool(row.get('downFractal', False)):
            fractal_map[ts] = "down"

    # dataframe z mapy
    df_map = pd.DataFrame(
        [(ts, v) for ts, v in fractal_map.items()],
        columns=['timestamp', 'fractal_from_df']
    )
    df_map['timestamp'] = pd.to_datetime(df_map['timestamp'], utc=True)

    # merge po timestamp
    df_merged = df_csv.merge(df_map, on='timestamp', how='left')

    # jeśli nie ma kolumny fractal, stworzymy
    if 'fractal' not in df_merged.columns:
        df_merged['fractal'] = "none"

    # jeśli fractal_from_df jest nie-NaN, nadpisuje kolumnę fractal
    df_merged['fractal'] = df_merged['fractal_from_df'].combine_first(df_merged['fractal'])

    # sprzątamy kolumnę pomocniczą
    df_merged = df_merged.drop(columns=['fractal_from_df'])

    df_merged.to_csv(csv_path, index=False)

# endregion
# region ================================================= FRACTAL 2 ====================================================

def recalc_fractals_in_csv(csv_path="ohlc_last.csv"):
    if not os.path.exists(csv_path):
        print("[fractals] Brak pliku CSV")
        return

    df = safe_read_ohlc_csv(csv_path)
    if df is None or df.empty:
        print(f"[fractals] Pusty lub uszkodzony CSV — przerywam")
        return

    if "timestamp" not in df.columns:
        print("[fractals ⚠️] Brak kolumny 'timestamp' — pomijam fractale")
        return

    # === timestamp → datetime ===
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    df = df.sort_values("timestamp")

    if df.empty:
        print("[fractals] Brak poprawnych timestampów")
        return

    # === index ===
    df.set_index("timestamp", inplace=True)

    # === OHLC ===
    for col in ["open", "high", "low", "close"]:
        if col not in df.columns:
            print(f"[fractals ⚠️] Brak kolumny {col}")
            return
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["open", "high", "low", "close"])
    if df.empty:
        print("[fractals] Brak poprawnych OHLC")
        return

    df = df.loc[:, ~df.columns.duplicated()]

    # === wyczyść stare fractale ===
    for col in ["upFractal", "downFractal", "fractal"]:
        if col in df.columns:
            df.drop(columns=[col], inplace=True)

    # === fractale ===
    try:
        df, _ = detect_fractals(df)
    except TypeError:
        df = detect_fractals(df)

    # === mapowanie ===
    df["fractal"] = "none"
    for ts, row in df.iterrows():
        if bool(row.get("upFractal", False)):
            df.at[ts, "fractal"] = "up"
        elif bool(row.get("downFractal", False)):
            df.at[ts, "fractal"] = "down"

    # === ostatnie 2 świece = none ===
    if len(df) >= 2:
        df.iloc[-2:, df.columns.get_loc("fractal")] = "none"

    # === cleanup ===
    df.drop(columns=[c for c in ["upFractal", "downFractal"] if c in df.columns], inplace=True)

    # === zapis ===
    df.reset_index(inplace=True)
    df.to_csv(csv_path, index=False)
    ensure_trade_columns(csv_path)

# endregion
# endregion
# region ========================================== ALL TV ===================================================
# region ============================== ALL 1 ==================================

def refresh_df_and_indicators_tv(symbol=None, interval="1m", limit=500):
    try:
        if not os.path.exists(SAVE_PATH):
            print(f"[TV ⚠️] Brak pliku {SAVE_PATH}")
            return None

        df = pd.read_csv(SAVE_PATH)

        # =====================================================
        # 1️⃣ WALIDACJA CSV
        # =====================================================
        if df.empty:
            print(f"[TV ⚠️] CSV pusty: {SAVE_PATH}")
            return None

        if "timestamp" not in df.columns:
            print(f"[TV ⚠️] Brak kolumny 'timestamp' w {SAVE_PATH}")
            return None

        # =====================================================
        # 2️⃣ TIMESTAMP → tz-aware (KOLUMNA)
        # =====================================================
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            format="%Y-%m-%d %H:%M:%S%z",
            utc=True,
            errors="coerce"
        )
        df = df.dropna(subset=["timestamp"])

        if df.empty:
            print(f"[TV ⚠️] Brak poprawnych timestampów w {SAVE_PATH}")
            return None

        df["timestamp"] = df["timestamp"].dt.tz_convert("Europe/Warsaw")

        # =====================================================
        # 3️⃣ SORT + LIMIT
        # =====================================================
        df = df.sort_values("timestamp").tail(limit)

        # =====================================================
        # 4️⃣ KONWERSJA OHLC
        # =====================================================
        for col in ["open", "high", "low", "close"]:
            if col not in df.columns:
                print(f"[TV ⚠️] Brak kolumny {col}")
                return None
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["open", "high", "low", "close"])

        if len(df) < 20:
            print(f"[TV ⚠️] Za mało świec do DEMA ({len(df)})")
            return None

        # =====================================================
        # 5️⃣ OBLICZENIA (INDEX TYLKO LOKALNIE)
        # =====================================================
        df_calc = df.copy()
        df_calc.set_index("timestamp", inplace=True)
        df_calc = df_calc[~df_calc.index.duplicated(keep="last")]

        df_calc["DEMA_short"]  = calculate_dema(df_calc["close"], 20)
        df_calc["DEMA_medium"] = calculate_dema(df_calc["close"], 50)
        df_calc["DEMA_long"]   = calculate_dema(df_calc["close"], 100)

        df_calc = df_calc.dropna(subset=["DEMA_short", "DEMA_medium", "DEMA_long"])

        if df_calc.empty:
            print("[TV ⚠️] DEMA puste po obliczeniach")
            return None

        return df_calc

    except Exception as e:
        print(f"[❌ BŁĄD TV DF] {SAVE_PATH}: {e}")
        return None
# endregion
# region ============================== ALL 2 ==================================

def get_futures_klines_tv(symbol=None, interval="1m", limit=500, path="ohlc_last.csv"):
    """
    Czyta OHLC z CSV (np. TradingView OCR) – WERSJA SAFE
    """
    try:
        if not os.path.exists(path):
            print(f"[TV ⚠️] Brak pliku {path}")
            return None

        df = pd.read_csv(path)

        if df.empty:
            print(f"[TV ⚠️] Pusty CSV: {path}")
            return None

        if "timestamp" not in df.columns:
            print(f"[TV ⚠️] Brak kolumny 'timestamp' w {path}")
            return None

        # === timestamp ===
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
        df = df.dropna(subset=["timestamp"])

        if df.empty:
            print(f"[TV ⚠️] Brak poprawnych timestampów w {path}")
            return None

        df["timestamp"] = df["timestamp"].dt.tz_convert("Europe/Warsaw")
        df = df.sort_values("timestamp")
        df.set_index("timestamp", inplace=True)

        df = df[~df.index.duplicated(keep="last")]

        # === OHLC ===
        for col in ["open", "high", "low", "close"]:
            if col not in df.columns:
                print(f"[TV ⚠️] Brak kolumny {col}")
                return None
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["open", "high", "low", "close"])
        if df.empty:
            print(f"[TV ⚠️] Brak poprawnych OHLC w {path}")
            return None

        if "index" in df.columns:
            df.drop(columns=["index"], inplace=True)

        df = df.loc[:, ~df.columns.duplicated()]

        # === DEMA ===
        df["DEMA_short"] = calculate_dema(df["close"], 20)
        df["DEMA_medium"] = calculate_dema(df["close"], 50)
        df["DEMA_long"] = calculate_dema(df["close"], 100)

        return df.tail(limit)

    except Exception as e:
        print(f"[⛔ BŁĄD ODCZYTU EXCELA] {path}: {e}")
        return None
# endregion
# endregion
# region ========================================== DF DO CSV PRZY BRAKU DANYCH ==============================
# endregion
# region ========================================== DEMA DO DF ===============================================
# endregion
# region ========================================== BINANCE ==================================================
# region ================================ TRADE ====================================

def attach_trade_to_latest_candle(
    symbol, side, entry_price, sl_price, tp_price,
    csv_path="ohlc_last.csv"
):
    if not os.path.exists(csv_path):
        print("[⚠️] Brak ohlc_last.csv — nie zapisuję trade info")
        return

    df = pd.read_csv(csv_path)

    if "timestamp" not in df.columns:
        print("[⚠️] Brak timestamp w CSV — nie zapisuję trade info")
        return

    # + kolumny jeśli ich nie ma
    for col in ["side", "entry", "sl", "tp", "symbol"]:
        if col not in df.columns:
            df[col] = "none"

    # parsowanie czasu i sortowanie
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        format="%Y-%m-%d %H:%M:%S%z",
        utc=True,
        errors="coerce"
    )
    df = df.dropna(subset=["timestamp"])
    df = df.sort_values("timestamp")

    if df.empty:
        print("[⚠️] CSV jest pusty — nie mam świecy na trade info")
        return

    idx = df.index[-1]  # ostatnia świeca

    # 🔥 POBIERAMY CACHE OTWARCIA POZYCJI
    cached = tp_sl_cache.get(symbol, {})

    entry_cache = cached.get("entry", entry_price)
    sl_cache = cached.get("sl", sl_price)
    tp_cache = cached.get("tp", tp_price)

    # 🔥 zapisujemy dane
    df.at[idx, "symbol"] = symbol
    df.at[idx, "side"] = "long" if str(side).upper() == "BUY" else "short"

    # ENTRY
    if entry_cache is None:
        df.at[idx, "entry"] = "none"
    else:
        df.at[idx, "entry"] = float(entry_cache)

    # SL
    if sl_cache is None:
        df.at[idx, "sl"] = "none"
    else:
        df.at[idx, "sl"] = float(sl_cache)

    # TP
    if tp_cache is None:
        df.at[idx, "tp"] = "none"
    else:
        df.at[idx, "tp"] = float(tp_cache)

    df.to_csv(csv_path, index=False)
    print(f"[CSV] Zapisano trade info dla {symbol} w {csv_path}")

# endregion
# region ================================ ALL ======================================

def append_ohlc_with_indicators(row, csv_path="ohlc_last.csv"):
    # =====================================================
    # 1️⃣ WCZYTAJ CSV
    # =====================================================
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        df = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close"])

    # =====================================================
    # 2️⃣ DODAJ NOWĄ ŚWIECĘ
    # =====================================================
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    new_idx = df.index[-1]

    # =====================================================
    # 3️⃣ UPEWNIJ SIĘ ŻE KOLUMNY ISTNIEJĄ
    # =====================================================
    for col in ["side", "entry", "sl", "tp", "symbol", "fractal"]:
        if col not in df.columns:
            df[col] = "none"

    # =====================================================
    # 4️⃣ MULTI-SYMBOL CARRY OVER
    # =====================================================
    current_symbol = df.at[new_idx, "symbol"]
    if current_symbol == "none" or pd.isna(current_symbol):
        current_symbol = None

    try:
        position_open = is_position_open(current_symbol)
    except:
        position_open = False

    if position_open and len(df) > 1:
        prev = df.iloc[-2]
        for col in ["side", "entry", "sl", "tp", "symbol"]:
            df.at[new_idx, col] = prev[col]
    else:
        for col in ["side", "entry", "sl", "tp", "symbol"]:
            df.at[new_idx, col] = "none"

    # =====================================================
    # 5️⃣ FILTR ŚWIECY
    # =====================================================
    try:
        o, h, l, c = map(float, (row["open"], row["high"], row["low"], row["close"]))
        if h < l or (h - l) > 400 or any(v < 50000 for v in (o, h, l, c)):
            raise ValueError
    except:
        df = df.iloc[:-1]
        df.to_csv(csv_path, index=False)
        return

    # =====================================================
    # 6️⃣ TIMESTAMP JAKO KOLUMNA (ZAWSZE)
    # =====================================================
    if "timestamp" not in df.columns:
        print("[🛑 CSV BLOCK] Brak timestamp — abort save")
        return

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        format="%Y-%m-%d %H:%M:%S%z",
        utc=True,
        errors="coerce"
    )
    df = df.dropna(subset=["timestamp"])
    df = df.sort_values("timestamp").tail(500)

    # =====================================================
    # 7️⃣ KONWERSJE
    # =====================================================
    for col in ["open", "high", "low", "close"]:
        df[col] = df[col].astype(float)

    df = df.loc[:, ~df.columns.duplicated()]

    # =====================================================
    # 8️⃣ OBLICZENIA (index TYLKO TYMCZASOWO)
    # =====================================================
    df_calc = df.copy()
    df_calc["timestamp"] = df_calc["timestamp"].dt.tz_convert("Europe/Warsaw")
    df_calc.set_index("timestamp", inplace=True)

    df_calc["DEMA_20"] = calculate_dema(df_calc["close"], 20)
    df_calc["DEMA_50"] = calculate_dema(df_calc["close"], 50)
    df_calc["DEMA_100"] = calculate_dema(df_calc["close"], 100)

    # =====================================================
    # 9️⃣ WRÓĆ DO CSV FORMATU (timestamp = kolumna)
    # =====================================================
    df_calc = df_calc.reset_index()

    # =====================================================
    # 🔟 OSTATECZNY ZAPIS (BEZPIECZNY)
    # =====================================================
    if len(df_calc) < 10:
        print("[🛑 CSV BLOCK] Za mało świec — nie zapisuję")
        return

    df_calc.to_csv(csv_path, index=False)
    ensure_trade_columns(csv_path)

# endregion
# region ================================ ALL 2 ====================================

def refresh_df_and_indicators(symbol, interval="1m", limit=500):
    try:
        klines = safe_binance_call(client.futures_klines, symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close',
            'volume', 'close_time', 'quote_asset_volume',
            'number_of_trades', 'taker_buy_base_volume',
            'taker_buy_quote_volume', 'ignore'
        ])
        if 'index' in df.columns:
            df = df.drop(columns=['index'])

        # ⏱ timestamp → DatetimeIndex
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
            df = df.dropna(subset=['timestamp'])
            df['timestamp'] = df['timestamp'].dt.tz_convert('Europe/Warsaw')
            df.set_index('timestamp', inplace=True)
        else:
            raise ValueError("CSV MUSI zawierać kolumnę 'timestamp'")


        df = df.loc[:, ~df.columns.duplicated()]
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df['timestamp'] = df['timestamp'].dt.tz_convert('Europe/Warsaw')
        df.set_index('timestamp', inplace=True)
        df = df.copy()
        df = df[~df.index.duplicated(keep='last')]
        df = df.tail(500)

        # Konwersje
        df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(float)

        if 'index' in df.columns:
            df = df.drop(columns=['index'])

        # ⏱ timestamp → DatetimeIndex
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
            df = df.dropna(subset=['timestamp'])
            df['timestamp'] = df['timestamp'].dt.tz_convert('Europe/Warsaw')
            df.set_index('timestamp', inplace=True)
        else:
            raise ValueError("CSV MUSI zawierać kolumnę 'timestamp'")


        df = df.loc[:, ~df.columns.duplicated()]

        # Dodaj DEMA
        df['DEMA_short'] = calculate_dema(df['close'], 20)
        df['DEMA_medium'] = calculate_dema(df['close'], 50)
        df['DEMA_long'] = calculate_dema(df['close'], 100)

        return df

    except Exception as e:
        print(f"[❌ BŁĄD] Nie udało się pobrać i przeliczyć df dla {symbol}: {e}")
        return None

# endregion
# region ================================ ALL 3 ====================================

def get_futures_klines(symbol, interval="1m", limit=500):
    try:
        klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        if 'index' in df.columns:
            df = df.drop(columns=['index'])

        # ⏱ timestamp → DatetimeIndex
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
            df = df.dropna(subset=['timestamp'])
            df['timestamp'] = df['timestamp'].dt.tz_convert('Europe/Warsaw')
            df.set_index('timestamp', inplace=True)
        else:
            raise ValueError("CSV MUSI zawierać kolumnę 'timestamp'")

        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df['timestamp'] = df['timestamp'].dt.tz_convert('Europe/Warsaw')
        df.set_index('timestamp', inplace=True)
        df = df.copy()
        df = df[~df.index.duplicated(keep='last')]
        df = df.tail(500)

        df.index = df.index
        df = df.loc[:, ~df.columns.duplicated()]

        for col in ['open', 'high', 'low', 'close']:
            df[col] = df[col].astype(float)

        if 'index' in df.columns:
            df = df.drop(columns=['index'])

        # ⏱ timestamp → DatetimeIndex
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
            df = df.dropna(subset=['timestamp'])
            df['timestamp'] = df['timestamp'].dt.tz_convert('Europe/Warsaw')
            df.set_index('timestamp', inplace=True)
        else:
            raise ValueError("CSV MUSI zawierać kolumnę 'timestamp'")


        df = df.loc[:, ~df.columns.duplicated()]
        return df
    except Exception as e:
        print(f"[⛔ BŁĄD API Binance] {symbol}: {e}")
        return None
    
# endregion
# endregion
# endregion
# region ======================================================= NOWA ŚWIECA TV =====================================================
# region ========================================= 1 ZLECENIE ================================================

_tv_lock = threading.Lock()
_tv_thread = None
_tv_waiters = []

def wait_for_closed_candle_tv_safe(symbol=None, last_checked_candle=None):
    """
    Bezpieczna wersja: nie pozwala odpalić kilku OCR równolegle.
    Wszystkie wywołania dostają ten sam wynik.
    """
    fut = Future()
    with _tv_lock:
        _tv_waiters.append(fut)
        global _tv_thread
        if _tv_thread is None or not _tv_thread.is_alive():
            _tv_thread = threading.Thread(
                target=_tv_worker, args=(symbol, last_checked_candle), daemon=True
            )
            _tv_thread.start()
    return fut.result()  # blokuje aż worker zwróci świecę

# endregion
# region =========================================== LOADER ==================================================

def _tv_worker(symbol, last_checked_candle):
    global _tv_last_checked_candle

    try:
        # 🔒 synchronizacja z globalem
        if last_checked_candle is not None:
            last_checked_candle = sanitize_last_checked_candle(last_checked_candle)

            if last_checked_candle is None:
                return  # albo continue, zależnie od kontekstu

            if _tv_last_checked_candle is None:
                _tv_last_checked_candle = last_checked_candle
            else:
                _tv_last_checked_candle = max(
                    sanitize_last_checked_candle(_tv_last_checked_candle),
                    last_checked_candle
                )

        result = _real_wait_for_closed_candle_tv(
            symbol,
            _tv_last_checked_candle
        )

        _tv_last_checked_candle = result

        with _tv_lock:
            for fut in _tv_waiters:
                if not fut.done():
                    fut.set_result(result)
            _tv_waiters.clear()

    except Exception as e:
        with _tv_lock:
            for fut in _tv_waiters:
                if not fut.done():
                    fut.set_exception(e)
            _tv_waiters.clear()

# endregion
# region ========================================= ODCZYTANIE ================================================

def read_ohlc_from_file(image_path="nowss_ohlc.png", csv_path="ohlc_last.csv"):
    if not os.path.exists(image_path):
        print(f"[⚠️] Brak pliku {image_path} – nic nie zapisuję.")
        return None

    img = Image.open(image_path)
    custom_config = r'--psm 6 -c tessedit_char_whitelist=OHLCE0123456789.,€'
    text = pytesseract.image_to_string(img, config=custom_config)
    text = text.replace(",", ".")
    text = fix_missing_letters(text)
    text = text.replace("C€", "C").replace("C €", "C")

    values = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # 🔹 Napraw typowe błędy OCR
        if line and line[0] == "0":
            line = "O" + line[1:]
        line = re.sub(r'([OHLC])\1+', r'\1', line)   # usuń LL, CC
        line = re.sub(r'([OHLC])\.', r'\g<1>0.', line)  # ✅ napraw C.107 → C0.107

        # 🔹 Użyj parsera
        o, h, l, c = parse_ohlc_smart(line)

        if o is not None:
            o = fix_leading_3_to_9(o)
            values["O"] = fix_misplaced_dot(fix_number(o))

        if h is not None:
            h = fix_leading_3_to_9(h)
            values["H"] = fix_misplaced_dot(fix_number(h))

        if l is not None:
            l = fix_leading_3_to_9(l)
            values["L"] = fix_misplaced_dot(fix_number(l))

        if c is not None:
            c = fix_leading_3_to_9(c)
            values["C"] = fix_misplaced_dot(fix_number(c))

    # 🔥 FILTRY — kontrola poprawności danych
    if len(values) == 4:
        try:
            floats = [float(v) for v in values.values()]
        except Exception as e:
            print(f"[⚠️] Błąd przy konwersji wartości na float: {e} — {values}")
            return None

        # 1️⃣ Pomijanie świec, jeśli którakolwiek wartość < 50k
        if any(v < 50000 for v in floats):
            if os.path.exists(image_path):
                os.remove(image_path)
            return None

        # 2️⃣ Pomijanie, jeśli różnica między OHLC > 2000
        diff = max(floats) - min(floats)
        if diff > 400:
            if os.path.exists(image_path):
                os.remove(image_path)
            return None

        # 3️⃣ Podejrzane wartości '0.xxx'
        suspicious = False
        digits_before = [len(str(v).split('.')[0]) for v in values.values() if '.' in str(v)]

        if digits_before:
            avg_digits = sum(digits_before) / len(digits_before)
            for k, v in values.items():
                s = str(v)
                if s.startswith("0.") and len(s.split(".")[1]) < avg_digits - 1:
                    suspicious = True
                    break

        if suspicious:
            if os.path.exists(image_path):
                os.remove(image_path)
            return None

        # 📅 Zapis poprawnej świecy
        ts = datetime.now(WARSAW) - timedelta(minutes=1)
        ts = ts.replace(second=0, microsecond=0)
        row = {
            "open": fix_misplaced_dot(values["O"]),
            "high": fix_misplaced_dot(values["H"]),
            "low": fix_misplaced_dot(values["L"]),
            "close": fix_misplaced_dot(values["C"]),
            "timestamp": ts,
        }

        append_ohlc_with_indicators(row, csv_path)
        recalc_fractals_in_csv(csv_path)
        ensure_trade_columns(csv_path)

        return row

    else:
        if os.path.exists(image_path):
            os.remove(image_path)

        return None

# endregion
# region ============================================ TIME ===================================================

def sanitize_last_checked_candle(ts):
    if ts is None:
        return None

    # pandas.Timestamp
    if isinstance(ts, pd.Timestamp):
        if ts.tzinfo is None:
            return ts.tz_localize(WARSAW)
        return ts.tz_convert(WARSAW)

    # datetime
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=WARSAW)
        return ts.astimezone(WARSAW)

    # string
    if isinstance(ts, str):
        try:
            t = pd.to_datetime(ts)
            if t.tzinfo is None:
                return t.tz_localize(WARSAW)
            return t.tz_convert(WARSAW)
        except Exception:
            return None

    return None

# endregion
# region =========================================== LOADER ==================================================

def _real_wait_for_closed_candle_tv(symbol, last_checked_candle):
    global kys, _tv_last_seen_candle

    last_checked_candle = sanitize_last_checked_candle(last_checked_candle)

    # 🔒 jeśli caller podał None, użyj globalnego
    if last_checked_candle is None:
        last_checked_candle = _tv_last_seen_candle

    if not kys:
        time.sleep(5)
        return _real_wait_for_closed_candle_tv(symbol, last_checked_candle)

    while True:
        now = datetime.now(WARSAW)

        if now.second == 5:

            # --- OCR ---
            pyautogui.moveTo(CLICK_POINT[0], CLICK_POINT[1])
            time.sleep(0.2)

            left, top, right, bottom = OHLC_BOX
            screenshot = pyautogui.screenshot(
                region=(left, top, right-left, bottom-top)
            )
            screenshot.convert("RGB").save("nowss_ohlc.png")

            row = read_ohlc_from_file("nowss_ohlc.png", SAVE_PATH)
            if not row:
                time.sleep(1)
                continue

            candle_time = sanitize_last_checked_candle(row.get("timestamp"))
            if candle_time is None:
                continue

            # 🔑 KLUCZOWA LOGIKA
            if last_checked_candle is not None and candle_time <= last_checked_candle:
                time.sleep(1)
                continue


            # 🔥 zapamiętaj globalnie
            _tv_last_seen_candle = candle_time

            return candle_time

        time.sleep(0.5)

# endregion
# endregion
# region ======================================================= OTWARTA POZYCJA ====================================================
# region ========================================== LINIA ====================================================

def detect_longest_horizontal_line(mask, image, color_name=None, y_threshold=1000):
    edges = cv2.Canny(mask, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)

    max_length = 400
    longest_line = None

    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

            # tylko linie prawie poziome i poniżej y_threshold
            if abs(y2 - y1) < 5 and y1 < y_threshold and y2 < y_threshold:
                if length > max_length:
                    max_length = length
                    longest_line = (x1, y1, x2, y2)

    if longest_line is not None:
        x1, y1, x2, y2 = longest_line
        # opcjonalne rysowanie
        if color_name == "blue":
            cv2.line(image, (x1, y1), (x2, y2), (255, 0, 0), 2)
        elif color_name == "red":
            cv2.line(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
        else:
            cv2.line(image, (x1, y1), (x2, y2), (0, 255, 0), 2)  # domyślnie zielona

        return x1, y1, x2, y2
    else:
        return None

# endregion
# region ========================================== OPEN POS =================================================

def is_position_open(symbol):
    if str(x).lower() == "binance":
        print("binance is position")
        positions = safe_binance_call(client.futures_position_information)
        if not positions:
            return False
        for pos in positions:
            if pos['symbol'] == symbol:
                amt = float(pos['positionAmt'])
                if abs(amt) > 0.0001:
                    return True
        return False
    else:
        do_action(0, 0, 1920, 1080, save_path="twoje_zdjecie.jpg")

        time.sleep(2)

        image = cv2.imread("twoje_zdjecie.jpg")

        if image is None or image.size == 0:
            print("[❌] Brak obrazu — image jest puste, pomijam cvtColor")
            return False

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Zakres kolorów dla niebieskiego (HSV)
        lower_blue = np.array([100, 150, 50])
        upper_blue = np.array([140, 255, 255])
        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

        # Zakres kolorów dla czerwonego (HSV)
        lower_red1 = np.array([0, 150, 50])
        upper_red1 = np.array([10, 255, 255])
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)

        lower_red2 = np.array([160, 150, 50])
        upper_red2 = np.array([180, 255, 255])
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)

        mask_red = cv2.bitwise_or(mask_red1, mask_red2)
        mask_all = cv2.bitwise_or(mask_blue, mask_red)

        detect_longest_horizontal_line(mask_all, image)
        wynik1 = detect_longest_horizontal_line(mask_all, image)
        if wynik1 is not None:
            return True
        else:
            return False

#endregion
#endregion
# region ======================================================= OGÓŁY BINANCE ======================================================
# region ========================================== BŁĘDY ====================================================
# region ===================================== CZAS MS ========================================


def get_time_offset():
    try:
        server_time = client.get_server_time()["serverTime"]
        local_time = int(time.time() * 1000)
        offset = server_time - local_time
        print(f"[⏱️ SYNC] Offset czasowy z Binance: {offset} ms")
        return offset
    except Exception as e:
        print(f"[❌ TIME SYNC FAIL] Nie udało się pobrać czasu Binance: {e}")
        return 0

# endregion
# region ====================================== -1111 =========================================

def get_df_for_chart(symbol, interval="1m", limit=500):
    df = refresh_df_and_indicators(symbol, interval=interval, limit=limit)
    if df is None or df.empty:
        return None

    # 🔒 UJEDNOLICENIE TIMESTAMP
    df = ensure_datetime_index(df)

    # pomocnicza kolumna time (do fractali / TV)
    df["time"] = df.index

    return df

# endregion
# endregion
# region ========================================== CLOSE ====================================================
# endregion
# region ========================================== OPEN =====================================================
# endregion
# endregion
# region ======================================================= ANALIZA RYNKU ======================================================
# region ========================================== AI =======================================================

def generate_clean_chart(symbol):
        print("binance")
        # === Normalny Binance flow ===
        klines = client.futures_klines(symbol=symbol, interval='1m', limit=70)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'trades',
            'taker_base_vol', 'taker_quote_vol', 'ignore'
        ])

        if 'index' in df.columns:
            df = df.drop(columns=['index'])

        # ⏱ timestamp → DatetimeIndex
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
            df = df.dropna(subset=['timestamp'])
            df['timestamp'] = df['timestamp'].dt.tz_convert('Europe/Warsaw')
            df.set_index('timestamp', inplace=True)
        else:
            raise ValueError("CSV MUSI zawierać kolumnę 'timestamp'")


        df = df.loc[:, ~df.columns.duplicated()]

        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df = df.copy()
        df = df[~df.index.duplicated(keep='last')]
        df = df.astype(float)

        # 3. Nazwa pliku tymczasowego
        file_path = f"chart_{symbol}.png"

        # 4. Rysowanie czystego wykresu (świece)
        mpf.plot(
            df,
            type='candle',
            style='charles',
            savefig=file_path
        )

        return file_path

# endregion
# region ========================================== NAGŁY WZROST/SPADEK ======================================

def should_skip_due_to_distance(symbol, current_price, fractal_time, df, position_type):
    if x == "tv":
        return False
    else:
        thresholds = {
            "BTCUSDT": 200.0,
            "ETHUSDT": 6.0,
            "SOLUSDT": 1.2,
        }

        df = df[~df.index.duplicated(keep='last')]

        idx = df.index.get_indexer([fractal_time], method="nearest")[0]

        if idx == -1:
            print(f"[BŁĄD] Nie znaleziono świecy z fraktalem dla {symbol}")
            return False

        fractal_idx = idx
        fractal_row = df.iloc[fractal_idx]

        threshold = thresholds.get(symbol, 200.0)
        recent_df = df.iloc[fractal_idx:]  # od fraktala do teraz

        if position_type == "long":
            base_price = fractal_row["low"]
            max_price = recent_df["high"].max()
            diff = max_price - base_price
            base_price_next = fractal_row["high"]
            fractal_knot = base_price_next - base_price
        else:
            base_price = fractal_row["high"]
            min_price = recent_df["low"].min()
            diff = base_price - min_price
            base_price_next = fractal_row["low"]
            fractal_knot = base_price - base_price_next

        if diff > threshold:
            print(f"[RESET] {symbol} — od fraktala ({base_price}) cena poszła o {round(diff, 2)} → za dużo ({threshold})")
            return True
        if fractal_knot > threshold:
            print(f"[RESET] {symbol}  różnica między low a high {fractal_knot} → za dużo ({threshold})")
            return True


        if fractal_time not in df.index:
            print(f"[DEBUG SPRAWDZANY DF] df.index[0] = {df.index[0]} → df.index[-1] = {df.index[-1]}")
            print(f"[DEBUG SPRAWDZANY DF] Czy fractal_time ∈ df.index? {fractal_time in df.index}")
            return False

        return False

# endregion
# region ========================================== ODLEGŁOŚCI DEMA ==========================================

def had_recent_impulse(df, symbol, direction="up", lookback=3):
    minimal_dema_distance = {
        "BTCUSDT": 15.0,
        "ETHUSDT": 0.3,
        "SOLUSDT": 0.12,
    }

    min_distance = minimal_dema_distance.get(symbol, 1.0)
    df = df.tail(lookback)

    for i, row in df.iterrows():
        d20 = row['DEMA_short']
        d50 = row['DEMA_medium']
        d100 = row['DEMA_long']

        # ————— Zbyt małe odległości
        if abs(d20 - d50) < min_distance or abs(d50 - d100) < min_distance:
            if not warned_dema_distance[symbol][direction]:
                print(f"[POMINIĘTE] Zbyt małe odległości DEMA ({symbol}) — {round(d20,2)}, {round(d50,2)}, {round(d100,2)}")
                warned_dema_distance[symbol][direction] = True
            return False
        else:
            warned_dema_distance[symbol][direction] = False

        # ————— Zły układ
        if direction == "up" and not (d20 > d50 > d100):
            if not warned_dema_order[symbol][direction]:
                print(f"[POMINIĘTE] Zły układ DEMA dla LONG ({symbol}) — {round(d20,2)}, {round(d50,2)}, {round(d100,2)}")
                warned_dema_order[symbol][direction] = True
            return False
        elif direction == "down" and not (d20 < d50 < d100):
            if not warned_dema_order[symbol][direction]:
                print(f"[POMINIĘTE] Zły układ DEMA dla SHORT ({symbol}) — {round(d20,2)}, {round(d50,2)}, {round(d100,2)}")
                warned_dema_order[symbol][direction] = True
            return False
        else:
            warned_dema_order[symbol][direction] = False

    print(f"[✅ IMPULS] Układ DEMA poprawny dla {symbol} ({direction}) na ostatnich {lookback} świecach")
    return True

# endregion
# endregion
# region ======================================================= LICZENIE ===========================================================
# region ========================================== STEP Z XUP/XDOWN =========================================

def round_to_step(value, step=None):
    try:
        # 🔹 Jeśli step nie jest podany — spróbuj obliczyć z obrazów (xup/xdown)
        if step is None:
            try:
                xup = read_number_from_image("gorny.png")
                xdown = read_number_from_image("dolny.png")
                if xup is not None and xdown is not None:
                    step = (xup - xdown) / 828.0
                    print(f"[ℹ️] Obliczono step z OCR: {step}")
                else:
                    print("[⚠️] Nie udało się odczytać xup/xdown — używam fallback=1.0")
                    step = 1.0
            except Exception as e:
                print(f"[⚠️] Błąd podczas obliczania step z OCR: {e}")
                step = 1.0

        # 🔹 Sprawdź, czy step istnieje i jest poprawny
        if step is None or step <= 0:
            print(f"[round_to_step ERROR] step niepoprawny ({step}) dla value={value}")
            return round(float(value), 2)

        # 🔹 Konwersja do Decimal (precyzyjna arytmetyka)
        step = Decimal(str(step))
        value = Decimal(str(value))

        # 🔹 Zaokrąglenie do najbliższego niższego kroku
        rounded = (value / step).quantize(0, ROUND_FLOOR) * step
        return float(rounded)

    except InvalidOperation:
        print(f"[round_to_step ERROR] Niepoprawne dane: value={value}, step={step}")
        return float(value)

    except Exception as e:
        print(f"[round_to_step ERROR] value={value}, step={step} | {type(e).__name__}: {e}")
        return float(value)

# endregion
# region ========================================== PERCISION ================================================

def get_symbol_precision(symbol):
    # Sztywne ustawienie dla KAŻDEGO symbolu
    step_size = 0.01   # minimalny krok wielkości (ilość)
    tick_size = 0.01   # minimalny krok ceny
    return step_size, tick_size

# endregion
# region ========================================== TICK SIZE ================================================

def get_symbol_tick_size(symbol):
    try:
        info = client.futures_exchange_info()
        for s in info.get("symbols", []):
            if s.get("symbol") == symbol:
                for f in s.get("filters", []):
                    if f.get("filterType") in ("PRICE_FILTER", "MARKET_LOT_SIZE", "PERCENT_PRICE"):
                        # PRICE_FILTER ma 'tickSize'
                        if "tickSize" in f:
                            try:
                                return float(f["tickSize"])
                            except Exception:
                                return None
                # jeśli nie znaleziono PRICE_FILTER, spróbuj domyślnie
                print(f"[⚠️] Nie znaleziono PRICE_FILTER dla {symbol} w exchange_info.")
                return None
        print(f"[⚠️] Nie znaleziono symbolu {symbol} w exchange_info.")
        return None
    except Exception as e:
        print(f"[⚠️] get_symbol_tick_size ERROR: {e}")
        return None

# endregion
# region ========================================== QTY ======================================================

MAX_RISK_USDT = 30  # maksymalna strata (stała)

def calculate_dynamic_qty(entry_price, sl_price, symbol, leverage=20, safety_factor=0.95):
    if x == "tv":
        qty = 0.5
        return qty
    if x == "binance":

        try:
            diff = abs(entry_price - sl_price)
            if diff == 0:
                print("[❌] Odległość SL = 0, nie można obliczyć ilości.")
                return 0

            # Pierwotna ilość na podstawie ryzyka
            qty = MAX_RISK_USDT / diff

            # --- SZTYWNA WARTOŚĆ ZAMIAST API BINANCE ---
            available_usdt = 101207.00    # <-- tutaj wprowadzasz własną wartość
            usable_usdt = available_usdt * safety_factor

            max_position_value = usable_usdt * leverage
            max_qty = max_position_value / entry_price
            print (f" entry {entry_price}  sl {sl_price}")

            if qty > max_qty:
                print(f"[⚠️] Obliczona ilość {qty:.3f} przekracza max_qty {max_qty:.3f} → zmniejszam do połowy.")
                qty = round(max_qty / 2, 6)

            return qty
        except Exception as e:
            print(f"[❌] Błąd w calculate_dynamic_qty: {e}")
            return 0

# endregion
# region ========================================== WZOR DEMA ================================================

def calculate_dema(series, period):
    ema = series.ewm(span=period, adjust=False).mean()
    dema = 2 * ema - ema.ewm(span=period, adjust=False).mean()
    return dema

# endregion
# region ========================================== DEMA =====================================================

# === WSKAŹNIKI ===
def apply_dema_indicators(df):
    if df is None or df.empty:
        return None

    if "close" not in df.columns:
        print("[DEMA ⚠️] Brak kolumny 'close'")
        return None

    df = df.copy()
    df = df[~df.index.duplicated(keep='last')]

    for period, label in [(20, "short"), (50, "medium"), (100, "long")]:
        ema1 = df["close"].ewm(span=period, adjust=False).mean()
        ema2 = ema1.ewm(span=period, adjust=False).mean()
        df[f"DEMA_{label}"] = 2 * ema1 - ema2

    return df

# endregion
# region ========================================== ALL FRACTAL ==============================================

n = 2

# === Szukanie fractala up ===
def detect_fractals(df):
    df = df.copy()
    df = df[~df.index.duplicated(keep='last')]
    df = df.tail(500)
    fractal_list = []  # zbierzemy (i, typ)

    for i in range(2, len(df) - 2):
        lows = df['low'].iloc[i - 2:i + 3].values
        highs = df['high'].iloc[i - 2:i + 3].values
        center_low = df['low'].iloc[i]
        center_high = df['high'].iloc[i]
        ts = df.index[i]

        df.at[df.index[i], 'upFractal'] = False
        df.at[df.index[i], 'downFractal'] = False

        if center_low == min(lows) and list(lows).count(center_low) == 1:
            df.at[df.index[i], 'upFractal'] = True
            fractal_list.append((i, "upFractal"))

        if center_high == max(highs) and list(highs).count(center_high) == 1:
            df.at[df.index[i], 'downFractal'] = True
            fractal_list.append((i, "downFractal"))

    return df, fractal_list


# endregion
# region ========================================== NEW FRACTAL ==============================================

def fractal(symbol, df=None):
    df = get_df_for_chart(symbol, limit=500)

    if df is None or df.empty:
        return None, None

    required_cols = ["open", "high", "low", "close"]
    for col in required_cols:
        if col not in df.columns:
            print(f"[FRACTAL ERROR] Brakuje kolumny: {col}")
            return None, None

    # DF MA DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        print("[FRACTAL ERROR] DF nie ma DatetimeIndex")
        return None, None

    df, fractal_list = detect_fractals(df)
    df = df.tail(500)

    up_list   = [i for i, t in fractal_list if t == "upFractal"]
    down_list = [i for i, t in fractal_list if t == "downFractal"]

    last_index = len(df) - 3
    if last_index < 0:
        return None, None

    if last_index in up_list:
        return "upFractal", df.index[last_index]

    if last_index in down_list:
        return "downFractal", df.index[last_index]

    return None, None

# endregion
# endregion
# region ======================================================= LICZENIE SL/TP =====================================================
# region ========================================== LOCAL SL =================================================


def start_logical_sl_monitor(symbol, entry_price, side='BUY', sl_price=None, tp_price=None, sl_logic_lookback=1):
    def monitor():
        try:
            print(f"[🧠 LOGICZNY SL] Start monitora SL dla {symbol}")

            df = get_futures_klines(symbol, interval='1m', limit=3)
            df = apply_dema_indicators(df)
            df = df.dropna()

            last_checked = df.index[-1]
            wait_for_closed_candle(symbol, last_checked)

            while is_position_open(symbol):
                df = get_futures_klines(symbol, interval='1m', limit=5)
                df = apply_dema_indicators(df)
                df = df.dropna()
                df.index = pd.to_datetime(df.index)

                if len(df) < 3:
                    time.sleep(30)
                    continue

                # TV or normal mode
                if x == "tv":
                    last = df.iloc[-1]
                    prev = df.iloc[-2]
                else:
                    last = df.iloc[-2]
                    prev = df.iloc[-3]

                # 🔥 DEMA LOGICAL STOP LOSS
                if side == 'BUY':
                    sl_triggered = (
                        prev['close'] < prev['DEMA_long'] and
                        last['close'] < last['DEMA_long']
                    )
                else:
                    sl_triggered = (
                        prev['close'] > prev['DEMA_long'] and
                        last['close'] > last['DEMA_long']
                    )

                if not sl_triggered:
                    print(f"czekam na sl dla {symbol}")
                else:
                    print(f"[⛔ LOGICZNY SL] Warunki spełnione na {symbol} — zamykam pozycję!")
                    force_close_position_until_success(symbol)
                    clear_trade_in_csv()
                    return

                # 🔥 OHLC do porównywań SL / TP
                o = last["open"]
                h = last["high"]
                l = last["low"]
                c = last["close"]

                # 🔥 OHLC SL/TP logic — według Twoich zasad
                if sl_price is not None and tp_price is not None:

                    if side == "BUY":
                        if sl_price > o or sl_price > h or sl_price > l or sl_price > c:
                            print("[📉 SL LOGIC BUY TRIGGERED]")
                            clear_trade_in_csv()
                        if tp_price < o or tp_price < h or tp_price < l or tp_price < c:
                            print("[📈 TP LOGIC BUY TRIGGERED]")
                            clear_trade_in_csv()

                    elif side == "SELL":
                        if sl_price < o or sl_price < h or sl_price < l or sl_price < c:
                            print("[📉 SL LOGIC SELL TRIGGERED]")
                            clear_trade_in_csv()
                        if tp_price > o or tp_price > h or tp_price > l or tp_price > c:
                            print("[📈 TP LOGIC SELL TRIGGERED]")
                            clear_trade_in_csv()

                time.sleep(30)

        except Exception as e:
            print(f"[❌ BŁĄD LOGICZNEGO SL] {symbol}: {e}")

    threading.Thread(target=monitor, daemon=True).start()

# endregion
# region ========================================== SL/TP TV =================================================

def sl_tp(df, side="BUY", sl_price=None, entry_price=None, tp_multiplier=1.5, tick_size=0.01):
    try:
        last = df.iloc[-1]
        entry_price = read_number_from_image("entry.png")

        # jeśli nie przekazano sl_price, pobierz z df
        if sl_price is None:
            if "sl_price" in df.columns and not pd.isna(last["sl_price"]):
                sl_price = float(last["sl_price"])
                print(f"[ℹ️] sl_price pobrano z df: {sl_price}")
            else:
                return None

        # Wyliczenie TP
        if side.upper() == "BUY":
            tp_price = entry_price + tp_multiplier * abs(entry_price - sl_price)
        elif side.upper() == "SELL":
            tp_price = entry_price - tp_multiplier * abs(entry_price - sl_price)
        else:
            print(f"[⚠️] Nieznany side: {side}")
            return None

        # Zaokrąglenia wg tick_size
        entry_price = round_to_step(entry_price, tick_size)
        sl_price = round_to_step(sl_price, tick_size)
        tp_price = round_to_step(tp_price, tick_size)


        result = {
            "entry": entry_price,
            "sl": sl_price,
            "tp": tp_price,
            "side": side,   # 🔹 dopisujemy side
        }
        print(f"[📊 SL/TP] side={side} | entry={entry_price} | sl={sl_price} | tp={tp_price}")
        print("dało result")
        return result

    except Exception as e:
        print(f"[❌ BŁĄD sl_tp] {e}")
        return None

# endregion
# region ========================================== ZAMYKANIE PRZY ZJEBANYM SL/TP ============================

def force_close_position_until_success(symbol, delay=2):
    print(f"[⚠️ AWARYJNE ZAMYKANIE] Start dla {symbol}")
    attempt_count = 0

    while attempt_count < 5:
        try:
            positions = retry_on_time_error(client.futures_position_information, symbol=symbol)
            pozycja_znaleziona = False

            for pos in positions:
                if pos['symbol'].upper() != symbol.upper():
                    continue
                amt = float(pos['positionAmt'])
                if abs(amt) > 0.0001:
                    pozycja_znaleziona = True
                    side = "SELL" if amt > 0 else "BUY"
                    qty = abs(amt)

                    print(f"✅ Pozycja OTWARTA → próbuję zamknąć ({side} {qty})")
                    retry_on_time_error(
                        client.futures_create_order,
                        symbol=symbol,
                        side=side,
                        type="MARKET",
                        quantity=qty,
                        reduceOnly=True
                    )
                    print(f"[🛑 ZAMKNIĘTO] Pozycja {symbol} została zamknięta awaryjnie.")
                    return  # zakończ po zamknięciu

            if not pozycja_znaleziona:
                print(f"❌ Pozycja ZAMKNIĘTA lub brak danych — próba {attempt_count+1}/5")
                attempt_count += 1
                time.sleep(delay)
                continue

        except Exception as e:
            print(f"[❌ BŁĄD W force_close_loop] {e}")
            attempt_count += 1
            time.sleep(delay)

    print(f"[❌ PRZERWANO] Przekroczono limit prób dla {symbol}")

# endregion
# region ========================================== FIX ======================================================
# region ====================================== PT1 =========================================

def place_futures_order_with_tp_sl(symbol, side, quantity, entry_price, sl_price, waiting_20, waiting_50, waiting_20_down, waiting_50_down, df, precision, tp_multiplier, opposite):
    try:
        if isinstance(sl_price, tuple):


            print(f"[⚠️] SL przekazane jako tuple: {sl_price} — biorę pierwszy element")
            sl_price = sl_price[0]
        if isinstance(entry_price, tuple):
            print(f"[⚠️] ENTRY przekazane jako tuple: {entry_price} — biorę pierwszy element")
            entry_price = entry_price[0]
        if isinstance(tick_size, tuple):
            print(f"[⚠️] tick_size przekazane jako tuple: {tick_size} — biorę drugi element")
            tick_size = tick_size[1]
        # === WALIDACJA PODSTAWOWA ===
        if sl_price is None or entry_price is None:
            print(f"[❌ BŁĄD LOGICZNY] Brak SL lub ENTRY — nie składam TP")
            return None, None

        if side == 'BUY':
            tp_price = entry_price + tp_multiplier * abs(entry_price - sl_price)
        else:  # side == 'SELL'
            tp_price = entry_price - tp_multiplier * abs(entry_price - sl_price)
        tp_price = round_to_step(tp_price, tick_size)
        print(f"[DEBUG] tp_price={tp_price}, tick_size={tick_size}, typy: {type(tp_price)}, {type(tick_size)}")
        print(f"[ZLECENIE DEBUG] {symbol} | side={side} | qty={quantity} | entry={entry_price} | SL={sl_price} | TP={tp_price}")

        start_logical_sl_monitor(
            symbol=symbol,
            entry_price=entry_price,
            side=side,
            sl_price=sl_price,
            tp_price=tp_price
        )
        # === MARKET ENTRY ===
        retry_on_time_error(
            client.futures_create_order,
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=quantity,
        )
        time.sleep(1)

        for _ in range(10):
            if retry_on_time_error(is_position_open, symbol):
                break
            print("[⏱️] Czekam aż pozycja się pojawi...")
            time.sleep(1)
        else:
            print("[❌] Pozycja się nie pojawiła — przerywam próbę ustawiania TP")
            return None, None

        # === TAKE PROFIT ===
        try:
            response = retry_on_time_error(
                client.futures_create_order,
                symbol=symbol,
                side=opposite,
                type="TAKE_PROFIT_MARKET",
                stopPrice=str(round(tp_price, 2)),
                closePosition=True,
                timeInForce="GTC"
            )
            print(f"[✅ TP ZLECONE] {tp_price} response = {response}")
            print(f"[DEBUG TP] entry: {entry_price}, sl: {sl_price}, tp_multiplier: {tp_multiplier}")
        except Exception as e:
            print(f"[❌ BŁĄD TP] {e}")

        # ❌ NIE USTAWIAMY SL NA BINANCE

        print(f"[📥 OTWARTA POZYCJA] {side} {symbol} | ENTRY: {entry_price} | SL(logiczny): {sl_price} | TP: {tp_price} ")
        threading.Thread(
            target=start_logical_sl_monitor,
            args=(symbol, entry_price, side, sl_price, tp_price),
            daemon=True
        ).start()
        df_before = df.iloc[-10:].copy()

        active_trades[symbol] = {
            "side": side,
            "entry_price": entry_price,
            "sl": sl_price,
            "tp": tp_price,
            "df_before": df_before,
        }

        tp_sl_cache[symbol] = {
            "tp": tp_price,
            "sl": sl_price,
            "side": side
        }

        attach_trade_to_latest_candle(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            sl_price=sl_price,
            tp_price=tp_price,
            csv_path=SAVE_PATH  # "ohlc_last.csv"
        )

        return tp_price, sl_price


    except Exception as e:
        print(f"[BŁĄD ZLECENIA] {symbol} | {side} | {e}")
        return None, None

# endregion
# region ====================================== PT2 =========================================

def verify_and_fix_tp_sl(symbol, side, tp_expected, sl_expected, tick_size=0.01, precision=2, max_attempts=3):
    print(f"[📡 SPRAWDZAM TP/SL] {symbol} — oczekiwane TP={tp_expected}, SL={sl_expected}")
    if isinstance(tp_expected, tuple):
        print(f"[⚠️] TP przekazane jako tuple: {tp_expected} — biorę pierwszy element")
        tp_expected = tp_expected[0]
    if isinstance(sl_expected, tuple):
        print(f"[⚠️] SL przekazane jako tuple: {sl_expected} — biorę pierwszy element")
        sl_expected = sl_expected[0]

    def round_price(p):
        if isinstance(p, tuple):
            print(f"[⚠️] round_price dostało tuple: {p} — biorę pierwszy element")
            p = p[0]
        return round_to_step(round(float(p), precision), tick_size)

    tp_expected = round_price(tp_expected)


    for attempt in range(1, max_attempts + 1):
        print(f"[🔁 PRÓBA {attempt}/{max_attempts}] Weryfikacja TP/SL dla {symbol}")

        try:
            orders = client.futures_get_open_orders(symbol=symbol)
            tp_order = next((o for o in orders if o["type"] == "TAKE_PROFIT_MARKET"), None)

            # === Sprawdź TP ===
            if tp_order:
                tp_current = round_price(tp_order["stopPrice"])
                if abs(tp_current - tp_expected) > tick_size:
                    print(f"[⚠️ BŁĘDNY TP] Binance ma {tp_current}, bot chciał {tp_expected} → USUWAM")
                    client.futures_cancel_order(symbol=symbol, orderId=tp_order["orderId"])
                    time.sleep(10)
                    retry_on_time_error(
                        client.futures_create_order,
                        symbol=symbol,
                        side='SELL' if side == 'BUY' else 'BUY',
                        type='TAKE_PROFIT_MARKET',
                        stopPrice=str(tp_expected),
                        closePosition=True,
                        timeInForce='GTC'
                    )
                    print(f"[✅ TP POPRAWIONY] {tp_expected}")
            elif not tp_order:
                print(f"[❗ BRAK TP] Brak zlecenia TP — ustawiam...")
                retry_on_time_error(
                    client.futures_create_order,
                    symbol=symbol,
                    side='SELL' if side == 'BUY' else 'BUY',
                    type='TAKE_PROFIT_MARKET',
                    stopPrice=str(tp_expected),
                    closePosition=True,
                    timeInForce='GTC'
                )
                print(f"[✅ TP USTAWIONY OD NOWA] {tp_expected}")


            # Weryfikacja po ustawieniu
            time.sleep(3)
            orders = client.futures_get_open_orders(symbol=symbol)
            tp_check = any(round_price(o["stopPrice"]) == tp_expected for o in orders if o["type"] == "TAKE_PROFIT_MARKET")

            if tp_check:
                print(f"[✅ SUKCES] TP i SL poprawnie ustawione dla {symbol}")
                return True

        except Exception as e:
            print(f"[❌ BŁĄD verify_and_fix_tp_sl] {symbol} → {e}")

    print(f"[❌ NIEUDANE PRÓBY] Nie udało się ustawić TP/SL dla {symbol} po {max_attempts} próbach")
    return False

# endregion
# endregion
# endregion
# region ======================================================= OGÓŁY TV ===========================================================
# region ========================================== ZAMKNIJ POS ==============================================

def close_position_tv():
    global cw
    print("close")
    do_action(0, 0, 1920, 1080, save_path="twoje_zdjecie.jpg")
    image = cv2.imread("twoje_zdjecie.jpg")

    if image is None:
        print("[❌ close_position_tv] Nie udało się wczytać screena")
        return

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower_blue = np.array([100, 150, 50])
    upper_blue = np.array([140, 255, 255])
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

    lower_red1 = np.array([0, 150, 50])
    upper_red1 = np.array([10, 255, 255])
    mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)

    lower_red2 = np.array([160, 150, 50])
    upper_red2 = np.array([180, 255, 255])
    mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)

    mask_red = cv2.bitwise_or(mask_red1, mask_red2)

    # ✅ zostaje mask_all
    mask_all = cv2.bitwise_or(mask_blue, mask_red)

    line = detect_longest_horizontal_line(mask_all, image)

    if not line:
        print("[⚠️ close_position_tv] Nie wykryto żadnej linii")
        return

    y_line = int(line[1])
    print(f"[ACTION] close_position_tv klikam y={y_line}")
    cw = False

    do_action(1390, y_line)
    cw = True

# endregion
# region ========================================== BINANCE NA TV ============================================
# endregion
# endregion
# region ======================================================= OTWIERANIE POZYCJI TV ==============================================
# region ========================================== DEF ======================================================

def place_futures_order_with_tp_sl_tv(symbol, quantity, entry_price, sl_price,
                                      waiting_20, waiting_50, waiting_20_down, waiting_50_down,
                                      df, precision, tp_multiplier,
                                      tick_size=None):
    global chuj, cw, mask_red, mask_blue, mask_all, position_active
    cw = False
    position_active = False

# region =============================== ZAKUP =======================================
    # ETAP 1 — KUPNO / SPRZEDAŻ (bez zmian logiki)
    try:
        if df is not None and not df.empty:
            last_close = float(df.iloc[-1]["close"])
            proposed_sl = float(sl_price)
            distance = abs(last_close - proposed_sl)

            print(f"[🧠] Odległość między CLOSE a SL = {distance:.2f} USD")

            if distance < 100:
                print(f"[⛔] SL ({proposed_sl}) jest zbyt blisko ostatniego CLOSE ({last_close}) — pomijam otwarcie pozycji!")
                return  # ❌ Zakończ funkcję bez kupowania/sprzedawania
        else:
            print("[⚠️] Brak danych DF do sprawdzenia odległości SL — pomijam weryfikację.")
    except Exception as e:
        print(f"[⚠️] Błąd przy sprawdzaniu odległości SL-close: {e}")

    do_action(165, 140)
    for _ in range(10):
        pyautogui.press("backspace")

    qty = calculate_dynamic_qty(entry_price, sl_price, symbol)
    pyautogui.write(str(qty), interval=0.05)

    if chuj == "buy":
        side = "BUY"
    elif chuj == "sell":
        side = "SELL"
    else:
        raise RuntimeError(f"[FATAL] Nieznany kierunek chuj={chuj}")

    if chuj == "buy":
        do_action(220, 135)
    elif chuj == "sell":
        do_action(120, 135)

    print("kupiono")
    check_pixel_once()
    time.sleep(5)
# endregion
# region =============================== CZY DZIAŁA =======================================
    do_action(0, 0, 1920, 1080, save_path="twoje_zdjecie.jpg")
    image = cv2.imread("twoje_zdjecie.jpg")
    if image is None:
        close_position_tv()
        print("[❌] Nie udało się wczytać obrazu twoje_zdjecie.jpg")
        return None, None

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([100, 150, 50])
    upper_blue = np.array([140, 255, 255])
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

    lower_red1 = np.array([0, 150, 50])
    upper_red1 = np.array([10, 255, 255])
    mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)

    lower_red2 = np.array([160, 150, 50])
    upper_red2 = np.array([180, 255, 255])
    mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)

    mask_red = cv2.bitwise_or(mask_red1, mask_red2)
    mask_all = cv2.bitwise_or(mask_blue, mask_red)

    if chuj == "buy":
        detect_longest_horizontal_line(mask_blue, image, "blue")
    if chuj == "sell":
        detect_longest_horizontal_line(mask_red, image, "red")

    y_line = detect_longest_horizontal_line(mask_all, image)

    # retry jak nie ma linii
    if not y_line:
        print("[⚠️] Nie udało się wykryć linii — czekam 10 sekund i próbuję jeszcze raz...")
        check_pixel_once()
        time.sleep(10)
        do_action(0, 0, 1920, 1080, save_path="twoje_zdjecie_retry.jpg")
        image = cv2.imread("twoje_zdjecie_retry.jpg")

        if image is None:
            close_position_tv()
            print("[❌] Brak obrazu po ponownej próbie — przerywam.")
            return None, None

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower_blue = np.array([100, 150, 50])
        upper_blue = np.array([140, 255, 255])
        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

        lower_red1 = np.array([0, 150, 50])
        upper_red1 = np.array([10, 255, 255])
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        lower_red2 = np.array([160, 150, 50])
        upper_red2 = np.array([180, 255, 255])
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)

        mask_red = cv2.bitwise_or(mask_red1, mask_red2)
        mask_all = cv2.bitwise_or(mask_blue, mask_red)

        y_line = detect_longest_horizontal_line(mask_all, image)
        if y_line:
            print("[✅] Linia wykryta w drugiej próbie.")
        else:
            close_position_tv()
            print("[❌] Nie udało się wykryć linii nawet po 10 sekundach.")
            return None, None
# endregion
# region =============================== SL/TP =======================================

    # jeśli dotarliśmy tutaj — linia istnieje
    y_line = y_line[1]
    print(f"y line {y_line}")

    do_action(1450, int(y_line))
    time.sleep(5)

    dwa_y = int(y_line - 16)
    jeden_y = int(y_line - 43)

    do_action(1453, int(jeden_y), 1515, int(dwa_y), save_path="entry.png")
    print("tu trzeba zmienic")

    entry_price_from_chart = read_number_from_image("entry.png")
    if entry_price_from_chart > 200_000:
        entry_price_from_chart = entry_price_from_chart // 10
    print(f"[ℹ️] Pobrano ENTRY z wykresu: {entry_price_from_chart}")

    # ETAP 2 — LICZENIE SL / TP
    result = sl_tp(
        df=df,
        side=side,
        sl_price=sl_price,
        entry_price=entry_price_from_chart,
        tp_multiplier=tp_multiplier,
        tick_size=tick_size
    )

    if not result:
        close_position_tv()
        print("[❌] sl_tp nie zwróciło wartości – przerywam.")
        return None, None

    try:
        entry_price_calc = float(result["entry"])
        sl_price_calc = float(result["sl"])
        tp_price_calc = float(result["tp"])
    except Exception as e:
        close_position_tv()
        print(f"[❌] Błąd podczas parsowania wyników sl_tp: {e} — result={result}")
        return None, None

    # TICK SIZE
    tick = tick_size
    if tick is None:
        tick = get_symbol_tick_size(symbol)
        if tick is None:
            print(f"[⚠️] Nie udało się pobrać tick_size dla {symbol} — używam fallback=1.0")
            tick = 1.0

    try:
        entry_price_final = round_to_step(entry_price_calc, tick)
    except Exception as e:
        close_position_tv()
        print(f"[round_to_step ERROR: entry] value={entry_price_calc}, tick={tick} -> {e}")
        entry_price_final = float(entry_price_calc)

    try:
        sl_price_final = round_to_step(sl_price_calc, tick)
    except Exception as e:
        close_position_tv()
        print(f"[round_to_step ERROR: sl] value={sl_price_calc}, tick={tick} -> {e}")
        sl_price_final = float(sl_price_calc)

    try:
        tp_price_final = round_to_step(tp_price_calc, tick)
    except Exception as e:
        close_position_tv()
        print(f"[round_to_step ERROR: tp] value={tp_price_calc}, tick={tick} -> {e}")
        tp_price_final = float(tp_price_calc)

    print(f"[📊 SL/TP] side={side} | entry={entry_price_final} | sl={sl_price_final} | tp={tp_price_final}")

# endregion
# region =============================== USTAW SL/TP =======================================

    cw = True

    # Zrzuty do OCR
    do_action(700, 160)
    do_action(1580, 150, 1640, 170, save_path="gorny.png")
    do_action(700, 820)
    do_action(1580, 810, 1640, 830, save_path="dolny.png")

    print("obliczenia")

    def safe_read_float(img_path):
        raw_val = read_number_from_image(img_path)
        if raw_val is None:
            close_position_tv()
            print(f"[⚠️] {img_path} zwrócił None")
            return None

        # extract_float_from_text usuwa'76930.3. dolny.png'
        val = extract_float_from_text(raw_val, default=None)
        if val is None:
            print(f"[⚠️] Nie udało się przekonwertować '{raw_val}' z {img_path} na float (po extract_float_from_text)")
        return val

    xup = protect_x_val(safe_read_float("gorny.png"))
    xdown = protect_x_val(safe_read_float("dolny.png"))

    print(f"xup = {xup}")
    print(f"xdown = {xdown}")

    if xup is None or xdown is None:
        close_position_tv()
        print("[⚠️] Nie udało się odczytać współrzędnych xup/xdown — zwracam same tp/sl.")
        return tp_price_final, sl_price_final

    # Obliczenia px
    try:
        px = (xup - xdown) / 665
    except ZeroDivisionError:
        close_position_tv()
        print("[❌] Dzielnie przez zero (665) — bardzo dziwne, ale przerywam.")
        return tp_price_final, sl_price_final

    if px == 0:
        close_position_tv()
        print("[❌] px wyszło 0 — coś jest nie tak z xup/xdown, przerywam.")
        return tp_price_final, sl_price_final

    px_sl_x = (entry_price_final - sl_price_final) / px
    px_tp_x = (tp_price_final - entry_price_final) / px

    print(f"px sl {px_sl_x} px tp {px_tp_x} px {px} tp price {tp_price_final}")
    try:
        diff_px = abs(px_sl_x)

        print(f"[TV CHECK] px_sl_x={px_sl_x} | diff={diff_px}px")

        if diff_px < 12:
            print("[🛑 TV] SL < 12px od entry → zamykam pozycję")
            close_position_tv()
            return tp_price_final, sl_price_final
    except Exception as e:
        print(f"[TV CHECK ERROR] {e}")

    # sanity check na absurdalne wartości
    MAX_PX_MOVE = 1070 
    if abs(px_sl_x) > MAX_PX_MOVE or abs(px_tp_x) > MAX_PX_MOVE:
        close_position_tv()
        print(f"[🚫] px_sl_x={px_sl_x}, px_tp_x={px_tp_x} wyglądają nienormalnie — NIE ruszam myszką.")
        return tp_price_final, sl_price_final

    # Ruchy myszką - BUY
    if chuj == "buy":
        px_tp_x *= -1
        print(f"[ACTION] moveTo(1300, {y_line}) then dragRel(0, {px_tp_x})")
        pyautogui.moveTo(1425, y_line, duration=0.2)
        pyautogui.dragRel(0, px_tp_x, duration=0.2, button='left')

        print(f"[ACTION] moveTo(1350, {y_line}) then dragRel(0, {px_sl_x})")
        pyautogui.moveTo(1425, y_line, duration=0.2)
        pyautogui.dragRel(0, px_sl_x, duration=0.2, button='left')

    # Ruchy myszką - SELL
    if chuj == "sell":
        px_tp_x *= -1
        print(f"[ACTION] moveTo(1300, {y_line}) then dragRel(0, {px_tp_x})")
        pyautogui.moveTo(1425, y_line, duration=0.2)
        pyautogui.dragRel(0, px_tp_x, duration=0.2, button='left')
        px_sl_x *= -1
        print(f"[ACTION] moveTo(1350, {y_line}) then dragRel(0, {px_sl_x} * -1)")
        pyautogui.moveTo(1425, y_line, duration=0.2)
        # tu masz w logice, że dla sell SL jest po drugiej stronie => mnożnik -1
        pyautogui.dragRel(0, -px_sl_x, duration=0.2, button='left')

# endregion
# region =============================== CSV =======================================

    attach_trade_to_latest_candle(
        symbol,
        side=side,
        entry_price=entry_price_final,
        sl_price=sl_price_final,
        tp_price=tp_price_final,
        csv_path=SAVE_PATH
    )
    if df is None:
        print("[ERROR] df is None — przerywam dalszą obróbkę (wskazówka: sprawdź read_ohlc_from_file / safe_read_ohlc_csv).")
        return  # lub continue w pętli, zależnie od kontekstu

    # upewnij się, że są wymagane kolumny
    required = ["timestamp", "open", "high", "low", "close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"[ERROR] Brakuje kolumn w df: {missing} — nie wykonuję dalszych operacji na tym df.")
        return # albo continue

    print("[CSV DEBUG] side =", side)
    print("[CSV DEBUG] entry_price_final =", entry_price_final)
    print("[CSV DEBUG] sl_price_final    =", sl_price_final)
    print("[CSV DEBUG] tp_price_final    =", tp_price_final)
    print("[CSV DEBUG] SAVE_PATH         =", SAVE_PATH)
    TRADE_CONTEXT[symbol] = {
        "timestamp": pd.Timestamp.utcnow(),
        "side": side,
        "entry": entry_price_final,
        "sl": sl_price_final,
        "tp": tp_price_final,
        "source": "tv_ocr",
    }

    position_active = True
    entry_index = len(df) - 1


    return tp_price_final, sl_price_final

# endregion
# endregion
# endregion
# region ======================================================= OTWIERANIE POZYCJI BINANCE =========================================
# region ========================================== MONITOR ==================================================

def monitor_tp_sl(symbol, df, entry_price, tp_price, sl_price, precision=2, max_check_candles=5):
    """
    Monitoruje, czy TP i SL są ustawione po otwarciu pozycji.
    Jeśli nie są ustawione w ciągu 5 świec, ustawia je ponownie lub zamyka pozycję awaryjnie.
    """
    candle_counter = 0

    while candle_counter < max_check_candles:
        time.sleep(60)  # Czeka na zamknięcie kolejnej świecy

        # Pobierz najnowsze dane świecy
        df = refresh_df_and_indicators(symbol, interval="1m", limit=3)
        df.index = pd.to_datetime(df.index)

        # Sprawdź, czy TP i SL są ustawione
        orders = client.futures_get_open_orders(symbol=symbol)
        tp_set = any(order['type'] == 'TAKE_PROFIT_MARKET' for order in orders)

        current_price = retry_on_time_error(
            lambda: float(client.futures_symbol_ticker(symbol=symbol)['price'])
        )

        global position_active, tp_sl_cache

        if is_position_open(symbol):
            # 🔹 Pozycja jest OTWARTA
            if not position_active:
                # przejście ZAMKNIĘTA → OTWARTA
                position_active = True
                print(f"[STATE] Pozycja {symbol} otwarta, position_active = {position_active}")

            # 🔹 Twoja logika TP
            if not tp_set:
                print(f"[❗ ALERT] Zlecenia TP dla {symbol} ZNIKNĘŁY! TP={tp_set}.")
                print(f"[⚠️] Podejmuję próbę awaryjnego zamknięcia pozycji.")
                force_close_position_until_success(symbol)
                return

        else:
            # 🔹 Pozycja JEST TERAZ ZAMKNIĘTA
            if position_active:
                # przejście OTWARTA → ZAMKNIĘTA -> czyścimy CSV i cache TYLKO RAZ
                clear_trade_in_csv(csv_path="ohlc_last.csv")

                if symbol in tp_sl_cache:
                    del tp_sl_cache[symbol]
                    print(f"[CACHE] Wyczyszczono tp_sl_cache dla {symbol}")

                position_active = False
                print(f"[STATE] Pozycja {symbol} zamknięta, position_active = {position_active}")

            print(f"[ℹ️] Pozycja już zamknięta — nic nie robię")
            return

        # Sprawdź czy pozycja nadal otwarta
        positions = client.futures_position_information(symbol=symbol)
        position_amt = float(next(p['positionAmt'] for p in positions if p['symbol'] == symbol))
        if abs(position_amt) < 0.0001:
            print(f"[✅] Pozycja na {symbol} zamknięta – kończę monitorowanie SL/TP.")
            return

        # Pobierz najnowsze dane świecy
        df = refresh_df_and_indicators(symbol, interval="1m", limit=3)
        df.index = pd.to_datetime(df.index)
        if tp_set:
            print(f"[✅] TP jest ustawione — sprawdzam dokładne wartości na Binance...")
            ok = verify_and_fix_tp_sl(
                symbol=symbol,
                side='BUY' if entry_price < tp_price else 'SELL',
                tp_expected=tp_price
            )
            if not ok:
                print(f"[🛑] Próba ustawienia TP nieudana — zamykam pozycję awaryjnie")
                force_close_position_until_success(symbol)
                return
            continue

        candle_counter += 1
        print(f"[⏱️] TP/SL nie ustawione. Próba {candle_counter}/{max_check_candles} dla {symbol}.")
        print(f"tp= {tp_set}")

    # Jeśli licznik się wyczerpał, podejmij odpowiednie działanie
    if not tp_set:
        print(f"[⚠️ BRAKUJE TP] Spróbuję ustawić brakujące TP dla {symbol}")
        ok = verify_and_add_missing_tp_sl(
            symbol=symbol,
            side='BUY' if entry_price < tp_price else 'SELL',
            tp_expected=tp_price
        )
        if not ok:
            print(f"[❌ NIE UDAŁO SIĘ] Ustawienie brakującego TP/SL nie powiodło się — zamykam pozycję awaryjnie")
            force_close_position_until_success(symbol)
            return
        else:
            candle_counter += 1
            print(f"[🔁] Ponowna próba — TP/SL zostały dodane, kontynuuję monitorowanie...")

# endregion
# region ========================================== OTWIERANIE ===============================================
# endregion
# region ========================================== ZAMYKANIE ================================================

def close_position(symbol, position):
    try:
        # pobierz faktyczną ilość pozycji
        positions = client.futures_position_information (symbol=symbol)
        qty = 0.0
        for pos in positions:
            if pos['symbol'] == symbol:
                qty = abs(float(pos['positionAmt']))
                break

        if qty == 0:
            print(f"[INFO] Nie ma pozycji do zamknięcia dla {symbol}")
            return

        side = "SELL" if position == "long" else "BUY"

        retry_on_time_error(
            client.futures_create_order,
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=qty,
        )

        print(f"[ZAMKNIĘCIE] Pozycja {position} na {symbol} została zamknięta.")

    except Exception as e:
        print(f"[BŁĄD] Nie udało się zamknąć pozycji na {symbol}: {e}")

# endregion
# region ========================================== OPEN POS =================================================

def verify_and_add_missing_tp_sl(symbol, side, tp_expected, sl_expected, tick_size=0.01, precision=2):
    try:
        orders = client.futures_get_open_orders(symbol=symbol)
        tp_exists = any(o["type"] == "TAKE_PROFIT_MARKET" for o in orders)

        if not tp_exists:
            retry_on_time_error(
                client.futures_create_order,
                symbol=symbol,
                side='SELL' if side == 'BUY' else 'BUY',
                type='TAKE_PROFIT_MARKET',
                stopPrice=str(round_to_step(tp_expected, tick_size)),
                closePosition=True,
                timeInForce='GTC'
            )
            print(f"[✅ TP USTAWIONY] {tp_expected}")
        return True
    except Exception as e:
        print(f"[❌ BŁĄD verify_and_add_missing_tp_sl] {symbol}: {e}")
        return False

# endregion
# endregion
# region ======================================================= NOWA ŚWIECA BINANCE ================================================

def wait_for_closed_candle(symbol, last_checked_candle):

    if str(x).lower() == 'tv':
        return wait_for_closed_candle_tv_safe(last_checked_candle)

    while True:
        df = get_futures_klines(symbol, interval='1m', limit=3)
        if df is None or df.empty:
            print(f"[⛔ BRAK DANYCH] df is None lub pusty w wait_for_closed_candle dla {symbol}")
            return None  # lub poczekaj i spróbuj ponownie
        candle_time = df.index[-2]

        if last_checked_candle is not None and candle_time <= last_checked_candle:
            time.sleep(5)
            continue
        return candle_time

# endregion
# region !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! WARNINGI !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

#=========== DAJ CTRL F BO JEST TO POJEBANE TYLKO DO BINANCE ===============

def safe_binance_call(func, *args, **kwargs):
    return func(*args, **kwargs)
def retry_on_time_error(func, *args, **kwargs):
    return func(*args, **kwargs)


#============ testuj o chuj chodzi =======================

def save_trade_to_excel(symbol, position_type, entry_price, sl, tp, result_usdt, df_before, df_after):
    # Skopiuj, żeby nie modyfikować oryginalnych DataFrame'ów
    df_before = df_before.copy()
    df_after = df_after.copy()

    # Dodaj numer offsetu świecy (względem momentu wejścia)
    df_before['candle_offset'] = list(range(-len(df_before)+1, 1))
    df_after['candle_offset'] = list(range(1, len(df_after)+1))

    # Łączymy dane przed i po w jedno
    df_all = pd.concat([df_before, df_after])
    df_all.reset_index(inplace=True)
    df_all['timestamp'] = df_all['timestamp'].dt.tz_localize(None)

    # Dodaj dane pozycji (wypełniamy tylko w świecy 0)
    df_all['symbol'] = symbol
    df_all['position_type'] = position_type
    df_all['entry_price'] = None
    df_all['sl'] = None
    df_all['tp'] = None
    df_all['result_usdt'] = None

    entry_index = df_all[df_all['candle_offset'] == 0].index
    if not entry_index.empty:
        i = entry_index[0]
        df_all.loc[i, 'entry_price'] = entry_price
        df_all.loc[i, 'sl'] = sl
        df_all.loc[i, 'tp'] = tp
        df_all.loc[i, 'result_usdt'] = result_usdt

    # Ścieżka do pliku
    os.makedirs("excel", exist_ok=True)
    excel_path = "excel/trade_log.xlsx"

    # Nazwa arkusza np. LONG_ETHUSDT_2025-06-24_15-21
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    sheet_name = f"{position_type}_{symbol}_{timestamp}"

    # Zapis do Excela (append arkusza)
    if os.path.exists(excel_path):
        with pd.ExcelWriter(excel_path, engine="openpyxl", mode="a", if_sheet_exists="new") as writer:
            df_all.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            df_all.to_excel(writer, sheet_name=sheet_name, index=False)

# endregion
# region !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! UŻYCIE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

setup_exit_shortcut()

if os.path.exists(SAVE_PATH):
    os.remove(SAVE_PATH)
    print(f"[🗑] Usunięto stary plik {SAVE_PATH}")

load_dotenv()
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
if not api_key or not api_secret:
    raise Exception("❌ Brak kluczy API w pliku .env")
client = Client(api_key, api_secret)

client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'
TIME_OFFSET = get_time_offset()

# Parametry transakcji
if str(x).lower() == "tv":
    symbols = ["BTCUSDT"]
    open_tv()
else:
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
position_locks = {symbol: threading.Lock() for symbol in symbols}
pullback_state = {symbol: False for symbol in symbols}
last_checked_candles = {symbol: None for symbol in symbols}



# endregion
# region !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! DEF TRADE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

def trade(symbol, tp_multiplier, precision):

# region ========================================== RESET PULLBACK UP =======================================

    #=== resret pullbacku ===
    def reset_pullback_up():
        nonlocal pullback_up_part2, dotknieto_50_up,already_warned_bad_dema_up, already_warned_too_close_dema_up
        nonlocal waiting_20, waiting_50, waiting_20_counter, waiting_50_counter, dotknieto_100
        nonlocal waiting_pullback_up, pullback_up_counter, pullback1_up_counter, dotknieto_50
        nonlocal last_used_fractal_time, dotknieto_20_up, kolejnosc_up_counter, dotknieto_20
        nonlocal wybicie_counter_20_up, wybicie_counter_up, wybicie_counter_50_up
        nonlocal pullback_part_1_up
        pullback_up_part2 = False
        pullback_state[symbol] = False
        waiting_20 = False
        waiting_50 = False
        waiting_20_counter = 0
        waiting_50_counter = 0
        waiting_pullback_up = False
        pullback_up_counter = 0
        pullback1_up_counter = 0
        last_used_fractal_time = None
        kolejnosc_up_counter = 0
        wybicie_counter_up = 0
        wybicie_counter_20_up = 0
        dotknieto_20_up = False
        wybicie_counter_50_up = 0
        dotknieto_50_up = False
        already_warned_bad_dema_up = False
        already_warned_too_close_dema_up = False
        dotknieto_20 = False
        dotknieto_50 = False
        dotknieto_100 = False
        cooldown = 0
        pullback_part_1_up = False

# endregion
# region ========================================== RESET PULLBACK DOWN =====================================

    def reset_pullback_down():
        nonlocal pullback_down_part2, pullback_part_1_down
        nonlocal waiting_20_down, waiting_50_down
        nonlocal waiting_20_down_counter, waiting_50_down_counter
        nonlocal waiting_pullback_down, pullback_counter, pullback1_counter
        nonlocal last_used_fractal_time_down, kolejnosc_down_counter, wybicie_counter_down
        nonlocal wybicie_counter_20_down, wybicie_counter_50_down, dotknieto_50_down, dotknieto_20_down
        nonlocal already_warned_bad_dema, already_warned_too_close_dema, dotknieto_50_down2
        nonlocal dotknieto_100_down2, dotknieto_20_down2
        pullback_part_1_down = False
        already_warned_bad_dema = False
        already_warned_too_close_dema = False
        pullback_down_part2 = False
        waiting_20_down = False
        waiting_50_down = False
        waiting_20_down_counter = 0
        waiting_50_down_counter = 0
        waiting_pullback_down = False
        pullback_counter = 0
        pullback1_counter = 0
        last_used_fractal_time_down = None
        kolejnosc_down_counter = 0
        wybicie_counter_down = 0
        wybicie_counter_20_down = 0
        dotknieto_20_down = False
        dotknieto_50_down = False
        wybicie_counter_20_down = 0
        wybicie_counter_50_down = 0
        dotknieto_50_down2 = False
        dotknieto_100_down2 = False
        dotknieto_20_down2 = False
        cooldown_down = 0

# endregion
# region ========================================== ALL NONE ================================================
    
    position = None
    # Flagi etapu pullbacku
    pullback_down_part2 = False
    waiting_pullback_down = False
    pullback_counter = 0
    pullback1_counter = 0
    pullback_up_part2 = False
    pullback_state[symbol] = False
    waiting_pullback_up = False
    pullback_up_counter = 0
    pullback1_up_counter = 0
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
    kolejnosc_up_counter = 0
    kolejnosc_down_counter = 0
    wybicie_counter_up = 0
    wybicie_counter_down = 0
    wybicie_counter_20_up = 0
    wybicie_counter_20_down = 0
    dotknieto_20_up = False
    dotknieto_20_down = False
    dotknieto_50_down = False
    wybicie_counter_20_down = 0
    wybicie_counter_50_down = 0
    wybicie_counter_50_up = 0
    dotknieto_50_up = False
    already_warned_bad_dema = False
    already_warned_too_close_dema = False
    already_warned_bad_dema_up = False
    already_warned_too_close_dema_up = False
    dotknieto_20 = False
    dotknieto_50 = False
    dotknieto_100 = False
    dotknieto_50_down2 = False
    dotknieto_100_down2 = False
    dotknieto_20_down2 = False
    last_checked_candle = None
    global last_checked_candles 
    global chuj
    chuj = None
    global cw
    cw = False
    is_open = retry_on_time_error(is_position_open, symbol)
    cooldown = 0
    cooldown_down = 0
    pullback_part_1_up = False
    pullback_part_1_down = False

    high_short = None
    kolejność_short = None

    high_long = None
    kolejność_long = None

# endregion
# region ========================================== ODPALANIE ===============================================
    
    while True:
        if str(x).lower() == "tv" and symbol != "BTCUSDT":
            return

        now = datetime.now()

        last_checked = last_checked_candles[symbol]
        is_open = retry_on_time_error(is_position_open, symbol)
        new_candle_time = wait_for_closed_candle(symbol, last_checked)

        df = get_futures_klines(symbol, interval='1m', limit=3)

        # brak danych OHLC
        if df is None or df.empty:
            print(f"[TRADE ⚠️] {symbol}: brak danych OHLC — pomijam iterację")
            time.sleep(1)
            continue

        df = apply_dema_indicators(df)

        # brak DEMA
        if df is None or df.empty:
            print(f"[TRADE ⚠️] {symbol}: brak DEMA — pomijam iterację")
            time.sleep(1)
            continue

        # TERAZ wolno dotykać index
        df.index = pd.to_datetime(df.index)

        if len(df) < 2:
            print(f"[TRADE ⚠️] {symbol}: za mało świec")
            continue

        last_checked_candle = df.index[-2]
        last_checked_candles[symbol] = new_candle_time

        if x == "tv":
            row = df.iloc[-1]   # TV  świeca zamknięta
        else:
            row = df.iloc[-2]

        if not all(k in row for k in ["DEMA_short", "DEMA_medium", "DEMA_long"]):
            print(f"[TRADE ⚠️] Brak kolumn DEMA w row ({symbol})")
            continue

        # Czekaj aż pojawi się świeca po last_checked_candle
        new_candle_time = wait_for_closed_candle(symbol, last_checked_candle)

        if new_candle_time == last_checked_candle:
            print("kurwa")
            time.sleep(1)
            continue
        last_checked_candle = new_candle_time

        lock = position_locks[symbol]
        with lock:
            df = refresh_df_and_indicators(symbol)
            if df is None or df.empty:
                print(f"[BŁĄD] df jest None lub pusty — pomijam {symbol}")
                time.sleep(5)
                continue

            if x == "tv": 
                row = df.iloc[-1]   # TradingView → ostatnia świeca już zamknięta
            else:
                row = df.iloc[-2]

            try:
                try:
                    if x == "binance":
                        current_price = retry_on_time_error(lambda: float(client.futures_symbol_ticker(symbol=symbol)['price']))
                    if x == "tv":
                        current_price = df['close'].iloc[-1]
                except requests.exceptions.ReadTimeout:
                    print(f"[TIMEOUT] [{datetime.now().strftime('%H:%M')}] Timeout przy pobieraniu ceny {symbol}. Próbuję ponownie za chwilę.")
                    time.sleep(5)
                    continue

# endregion
# region ========================================== DF ======================================================
                
                df = refresh_df_and_indicators(symbol)
                if df is None or df.empty:
                    print(f"[BŁĄD] df jest None lub pusty — pomijam {symbol}")
                    time.sleep(5)
                    continue
                df = get_futures_klines(symbol, interval="1m", limit=500)
                if df is None or df.empty:
                    print(f"[BŁĄD] [{datetime.now().strftime('%H:%M')}] Nie udało się pobrać danych dla {symbol}")
                    return
                df = apply_dema_indicators(df)
                df, fractal_list = detect_fractals(df)
                
                df = df.dropna(subset=["DEMA_short", "DEMA_medium", "DEMA_long"])
                if df.empty or len(df) < 3:
                    print(f"[BRAK DANYCH] [{datetime.now().strftime('%H:%M')}] {symbol}")
                    time.sleep(20)
                    continue
                    
                required_cols = ['DEMA_short', 'DEMA_medium', 'DEMA_long']
                if not all(col in df.columns for col in required_cols):
                    print(f"[ERROR] Brak kolumn DEMA w df ({symbol}), pomijam...")
                    continue

# endregion
# region ========================================== RESETY CLOSE AI =========================================
            
                if pullback_up_part2:
                    if dotknieto_100:
                        print (f"[RESET] [{datetime.now().strftime('%H:%M')}] dotknięcie dema 100 dla {symbol}")
                        reset_pullback_up()
                        continue
                    
                if pullback_down_part2:
                    if dotknieto_100_down2:
                        print (f"[RESET] [{datetime.now().strftime('%H:%M')}] dotknięcie dema 100 dla {symbol}")
                        reset_pullback_down()
                        continue    


                # Upewnij się, że mamy wystarczająco danych
                if len(df) < 3:
                    print(f"[SKIP] Za mało danych ({len(df)}) dla {symbol}, pomijam...")
                    continue

                # pobierz row
                if x == "tv": 
                    row = df.iloc[-1]   # TradingView ostatnia świeca już zamknięta
                else:
                    row = df.iloc[-2]

                # Jeśli jest otwarta pozycja LONG i zanikła kolejność DEMA zamknij
                if position == "long" and not (row['DEMA_short'] > row['DEMA_medium'] > row['DEMA_long']):
                    close_position(symbol)
                    reset_pullback_up()
                    print(f"[ZAMKNIĘCIE] [{datetime.now().strftime('%H:%M')}] Trend wzrostowy DEMA zanikł — {symbol}")
                    continue

                # Jeśli jest otwarta pozycja SHORT i zanikła kolejność DEMA zamknij
                if position == "short" and not (row['DEMA_short'] < row['DEMA_medium'] < row['DEMA_long']):
                    close_position(symbol)
                    reset_pullback_down()
                    print(f"[ZAMKNIĘCIE] [{datetime.now().strftime('%H:%M')}] Trend spadkowy DEMA zanikł — {symbol}")
                    continue
                latest_fractal = fractal(symbol, df)
                if df is None or df.empty:
                    print("[⛔ trade] df jest None/puste — NIE wywołuję fractal()")
                    continue 

                # RESET DLA UP — jeśli aktywny pullback lub waiting, ale zła kolejność DEMA
                if pullback_up_part2 or waiting_20 or waiting_50:
                    if not (row['DEMA_short'] > row['DEMA_medium'] > row['DEMA_long']):
                        print(f"[RESET_UP] [{datetime.now().strftime('%H:%M')}] Zła kolejność DEMA przy aktywnym pullback — {symbol}")
                        reset_pullback_up()
                        continue
                                
                # RESET DLA DOWN — jeśli aktywny pullback lub waiting, ale zła kolejność DEMA
                if pullback_down_part2 or waiting_20_down or waiting_50_down:
                    if not (row['DEMA_short'] < row['DEMA_medium'] < row['DEMA_long']):
                        print(f"[RESET_DOWN] [{datetime.now().strftime('%H:%M')}] Zła kolejność DEMA przy aktywnym pullback — {symbol}")
                        reset_pullback_down()
                        continue

                if str(x).lower() == "binance":
                    chart_path = generate_clean_chart(symbol)
                    market_status = predict_image(chart_path)
                    if market_status == "bad":
                        print(f"[AI] {symbol} → rynek chujowy, pomijam analizę.")
                        continue
                    else:
                        print(f"[AI] {symbol} → rynek dobry, lecimy z DEMA/fractale.")

            except Exception as e:
                print("Wystąpił wyjątek!")
                print(f"[EXCEPTION] {type(e).__name__}: {str(e) or 'brak treści'}")
                traceback.print_exc()
                reset_pullback_up()
                reset_pullback_down()
                position = None
                time.sleep(10)
                continue 

# endregion
# region ========================================== PULLBACK UP =============================================
# region ====================================== WSTĘP =========================================         

            if (not pullback_up_part2 and
                row['low'] > row['DEMA_short'] and
                row['low'] > row['DEMA_medium'] and
                row['low'] > row['DEMA_long'] and
                row['DEMA_short'] > row['DEMA_medium'] > row['DEMA_long']):

                pullback_up_part2 = True
                pullback_state[symbol] = True
                pullback1_up_counter = 0
                continue
                
            if pullback_up_part2:
                #  RESET jeśli kolejność DEMA się rozsypała, zanim dotknęło DEMA
                if not (row['DEMA_short'] > row['DEMA_medium'] > row['DEMA_long']):
                    reset_pullback_up()
                    continue


                dema_20 = row['DEMA_short']
                dema_50 = row['DEMA_medium']
                dema_100 = row['DEMA_long']

                dotknieto_20 = (
                    row['low'] < row['DEMA_short'] and
                    row['low'] > row['DEMA_medium'] and
                    row['low'] > row['DEMA_long']
                )   
                dotknieto_50 = (
                    row['low'] < row['DEMA_short'] and
                    row['low'] < row['DEMA_medium'] and
                    row['low'] > row['DEMA_long']
                )
                dotknieto_100 = row['low'] <= dema_100

                # PRIORYTET: DEMA 50 > DEMA 20
                if dotknieto_20 and not waiting_20 and not waiting_50:
                    waiting_20 = True
                    waiting_20_counter = 0

                elif dotknieto_50 and not waiting_50 and not waiting_20:
                    waiting_50 = True
                    waiting_50_counter = 0

                elif dotknieto_100:
                    print (f"[RESET] [{datetime.now().strftime('%H:%M')}] dotknięcie dema 100 dla {symbol}")
                    reset_pullback_up()
                    continue

# endregion
# region ==================================== WAITING 50 ======================================
# region ========================== WSTĘP  =================================
            if waiting_50:
                if cooldown < 3:
                    cooldown += 1
                    continue
                print("waiting")
                waiting_20 = False 
                dotknieto_100 = row['low'] <= dema_100
                new_fractal, fractal_time = fractal(symbol, df)
                if dotknieto_100:
                    print (f"[RESET] [{datetime.now().strftime('%H:%M')}] dotknięcie dema 100 dla {symbol}")
                    reset_pullback_up()
                    continue

                new_fractal, fractal_time = fractal(symbol, df)
                print(f"[{datetime.now().strftime('%H:%M')}] czeka na fractala 50 up dla {symbol}")
                if not (row['DEMA_short'] > row['DEMA_medium'] > row['DEMA_long']):
                    print(f"[RESET] [{datetime.now().strftime('%H:%M')}] Zła kolejność DEMA w czasie waiting_20 — reset dla {symbol}")
                    reset_pullback_up()
                    waiting_50 = False
                    wybicie_counter_50_up = 0
                    continue
                
                if x == "tv":
                    is_open = is_position_open(symbol)
                else:
                    is_open = retry_on_time_error(is_position_open, symbol)

                print(f"[DEBUG] is_position_open({symbol}) = {is_open}")
                print(f"czeka na fractala 20 down dla {symbol}")
                print(f"new fractal = {new_fractal} next {fractal_time} =! {last_used_fractal_time}")

                if (
                    new_fractal == "upFractal"
                    and fractal_time != last_used_fractal_time
                    and not retry_on_time_error(is_position_open, symbol)
                ):

                    if fractal_time is None or pd.isna(fractal_time):
                        print(f"[❌ BŁĄD] fractal_time = {fractal_time} → pomijam {symbol}")
                        reset_pullback_up()  # lub reset_pullback_down() zależnie od kontekstu
                        continue

                    if should_skip_due_to_distance(symbol, current_price, fractal_time, df, "long"):
                        reset_pullback_up()
                        waiting_20 = False
                        waiting_50 = False
                        continue
               
                    if not had_recent_impulse(df, symbol, direction='up', lookback=3):
                        print (f"[RESET] [{datetime.now().strftime('%H:%M')}] dema za blisko dla {symbol}")
                        reset_pullback_up()
                        continue
            
                    # 1. Pobierz dane z fraktalem
                    print(f"[⏱️] Czekam na nową świecę...")
                    new_candle_time = wait_for_closed_candle(symbol, df.index[-2])

                    df_check = get_futures_klines(symbol, interval='1m', limit=2)
                    df_check = apply_dema_indicators(df_check)
                    df_check = df_check.dropna()

                    current_row = df_check.iloc[-2]



                    last_used_fractal_time = fractal_time
                    print(f"[SYGNAŁ] [{datetime.now().strftime('%H:%M')}] upFractal z {fractal_time} — próbuję LONG na {symbol}")

# endregion
# region ======================== KUPOWANIE  ===============================
# region ====================== TV  ==============================
                    if x == "tv":
                        chuj = "buy"
                        sl_price = round(df["DEMA_long"].iloc[-1], 2)
                        print(f"sl wedlog petli = {sl_price}")
                        step_size, tick_size = get_symbol_precision(symbol)
                 
                        ai_result = predict_long()

                        print(f"LONG AI THINKS: {ai_result}")

                        try:
                            tp_price, sl_price = place_futures_order_with_tp_sl_tv(
                                symbol=symbol,            # ← JEDYNA ZMIANA
                                quantity=0.5,
                                entry_price=None,
                                sl_price=sl_price,
                                waiting_20=waiting_20,
                                waiting_50=waiting_50,
                                waiting_20_down=waiting_20_down,
                                waiting_50_down=waiting_50_down,
                                df=df,
                                precision=precision,
                                tp_multiplier=tp_multiplier,      # ← JEDYNA ZMIANA
                            )
                            reset_pullback_up()             # ← BUY = UP
                            print("reset")
                        except Exception as e:
                            print(f"[BŁĄD KRYTYCZNY] [{datetime.now().strftime('%H:%M')}] place_futures_order_with_tp_sl_tv rzucił wyjątek na {symbol}: {e}")
                            reset_pullback_up()
                            continue
# endregion
# region =================== BINANCE  ============================
                    else:
                        chuj = "buy"
                        # Stara logika (API / Binance)
                        sl_price = round(df["DEMA_long"].iloc[-1], 2)
                        entry_price = current_price
                        qty = calculate_dynamic_qty(entry_price, sl_price, symbol)

                        if qty <= 0:
                            print(f"[BŁĄD] Ilość pozycji = {qty} — nie otwieram LONG na {symbol}")
                            reset_pullback_up()
                            continue

                        step_size, tick_size = get_symbol_precision(symbol)
                        qty = round_to_step(qty, step_size)
                        entry_price = round_to_step(entry_price, tick_size)
                        sl_price = round_to_step(sl_price, tick_size)

                        try:
                            tp_price, sl_price = place_futures_order_with_tp_sl(
                                symbol=symbol,
                                side=SIDE_BUY,
                                quantity=qty,
                                entry_price=entry_price,
                                sl_price=sl_price,
                                waiting_20=waiting_20,
                                waiting_50=waiting_50,
                                waiting_20_down=waiting_20_down,
                                waiting_50_down=waiting_50_down,
                                df=df,
                                precision=precision,
                                tp_multiplier=tp_multiplier,
                                opposite=SIDE_SELL,
                                tick_size=tick_size
                                )
                            if tp is not None:
                                print(f"[OTWARTA POZYCJA] [{datetime.now().strftime('%H:%M')}] LONG {symbol} | TP: {tp} | SL: {sl}")
                                if x == "binance":
                                    start_logical_sl_monitor(symbol, entry_price, sl_price, tp_price)
                                    monitor_tp_sl(symbol, df, entry_price, tp, precision)
                                position = 'LONG'
                                reset_pullback_up()
                            else:
                                print(f"[BŁĄD] [{datetime.now().strftime('%H:%M')}] Nie udało się otworzyć pozycji LONG na {symbol}")
                                if x == "binance":    
                                    monitor_tp_sl(symbol, df, entry_price, tp, precision)
                                reset_pullback_up()
                            continue
                        except Exception as e:
                            print(f"[BŁĄD KRYTYCZNY] [{datetime.now().strftime('%H:%M')}] place_futures_order_with_tp_sl rzucił wyjątek na {symbol}: {e}")
                            reset_pullback_up()
                            continue

# endregion
# endregion
# region ====================== WYBICIE ENDING  ============================
                # Jeśli cena wyszła nad DEMA50 → odliczaj 5 świec
                if not dotknieto_50_up and row['low'] < row['DEMA_short']:
                    dotknieto_50_up = True

                if dotknieto_50_up and row['close'] > row['DEMA_short']:
                    wybicie_counter_50_up += 1
                    print(f"[⏱️ WYBICIE 50] [{datetime.now().strftime('%H:%M')}] Nad DEMA50 — {wybicie_counter_50_up}/5 dla {symbol}")
                    # Jeśli w czasie czekania na wybicie 50, cena spadnie pod DEMA 100 → reset
                    if waiting_50 and row['low'] < row['DEMA_long']:
                        print(f"[RESET] [{datetime.now().strftime('%H:%M')}] Spadek pod DEMA 100 w czasie waiting_50 — reset dla {symbol}")
                        reset_pullback_up()
                        waiting_20 = False
                        waiting_50 = False
                        wybicie_counter_50_up = 0
                        continue

                    if wybicie_counter_50_up >= 3:
                        print(f"[RESET] [{datetime.now().strftime('%H:%M')}] Wybicie DEMA50 trwa zbyt długo — reset {symbol}")
                        reset_pullback_up()
                        pullback_up_part2 = True
                        continue
                else:
                    wybicie_counter_50_up = 0


                # Reset jeśli układ DEMA popsuty
                if not (row['DEMA_short'] > row['DEMA_medium'] > row['DEMA_long']):
                    print (f"[RESET] [{datetime.now().strftime('%H:%M')}] zła kolejność dema dla {symbol}")
                    reset_pullback_up()
                    continue

                waiting_50_counter += 1
                if waiting_50_counter >= 10:
                    print(f"[RESET] [{datetime.now().strftime('%H:%M')}] Brak fraktala po DEMA 50 → resetuję {symbol}")
                    reset_pullback_up()

# endregion
#endregion
# region ==================================== WAITING 20  =====================================
# region ========================== WSTĘP  =================================

            # === Czekanie na fraktala DEMA 20 ===
            elif waiting_20:
                if cooldown < 3:
                    cooldown += 1
                    continue
                print("waiting 20")
                dotknieto_100 = row['low'] <= dema_100
                new_fractal, fractal_time = fractal(symbol, df)
                if dotknieto_100:
                    print (f"[RESET] [{datetime.now().strftime('%H:%M')}] dotknięcie dema 100 dla {symbol}")
                    reset_pullback_up()
                    continue

                if x == "tv":
                    is_open = is_position_open(symbol)
                else:
                    is_open = retry_on_time_error(is_position_open, symbol)

                print(f"czeka na fractala 20 up dla {symbol}")
                print(f"[DEBUG] is_position_open({symbol}) = {is_open}")
                print(f"new fractal = {new_fractal} next {fractal_time} =! {last_used_fractal_time}")
                if (
                    new_fractal == "upFractal"
                    and fractal_time != last_used_fractal_time
                    and not retry_on_time_error(is_position_open, symbol)
                ):

                    if fractal_time is None or pd.isna(fractal_time):
                        print(f"[❌ BŁĄD] fractal_time = {fractal_time} → pomijam {symbol}")
                        reset_pullback_up()  # lub reset_pullback_down() zależnie od kontekstu
                        continue


                    if should_skip_due_to_distance(symbol, current_price, fractal_time, df, "long"):
                        reset_pullback_up()
                        waiting_20 = False
                        waiting_50 = False
                        continue

                
                    if not had_recent_impulse(df, symbol, direction='up', lookback=3):
                        print (f"[RESET] [{datetime.now().strftime('%H:%M')}] dema za blisko dla {symbol}")
                        reset_pullback_up()
                        continue
   

                    # 1. Pobierz dane z fraktalem
                    print(f"[⏱️] Czekam na nową świecę...")
                    new_candle_time = wait_for_closed_candle(symbol, df.index[-2])

                    df_check = get_futures_klines(symbol, interval='1m', limit=2)
                    df_check = apply_dema_indicators(df_check)
                    df_check = df_check.dropna()

                    current_row = df_check.iloc[-2]




                    last_used_fractal_time = fractal_time
                    print(f"[SYGNAŁ] [{datetime.now().strftime('%H:%M')}] upFractal z {fractal_time} — próbuję LONG na {symbol}")

# endregion
# region ======================== KUPOWANIE  ===============================
# region ====================== TV  ==============================
                    if x == "tv":
                        chuj = "buy"
                        sl_price = round(df["DEMA_long"].iloc[-1], 2)
                        print(f"sl wedlog petli = {sl_price}")
                        step_size, tick_size = get_symbol_precision(symbol)


                        ai_result = predict_long()

                        print(f"LONG AI THINKS: {ai_result}")

                        try:
                            tp_price, sl_price = place_futures_order_with_tp_sl_tv(
                                symbol=symbol,          # ← JEDYNA ZMIANA
                                quantity=0.5,
                                entry_price=None,
                                sl_price=sl_price,
                                waiting_20=waiting_20,
                                waiting_50=waiting_50,
                                waiting_20_down=waiting_20_down,
                                waiting_50_down=waiting_50_down,
                                df=df,
                                precision=precision,
                                tp_multiplier=tp_multiplier,    # ← JEDYNA ZMIANA
                            )
                            reset_pullback_up()             # ← BUY = UP
                            print("reset")
                        except Exception as e:
                            print(f"[BŁĄD KRYTYCZNY] [{datetime.now().strftime('%H:%M')}] place_futures_order_with_tp_sl_tv rzucił wyjątek na {symbol}: {e}")
                            reset_pullback_up()
                            continue
# endregion
# region ==================== BINANCE  ===========================
                    else:
                        chuj = "buy"
                        # Stara logika (API / Binance)
                        sl_price = round(df["DEMA_medium"].iloc[-1], 2)
                        entry_price = current_price
                        qty = calculate_dynamic_qty(entry_price, sl_price, symbol)

                        if qty <= 0:
                            print(f"[BŁĄD] Ilość pozycji = {qty} — nie otwieram LONG na {symbol}")
                            reset_pullback_up()
                            continue

                        step_size, tick_size = get_symbol_precision(symbol)
                        qty = round_to_step(qty, step_size)
                        entry_price = round_to_step(entry_price, tick_size)
                        sl_price = round_to_step(sl_price, tick_size)

                        try:
                            tp_price, sl_price = place_futures_order_with_tp_sl(
                                symbol=symbol,
                                side=SIDE_BUY,
                                quantity=qty,
                                entry_price=entry_price,
                                sl_price=sl_price,
                                waiting_20=waiting_20,
                                waiting_50=waiting_50,
                                waiting_20_down=waiting_20_down,
                                waiting_50_down=waiting_50_down,
                                df=df,
                                precision=precision,
                                tp_multiplier=tp_multiplier,
                                opposite=SIDE_SELL,
                                tick_size=tick_size
                                )
                            if tp is not None:
                                print(f"[OTWARTA POZYCJA] [{datetime.now().strftime('%H:%M')}] LONG {symbol} | TP: {tp} | SL: {sl}")
                                if x == "binance":
                                    start_logical_sl_monitor(symbol, entry_price, sl_price, tp_price)
                                    monitor_tp_sl(symbol, df, entry_price, tp, precision)
                                position = 'LONG'
                                reset_pullback_up()
                            else:
                                print(f"[BŁĄD] [{datetime.now().strftime('%H:%M')}] Nie udało się otworzyć pozycji LONG na {symbol}")
                                if x == "binance":    
                                    monitor_tp_sl(symbol, df, entry_price, tp, precision)
                                reset_pullback_up()
                            continue
                        except Exception as e:
                            print(f"[BŁĄD KRYTYCZNY] [{datetime.now().strftime('%H:%M')}] place_futures_order_with_tp_sl rzucił wyjątek na {symbol}: {e}")
                            reset_pullback_up()
                            continue
#endregion
#endregion
# region ===================== WYBICIE ENDING  =============================

                # Jeśli cena wyszła nad DEMA — licz do 5
                if not dotknieto_20_up and row['low'] < row['DEMA_short']:
                    dotknieto_20_up = True

                if dotknieto_20_up and row['close'] > row['DEMA_short']:
                    wybicie_counter_20_up += 1
                    print(f"[⏱️ WYBICIE 20] [{datetime.now().strftime('%H:%M')}] Nad DEMA20 — {wybicie_counter_20_up}/5 dla {symbol}")
                    if wybicie_counter_20_up >= 3:
                        print(f"[RESET] [{datetime.now().strftime('%H:%M')}] Wybicie DEMA20 trwa zbyt długo — reset {symbol}")
                        reset_pullback_up()
                        pullback_up_part2 = True
                        continue
                else:
                    wybicie_counter_20_up = 0


                # reset jeśli DEMA się rozjechały
                if not (row['DEMA_short'] > row['DEMA_medium'] > row['DEMA_long']):
                    print (f"[RESET] [{datetime.now().strftime('%H:%M')}] zła kolejność dema dla {symbol}")
                    reset_pullback_up()
                    continue

                waiting_20_counter += 1
                if waiting_20_counter >= 10:
                    print(f"[RESET] [{datetime.now().strftime('%H:%M')}] Brak fraktala po DEMA 20 → resetuję {symbol}")
                    reset_pullback_up()
# endregion
# endregion
# endregion
# region ========================================== PULLBACK DOWN ===========================================
# region ====================================== WSTĘP =========================================
            
            if (not pullback_down_part2 and
                row['high'] < row['DEMA_short'] and
                row['high'] < row['DEMA_medium'] and
                row['high'] < row['DEMA_long'] and
                row['DEMA_short'] < row['DEMA_medium'] < row['DEMA_long']):

                pullback_down_part2 = True
                continue
            
            if pullback_down_part2:
                #  RESET jeśli DEMA się rozjechały zanim dotknęło DEMA
                if not (row['DEMA_short'] < row['DEMA_medium'] < row['DEMA_long']):
                    reset_pullback_down()
                    continue
                    

                dema_20 = row['DEMA_short']
                dema_50 = row['DEMA_medium']
                dema_100 = row['DEMA_long']

                dotknieto_20_down2 =(
                    row['high'] > row['DEMA_short'] and
                    row['high'] < row['DEMA_medium'] and
                    row['high'] < row['DEMA_long']
                )
                dotknieto_50_down2 =(
                    row['high'] > row['DEMA_short'] and
                    row['high'] > row['DEMA_medium'] and
                    row['high'] < row['DEMA_long']
                )
                dotknieto_100_down2 = row['high'] >= dema_100

                # PRIORYTET: DEMA 50 > DEMA 20
                if dotknieto_20_down2 and not waiting_20_down and not waiting_50_down:
                    waiting_20_down = True
                    waiting_20_down_counter = 0

                elif dotknieto_50_down2 and not waiting_50_down and not waiting_20_down:
                    waiting_50_down = True
                    waiting_50_down_counter = 0

                elif dotknieto_100_down2:
                    print (f"[RESET] [{datetime.now().strftime('%H:%M')}] dotknięcie dema 100 dla {symbol}")
                    reset_pullback_down()
                    continue
# endregion
# region ==================================== WAITING 50 ======================================
# region ========================== WSTĘP  =================================
            # === Czekanie na fraktala DEMA 50 ===
            if waiting_50_down:
                if cooldown_down < 3:
                    cooldown_down += 1
                    continue
                print("waiting down")
                waiting_20_down = False
                new_fractal, fractal_time = fractal(symbol, df)

                if x == "tv":
                    is_open = is_position_open(symbol)
                else:
                    is_open = retry_on_time_error(is_position_open, symbol)
                
                
                print(f"czeka na fractala 50 down dla {symbol}")
                print(f"[DEBUG] is_position_open({symbol}) = {is_open}")
                print(f"new fractal = {new_fractal} next {fractal_time} =! {last_used_fractal_time_down}")


                if (
                    new_fractal == "downFractal"
                    and fractal_time != last_used_fractal_time_down
                    and not retry_on_time_error(is_position_open, symbol)
                ):

                    if fractal_time is None or pd.isna(fractal_time):
                        print(f"[❌ BŁĄD] fractal_time = {fractal_time} → pomijam {symbol}")
                        reset_pullback_down()
                        continue


                    if should_skip_due_to_distance(symbol, current_price, fractal_time, df, "short"):
                        reset_pullback_down()
                        waiting_20_down = False
                        waiting_50_down = False
                        continue

                    if not had_recent_impulse(df, symbol, direction='down', lookback=3):
                        print (f"[RESET] [{datetime.now().strftime('%H:%M')}] dema za blisko dla {symbol}")
                        reset_pullback_down()
                        continue
             

                    print(f"[⏱️] Czekam na nową świecę...")
                    new_candle_time = wait_for_closed_candle(symbol, df.index[-2])

                    df_check = get_futures_klines(symbol, interval='1m', limit=2)
                    df_check = apply_dema_indicators(df_check)
                    df_check = df_check.dropna()

                    current_row = df_check.iloc[-2]


                    last_used_fractal_time_down = fractal_time
                    print(f"[SYGNAŁ] [{datetime.now().strftime('%H:%M')}] downFractal z {fractal_time} — próbuję SHORT na {symbol}")
# endregion
# region ======================== KUPOWANIE  ===============================
# region ====================== TV  ==============================
                    if x == "tv":
                        # Dla TradingView — wizualne otwieranie i wyznaczanie TP/SL
                        chuj = "sell"
                        sl_price = round(df["DEMA_long"].iloc[-1], 2)
                        print(f"sl wedlog petli = {sl_price}")
                        step_size, tick_size = get_symbol_precision(symbol)


                        ai_result = predict_short()

                        print(f"SHORT AI THINKS: {ai_result}")


                        try:
                            tp_price, sl_price = place_futures_order_with_tp_sl_tv(
                                symbol=symbol,
                                quantity=0.5,        # ilość ustawia TradingView automatycznie
                                entry_price=None,     # zostanie odczytany z ekranu
                                sl_price=sl_price,        # zostanie odczytany z ekranu lub wyliczony po fakcie
                                waiting_20=waiting_20,
                                waiting_50=waiting_50,
                                waiting_20_down=waiting_20_down,
                                waiting_50_down=waiting_50_down,
                                df=df,
                                precision=precision,
                                tp_multiplier=tp_multiplier,
                            )
                            reset_pullback_down()
                            print("reset")
                        except Exception as e:
                            print(f"[BŁĄD KRYTYCZNY] [{datetime.now().strftime('%H:%M')}] place_futures_order_with_tp_sl_tv rzucił wyjątek na {symbol}: {e}")
                            reset_pullback_down()
                            continue
# endregion
# region =================== BINANCE  ============================
                    else:
                        chuj = "sell"
                        # Stara logika (API / Binance)
                        sl_price = round(df["DEMA_long"].iloc[-1], 2)
                        entry_price = current_price
                        qty = calculate_dynamic_qty(entry_price, sl_price, symbol)

                        if qty <= 0:
                            print(f"[BŁĄD] Ilość pozycji = {qty} — nie otwieram LONG na {symbol}")
                            reset_pullback_down()
                            continue

                        step_size, tick_size = get_symbol_precision(symbol)
                        qty = round_to_step(qty, step_size)
                        entry_price = round_to_step(entry_price, tick_size)
                        sl_price = round_to_step(sl_price, tick_size)

                        try:
                            tp_price, sl_price = place_futures_order_with_tp_sl(
                                symbol=symbol,
                                side=SIDE_SELL,
                                quantity=qty,
                                entry_price=entry_price,
                                sl_price=sl_price,
                                waiting_20=waiting_20,
                                waiting_50=waiting_50,
                                waiting_20_down=waiting_20_down,
                                waiting_50_down=waiting_50_down,
                                df=df,
                                precision=precision,
                                tp_multiplier=tp_multiplier,
                                opposite=SIDE_BUY,
                                tick_size=tick_size
                                )
                            if tp is not None:
                                print(f"[OTWARTA POZYCJA] [{datetime.now().strftime('%H:%M')}] SHORT {symbol} | TP: {tp} | SL: {sl}")
                                if x == "binance":
                                    start_logical_sl_monitor(symbol, entry_price, sl_price, tp_price)
                                    monitor_tp_sl(symbol, df, entry_price, tp, precision)
                                position = 'SHORT'
                                reset_pullback_down()
                            else:
                                print(f"[BŁĄD] [{datetime.now().strftime('%H:%M')}] Nie udało się otworzyć pozycji SHORT na {symbol}")
                                if x == "binance":    
                                    monitor_tp_sl(symbol, df, entry_price, tp, precision)
                                reset_pullback_down()
                            continue
                        except Exception as e:
                            print(f"[BŁĄD KRYTYCZNY] [{datetime.now().strftime('%H:%M')}] place_futures_order_with_tp_sl rzucił wyjątek na {symbol}: {e}")
                            reset_pullback_down()
                            continue

# endregion
# endregion
# region ====================== WYBICIE ENDING  ============================
                # Odliczanie jeśli cena SPADŁA poniżej DEMA20
                if not dotknieto_50_down and row['high'] > row['DEMA_short']:
                    dotknieto_50_down = True

                if dotknieto_50_down and row['close'] < row['DEMA_short']:
                    wybicie_counter_50_down += 1
                    print(f"[⏱️ WYBICIE 50] [{datetime.now().strftime('%H:%M')}] Pod DEMA50 — {wybicie_counter_50_down}/5 dla {symbol}")
                    if waiting_50_down and row['high'] > row['DEMA_long']:
                        print(f"[RESET] [{datetime.now().strftime('%H:%M')}] Wzrost nad DEMA 100 w czasie waiting_50_down — reset dla {symbol}")
                        reset_pullback_down()
                        waiting_20_down = False
                        waiting_50_down = False
                        wybicie_counter_50_down = 0
                        continue

                    if wybicie_counter_50_down >= 3:
                        print(f"[RESET] [{datetime.now().strftime('%H:%M')}] Wybicie DEMA50 trwa zbyt długo — reset {symbol}")
                        reset_pullback_down()
                        pullback_down_part2 = True
                        continue
                else:
                    wybicie_counter_50_down = 0


                # Reset jeśli DEMA popsute
                if not (row['DEMA_short'] < row['DEMA_medium'] < row['DEMA_long']):
                    print (f"[RESET] [{datetime.now().strftime('%H:%M')}] zła kolejność dema dla {symbol}")
                    reset_pullback_down()
                    continue

                waiting_50_down_counter += 1
                if waiting_50_down_counter >= 10:
                    print(f"[RESET] [{datetime.now().strftime('%H:%M')}] Brak fraktala po DEMA 50 → resetuję {symbol}")
                    reset_pullback_down()
# endregion
# endregion
# region ==================================== WAITING 20  =====================================
# region ========================== WSTĘP  =================================

            # === Czekanie na fraktala DEMA 20 ===
            elif waiting_20_down:
                if cooldown_down < 3:
                    cooldown_down += 1
                    continue
                print("waiting 20 down")
                new_fractal, fractal_time = fractal(symbol, df)

                if x == "tv":
                    is_open = is_position_open(symbol)
                else:
                    is_open = retry_on_time_error(is_position_open, symbol)
            
                print(f"[DEBUG] is_position_open({symbol}) = {is_open}")
                print(f"czeka na fractala 20 down dla {symbol}")
                print(f"new fractal = {new_fractal} next {fractal_time} =! {last_used_fractal_time_down}")


                if (
                    new_fractal == "downFractal"
                    and fractal_time != last_used_fractal_time_down
                    and not retry_on_time_error(is_position_open, symbol)
                ):

                    if fractal_time is None or pd.isna(fractal_time):
                        print(f"[❌ BŁĄD] fractal_time = {fractal_time} → pomijam {symbol}")
                        reset_pullback_down()
                        continue

                    if should_skip_due_to_distance(symbol, current_price, fractal_time, df, "short"):
                        reset_pullback_down()
                        waiting_20_down = False
                        waiting_50_down = False
                        continue

                    if not had_recent_impulse(df, symbol, direction='down', lookback=3):
                        print (f"[RESET] [{datetime.now().strftime('%H:%M')}] dema za blisko dla {symbol}")
                        reset_pullback_down()
                        continue
                

                    print(f"[⏱️] Czekam na nową świecę...")
                    new_candle_time = wait_for_closed_candle(symbol, df.index[-2])

                    df_check = get_futures_klines(symbol, interval='1m', limit=2)
                    df_check = apply_dema_indicators(df_check)
                    df_check = df_check.dropna()

                    current_row = df_check.iloc[-2]

                    
                    last_used_fractal_time_down = fractal_time
                    print(f"[SYGNAŁ] [{datetime.now().strftime('%H:%M')}] downFractal z {fractal_time} — próbuję SHORT na {symbol}")

# endregion
# region ======================== KUPOWANIE  ===============================
# region ====================== TV  ==============================
                    if x == "tv":
                        chuj = "sell"
                        # Dla TradingView — wizualne otwieranie i wyznaczanie TP/SL
                        sl_price = round(df["DEMA_medium"].iloc[-1], 2)
                        print(f"sl wedlog petli = {sl_price}")

                        
                        ai_result = predict_short()

                        print(f"SHORT AI THINKS: {ai_result}")


                        step_size, tick_size = get_symbol_precision(symbol)
                        try:
                            tp_price, sl_price = place_futures_order_with_tp_sl_tv(
                                symbol=symbol,
                                quantity=0.5,        # ilość ustawia TradingView automatycznie
                                entry_price=None,     # zostanie odczytany z ekranu
                                sl_price=sl_price,        # zostanie odczytany z ekranu lub wyliczony po fakcie
                                waiting_20=waiting_20,
                                waiting_50=waiting_50,
                                waiting_20_down=waiting_20_down,
                                waiting_50_down=waiting_50_down,
                                df=df,
                                precision=precision,
                                tp_multiplier=tp_multiplier,
                            )
                            reset_pullback_down()
                            print("reset")
                        except Exception as e:
                            print(f"[BŁĄD KRYTYCZNY] [{datetime.now().strftime('%H:%M')}] place_futures_order_with_tp_sl_tv rzucił wyjątek na {symbol}: {e}")
                            reset_pullback_down()
                            continue
# endregion
# region =================== BINANCE  ============================

                    else:
                        chuj = "sell"
                        # Stara logika (API / Binance)
                        sl_price = round(df["DEMA_medium"].iloc[-1], 2)
                        entry_price = current_price
                        qty = calculate_dynamic_qty(entry_price, sl_price, symbol)

                        if qty <= 0:
                            print(f"[BŁĄD] Ilość pozycji = {qty} — nie otwieram LONG na {symbol}")
                            reset_pullback_down()
                            continue

                        step_size, tick_size = get_symbol_precision(symbol)
                        qty = round_to_step(qty, step_size)
                        entry_price = round_to_step(entry_price, tick_size)
                        sl_price = round_to_step(sl_price, tick_size)

                        try:
                            tp_price, sl_price = place_futures_order_with_tp_sl(
                                symbol=symbol,
                                side=SIDE_SELL,
                                quantity=qty,
                                entry_price=entry_price,
                                sl_price=sl_price,
                                waiting_20=waiting_20,
                                waiting_50=waiting_50,
                                waiting_20_down=waiting_20_down,
                                waiting_50_down=waiting_50_down,
                                df=df,
                                precision=precision,
                                tp_multiplier=tp_multiplier,
                                opposite=SIDE_BUY,
                                tick_size=tick_size
                                )
                            if tp is not None:
                                print(f"[OTWARTA POZYCJA] [{datetime.now().strftime('%H:%M')}] SHORT {symbol} | TP: {tp} | SL: {sl}")
                                if x == "binance":
                                    start_logical_sl_monitor(symbol, entry_price, sl_price, tp_price)
                                    monitor_tp_sl(symbol, df, entry_price, tp, precision)
                                position = 'SHORT'
                                reset_pullback_down()
                            else:
                                print(f"[BŁĄD] [{datetime.now().strftime('%H:%M')}] Nie udało się otworzyć pozycji SHORT na {symbol}")
                                if x == "binance":    
                                    monitor_tp_sl(symbol, df, entry_price, tp, precision)
                                reset_pullback_down()
                            continue
                        except Exception as e:
                            print(f"[BŁĄD KRYTYCZNY] [{datetime.now().strftime('%H:%M')}] place_futures_order_with_tp_sl rzucił wyjątek na {symbol}: {e}")
                            reset_pullback_down()
                            continue
# endregion
# endregion
# region ====================== WYBICIE ENDING  ============================

                # Odliczanie jeśli cena SPADŁA poniżej DEMA20
                if not dotknieto_20_down and row['high'] > row['DEMA_short']:
                    dotknieto_20_down = True

                if dotknieto_20_down and row['close'] < row['DEMA_short']:
                    wybicie_counter_20_down += 1
                    print(f"[⏱️ WYBICIE 20] [{datetime.now().strftime('%H:%M')}] Pod DEMA20 — {wybicie_counter_20_down}/5 dla {symbol}")
                    if wybicie_counter_20_down >= 3:
                        print(f"[RESET] [{datetime.now().strftime('%H:%M')}] Wybicie DEMA20 trwa zbyt długo — reset {symbol}")
                        reset_pullback_down()
                        pullback_down_part2 = True
                        continue
                else:
                    wybicie_counter_20_down = 0


                # Reset jeśli DEMA popsute
                if not (row['DEMA_short'] < row['DEMA_medium'] < row['DEMA_long']):
                    print (f"[RESET] [{datetime.now().strftime('%H:%M')}] zła kolejność dema dla {symbol}")
                    reset_pullback_down()
                    continue

                waiting_20_down_counter += 1
                if waiting_20_down_counter >= 10:
                    print(f"[RESET] [{datetime.now().strftime('%H:%M')}] Brak fraktala po DEMA 20 → resetuję {symbol}")
                    reset_pullback_down()
# endregion
# endregion
# endregion
# region ========================================== EXCEL ===================================================

            position_still_open = False
            for _ in range(5):
                time.sleep(1)
                if not is_position_open(symbol):
                    break
                position_still_open = True

            if not position_still_open and position:
                position = None

                try:
                    df_full = get_futures_klines(symbol, interval='1m', limit=500)
                    df_full = apply_dema_indicators(df_full)
                    df_full = detect_fractals(df_full)
                    df_full = df_full.dropna()

                    df_after = df_full.tail(3)

                    trade_info = active_trades.get(symbol)
                    if trade_info:
                        save_trade_to_excel(
                            symbol=symbol,
                            position_type="LONG" if trade_info["side"] == "BUY" else "SHORT",
                            entry_price=trade_info["entry_price"],
                            sl=trade_info["sl"],
                            tp=trade_info["tp"],
                            df_before=trade_info["df_before"],
                            df_after=df_after
                        )

                except Exception as e:
                    print(f"[EXCEL ERROR] Nie udało się zapisać do Excela dla {symbol}: {e}")

            time.sleep(20)

# endregion

# endregion
# region !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! PO DEF TRADE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

tp_multiplier = 1.5
precision = 2
def start_trade_thread(symbol):
    while True:
        try:
            trade(symbol, tp_multiplier, precision)
        except Exception as e:
            print(f"[THREAD CRASH] {symbol}: {type(e).__name__} — {e}")
            traceback.print_exc()
            print(f"[RESTART] {symbol} → wątek ruszy ponownie za 20s...\n")
            time.sleep(20)

# === URUCHOMIENIE TRADE() Z RESTARTEM ===
threads = []
for symbol in symbols:
    thread = threading.Thread(target=start_trade_thread, args=(symbol,), daemon=True)
    thread.start()
    threads.append(thread)




# === rysuje ===
app = Flask(__name__)
def update_chart(symbol, *args, **kwargs):
    if x == "tv":
        symbol = "BTCUSDT"
        global first_scan_done
        while not first_scan_done:
            time.sleep(1)

    def _draw_chart(df, symbol, entry_price, sl, tp):


        df = apply_dema_indicators(df)

        df, fractal_list = detect_fractals(df)
        df = df.dropna(subset=["DEMA_short", "DEMA_medium", "DEMA_long"])
        if 'upFractal' not in df.columns:
            df['upFractal'] = False
        if 'downFractal' not in df.columns:
            df['downFractal'] = False

        df['upFractal'] = df['upFractal'].where(df['upFractal'].notna(), False).astype(bool)
        df['downFractal'] = df['downFractal'].where(df['downFractal'].notna(), False).astype(bool)
        offset_factor = 0.0005
        sync_fractals_from_df_to_csv(df, csv_path="ohlc_last.csv")

        fig = go.Figure(data=[
            go.Candlestick(
                x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='Candles'
            ),
            go.Scatter(x=df.index, y=df['DEMA_short'], mode='lines', name='DEMA 20', line=dict(color='green')),
            go.Scatter(x=df.index, y=df['DEMA_medium'], mode='lines', name='DEMA 50', line=dict(color='deepskyblue')),
            go.Scatter(x=df.index, y=df['DEMA_long'], mode='lines', name='DEMA 100', line=dict(color='#C9A800')),
            go.Scatter(
                x=df[df['upFractal']].index,
                y=df[df['upFractal']]['low'] * (1 - offset_factor),
                mode='markers',
                name='Fractal UP',
                marker=dict(symbol='triangle-down', color='lime', size=12)
            ),
            go.Scatter(
                x=df[df['downFractal']].index,
                y=df[df['downFractal']]['high'] * (1 + offset_factor),
                mode='markers',
                name='Fractal DOWN',
                marker=dict(symbol='triangle-up', color='red', size=12)
            ),
        ])

        # 🔹 Dodaj linie SL / TP / ENTRY
        if sl is not None:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=[sl] * len(df),
                mode='lines',
                name='SL',
                line=dict(color='red', width=1.5, dash='dash')
            ))

        if tp is not None:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=[tp] * len(df),
                mode='lines',
                name='TP',
                line=dict(color='green', width=1.5, dash='dash')
            ))

        if entry_price is not None:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=[entry_price] * len(df),
                mode='lines',
                name='ENTRY',
                line=dict(color='blue', width=1.5, dash='dot')
            ))

        fig.update_layout(
            title=f"{symbol} — Live Chart",
            xaxis_title='Time',
            yaxis_title='Price',
            xaxis_rangeslider_visible=False
        )


        y_values = [
            df['low'].min(),
            df['high'].max()
        ]

        if entry_price is not None:
            y_values.append(entry_price)
        if sl is not None:
            y_values.append(sl)
        if tp is not None:
            y_values.append(tp)

        fig.update_yaxes(range=[min(y_values), max(y_values)])

        folder_path = os.path.join('static', symbol)
        os.makedirs(folder_path, exist_ok=True)
        chart_path = os.path.join(folder_path, 'chart.html')
        fig.write_html(chart_path)

    # ================= TV =================
    if x == "tv":
        while True:
            try:
                df = get_futures_klines_tv(
                    symbol=symbol,
                    interval="1m",
                    limit=10000,
                    path=SAVE_PATH
                )
            except Exception as e:
                print(f"[TV] Błąd get_futures_klines_tv: {e}")
                time.sleep(60)
                continue

            if df is None or df.empty:
                print(f"[TV] Brak danych w {SAVE_PATH}")
                time.sleep(60)
                continue

            # ⬇️ OD TEGO MOMENTU UŻYWASZ TYLKO TEGO df
            entry_price = sl = tp = None
            result = None

            # ─────────────────────────────────────────────
            # TYLKO GDY POZYCJA OTWARTA
            # ─────────────────────────────────────────────
            if is_position_open(symbol):

                print(f"[DEBUG] 🟢 Pozycja OTWARTA dla {symbol}")

                result = load_last_trade_from_csv("ohlc_last.csv")
                print("[DEBUG] CSV result:", result)

                if isinstance(result, dict):
                    try:
                        entry_price = float(result["entry"])
                        sl = float(result["sl"])
                        tp = float(result["tp"])

                        print(
                            f"[FINAL CHECK] "
                            f"ENTRY={entry_price} ({type(entry_price)}), "
                            f"SL={sl} ({type(sl)}), "
                            f"TP={tp} ({type(tp)})"
                        )

                    except (KeyError, TypeError, ValueError) as e:
                        print(f"[ERROR] Nieprawidłowe dane w CSV: {e}")
                        entry_price = sl = tp = None

                else:
                    print_once("[⚠️] Brak poprawnych danych trade w CSV")


            # ─────────────────────────────────────────────
            # 3️⃣ RYSOWANIE (ODDZIELNY TRY)
            # ─────────────────────────────────────────────
            try:
                _draw_chart(df, symbol, entry_price, sl, tp)
            except Exception as e:
                print(f"[ERROR] _draw_chart wyjątek: {e}")


            time.sleep(60)


    # ================= BINANCE =================
    else:
        print("działa binance")
        last_drawn_candle = None
        last_checked_candle_chart = None

        while True:
            if last_checked_candle_chart is None:
                df_init = get_futures_klines(symbols[0], interval='1m', limit=3)
                df_init.index = pd.to_datetime(df_init.index)
                last_checked_candle_chart = df_init.index[-2]

            candle_time = wait_for_closed_candle(symbols[0], last_checked_candle_chart)

            if candle_time == last_checked_candle_chart:
                time.sleep(1)
                continue

            last_checked_candle_chart = candle_time

            if candle_time == last_drawn_candle:
                time.sleep(1)
                continue

            last_drawn_candle = candle_time

            for symbol in symbols:
                try:
                    df = get_df_for_chart(symbol, limit=500)
                    df = df[df.index <= candle_time].copy()
                    df = df.dropna()
                    print("działa binance")

                    # Tworzenie wykresu
                    fig = go.Figure(data=[
                        go.Candlestick(
                            x=df.index,
                            open=df['open'],
                            high=df['high'],
                            low=df['low'],
                            close=df['close'],
                            name='Candles'
                        )
                    ])

                    # DEMA (jeśli istnieją)
                    for col, color, name in [
                        ("DEMA_short", "green", "DEMA 20"),
                        ("DEMA_medium", "deepskyblue", "DEMA 50"),
                        ("DEMA_long", "#C9A800", "DEMA 100")
                    ]:
                        if col in df.columns:
                            fig.add_trace(go.Scatter(x=df.index, y=df[col], mode="lines", name=name, line=dict(color=color)))

                    # Fractale
                    offset_factor = 0.002  # np. 0.2%
                    if "upFractal" in df.columns:
                        fig.add_trace(go.Scatter(
                            x=df.loc[df["upFractal"]].index,
                            y=df.loc[df["upFractal"], "low"] * (1 - offset_factor),
                            mode="markers",
                            name="Fractal UP",
                            marker=dict(symbol="triangle-down", color="lime", size=12)
                        ))

                    if "downFractal" in df.columns:
                        fig.add_trace(go.Scatter(
                            x=df.loc[df["downFractal"]].index,
                            y=df.loc[df["downFractal"], "high"] * (1 + offset_factor),
                            mode="markers",
                            name="Fractal DOWN",
                            marker=dict(symbol="triangle-up", color="red", size=12)
                        ))

                    # SL / TP / ENTRY
                    if sl is not None:
                        fig.add_trace(go.Scatter(
                            x=df.index,
                            y=[sl] * len(df),
                            mode="lines",
                            name="SL",
                            line=dict(color="red", width=1.5, dash="dash")
                        ))

                    if tp is not None:
                        fig.add_trace(go.Scatter(
                            x=df.index,
                            y=[tp] * len(df),
                            mode="lines",
                            name="TP",
                            line=dict(color="green", width=1.5, dash="dash")
                        ))

                    if entry_price is not None:
                        fig.add_trace(go.Scatter(
                            x=df.index,
                            y=[entry_price] * len(df),
                            mode="lines",
                            name="ENTRY",
                            line=dict(color="blue", width=1.5, dash="dot")
                        ))

                    # Layout
                    fig.update_layout(
                        title=f"{symbol} — Live Chart",
                        xaxis_title="Time",
                        yaxis_title="Price",
                        xaxis_rangeslider_visible=False
                    )

                    # Zapis wykresu
                    folder_path = os.path.join("static", symbol)
                    os.makedirs(folder_path, exist_ok=True)
                    chart_path = os.path.join(folder_path, "chart.html")
                    fig.write_html(chart_path)


                except Exception as e:
                    print(f"[BŁĄD CHARTU] {symbol} → {e}")

            time.sleep(20)



def load_last_trade_from_csv(path):
    try:
        df_csv = pd.read_csv(path)
        if df_csv.empty:
            return None
        last = df_csv.iloc[-1]   # 🔥 NAJNIŻSZY WIERSZ
        return {
            "entry": last.get("entry"),
            "sl": last.get("sl"),
            "tp": last.get("tp"),
        }
    except Exception as e:
        print(f"[CSV ERROR] {e}")
        return None

@app.route('/ohlc_tv', methods=['GET'])
def ohlc_tv():
    try:
        return send_file(
            "ohlc_last.csv",
            mimetype="text/csv",
            as_attachment=False
        )
    except Exception as e:
        return f"Błąd odczytu CSV: {e}", 500
@app.route('/ohlc_last', methods=['GET'])
def ohlc_last():
    try:
        return send_file(
            "ohlc_last.csv",
            mimetype="text/csv",
            as_attachment=False  # jeśli True → pobieranie, jeśli False → podgląd w przeglądarce
        )
    except Exception as e:
        return f"Błąd odczytu CSV: {e}", 500
@app.route('/')
def home():
    return '''
    <html>
        <head><title>Wykresy</title></head>
        <body>
            <h1>Wybierz wykres</h1>
            <ul>
                <li><a href="/chart/BTCUSDT">BTCUSDT</a></li>
                <li><a href="/chart/ETHUSDT">ETHUSDT</a></li>
                <li><a href="/chart/SOLUSDT">SOLUSDT</a></li>
            </ul>

            <h2>Dane OHLC z CSV</h2>
            <ul>
                <li><a href="/ohlc_last">Podgląd ohlc_last.csv</a></li>
            </ul>
        </body>
    </html>
    '''


def enable_tv_mode():
    print("[TV] Tryb TV aktywny: dane z OCR (TradingView).")

    globals()['get_futures_klines'] = get_futures_klines_tv
    globals()['refresh_df_and_indicators'] = refresh_df_and_indicators_tv
    globals()['wait_for_closed_candle'] = wait_for_closed_candle_tv_safe
    globals()['place_futures_order_with_tp_sl'] = place_futures_order_with_tp_sl_tv
    globals()['close_position'] = close_position_tv

    # Na starcie pełny skan

    tv_symbol = "BTCUSDT"
    threading.Thread(target=trade, args=(tv_symbol, 1.5, 2), daemon=True).start()

if x == "tv":
    enable_tv_mode()
else:
    print("[BINANCE] Tryb binance — bez zmian (API).")

@app.route('/chart/<symbol>')
def serve_chart_for_symbol(symbol):
    path = os.path.join('static', symbol, 'chart.html')
    if not os.path.exists(path):
        return f'Brak wykresu dla {symbol}', 404
    return send_file(path)

entry_price = None
sl = None
tp = None
# Start wątku generującego wykres
chart_thread = threading.Thread(target=update_chart, args=(symbol))
chart_thread.daemon = True
chart_thread.start()


def get_ohlc_by_time(hour_min_str, csv_path="ohlc_last.csv"):
    """
    Pozwala po wpisaniu np. '19.20' zobaczyć wartości OHLC z pliku ohlc_last.csv.
    """
    try:
        df = pd.read_csv(csv_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df.dropna(subset=['timestamp'], inplace=True)

        # Format wejściowy np. "19.20" lub "19:20"
        hour_min_str = hour_min_str.replace(":", ".")
        hour, minute = hour_min_str.split(".")
        hour, minute = int(hour), int(minute)

        # Filtr
        match = df[df['timestamp'].dt.hour.eq(hour) & df['timestamp'].dt.minute.eq(minute)]

        if match.empty:
            print(f"[⚠️] Brak świecy o godzinie {hour:02d}:{minute:02d}")
            return None
        else:
            row = match.iloc[-1]
            return row

    except Exception as e:
        print(f"[❌ BŁĄD] Nie udało się odczytać OHLC: {e}")
        return None
if __name__ == "__main__":
    if x == "tv":
        threading.Thread(target=watch_pixel, daemon=True).start()
        print("[🚀] Najpierw pełny first_scan...")
        first_scan()
        # ustaw flagę, żeby zegar i reszta mogły ruszyć
        first_scan_done = True
        print("[✅] First scan zakończony!")
    # teraz dopiero wątki
    df = pd.read_csv("ohlc_last.csv")
    threading.Thread(target=training, daemon=True).start()
    print_once("odziwo działa")


    threads = []
    for symbol in symbols:
        thread = threading.Thread(target=start_trade_thread, args=(symbol,), daemon=True)
        thread.start()
        threads.append(thread)
        precision = 2
        tp_multiplier = 1.5
        t = Thread(target=trade, args=(symbol, tp_multiplier, precision), daemon=True)
        t.start()
    app.run(host="0.0.0.0", port=5050, debug=False)
#=== testnet ===
while True:
    for symbol in symbols:
        try:
            pos = "OPEN" if retry_on_time_error(is_position_open, symbol) else "None"
        except requests.exceptions.ReadTimeout:
            print(f"[TIMEOUT] Timeout przy sprawdzaniu pozycji {symbol}.")
            pos = "Brak danych"
        time.sleep(20)


# endregion
