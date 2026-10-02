import time
import re
import os
from decimal import Decimal
from datetime import datetime, timedelta

import numpy as np
import cv2
import pytesseract
from PIL import Image
import mss
import pyautogui
import cv2

# ------- Ustawienia (dostosuj) -------
# Jeśli masz niestandardową ścieżkę do tesseract:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Globalne (tak jak w dema.py)
chuj = None
cw = False
mask_red = None
mask_blue = None
mask_all = None

# ------- Pomocnicze funkcje (zachowanie jak w dema.py) -------

def do_action(*args, save_path="screenshot.png"):
    """
    Jeżeli podano 2 argumenty -> klik (x, y)
    Jeżeli podano 4 argumenty -> screenshot (left, top, right, bottom)
    Zwraca Image obiektu PIL przy screenshot.
    """
    if len(args) == 2:
        x, y = args
        print(f"[do_action] klik ({x},{y})")
        pyautogui.moveTo(x, y)
        pyautogui.click()
        return None
    elif len(args) == 4:
        left, top, right, bottom = args
        width = right - left
        height = bottom - top
        print(f"[do_action] screenshot area {left},{top},{right},{bottom} -> {save_path}")
        with mss.mss() as sct:
            monitor = {"left": left, "top": top, "width": width, "height": height}
            shot = sct.grab(monitor)
            img = Image.frombytes("RGB", shot.size, shot.rgb)
            img.save(save_path)
            return img
    else:
        raise ValueError("do_action: podaj 2 (klik) lub 4 (screenshot) argumenty")


def round_to_step(value, step):
    try:
        if value is None:
            raise ValueError("value is None")
        step = Decimal(str(step))
        return float((Decimal(str(value)) // step) * step)
    except Exception as e:
        print(f"[round_to_step ERROR] value: {value}, step: {step} | {e}")
        raise


def calculate_dynamic_qty(entry_price, sl_price, symbol, leverage=20, safety_factor=0.95):
    # Kopia prostej logiki z dema.py (u Ciebie jest stały available_usdt)
    MAX_RISK_USDT = 30
    try:
        diff = abs(float(entry_price) - float(sl_price))
        if diff == 0:
            print("[calculate_dynamic_qty] odległość SL = 0 -> zwracam 0")
            return 0.0
        qty = MAX_RISK_USDT / diff
        available_usdt = 1000.0  # dostosuj / nadpisz ręcznie jeśli trzeba
        usable = available_usdt * safety_factor
        max_pos_val = usable * leverage
        max_qty = max_pos_val / float(entry_price)
        if qty > max_qty:
            qty = round(max_qty / 2, 6)
        return qty
    except Exception as e:
        print(f"[calculate_dynamic_qty ERROR] {e}")
        return 0.0


def detect_longest_horizontal_line(mask, image, color_name=None,
                                   y_threshold=1000,
                                   offset_x=-1920,
                                   offset_y=0,
                                   screenshot_height=1080,
                                   screen_height=1349):
    """
    Wykrywa najdłuższą poziomą linię w masce.
    Automatycznie przelicza pozycję kliknięcia z przestrzeni obrazu (screenshot)
    na przestrzeń ekranu (z uwzględnieniem skalowania DPI w Windows).
    """

    try:
        # 1️⃣ Wykrywanie krawędzi i linii
        edges = cv2.Canny(mask, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180,
                                threshold=100, minLineLength=100, maxLineGap=10)

        max_length = 400
        longest_line = None

        if lines is not None:
            for l in lines:
                x1, y1, x2, y2 = l[0]
                length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                if abs(y2 - y1) < 5 and y1 < y_threshold:
                    if length > max_length:
                        max_length = length
                        longest_line = (x1, y1, x2, y2)

        if not longest_line:
            print("[⚠️] Nie znaleziono żadnej linii spełniającej warunki.")
            return None

        # 2️⃣ Najdłuższa linia
        x1, y1, x2, y2 = longest_line
        mid_x = int((x1 + x2) / 2)
        mid_y = int((y1 + y2) / 2)

        # 3️⃣ Rysowanie (debug)
        color = (0, 255, 0)
        if color_name == "blue":
            color = (255, 0, 0)
        elif color_name == "red":
            color = (0, 0, 255)
        cv2.line(image, (x1, y1), (x2, y2), color, 2)

        # 4️⃣ Przeliczenie skali (screenshot → ekran logiczny)
        scale_y = screen_height / screenshot_height
        scale_x = screen_height / screenshot_height  # zakładamy proporcje 1:1
        scaled_x = int(mid_x * scale_x)
        scaled_y = int(mid_y * scale_y)

        # 5️⃣ Dodanie offsetu monitora
        screen_x = scaled_x + offset_x
        screen_y = scaled_y + offset_y

        # 6️⃣ Logi
        print(f"[INFO] Linia (obraz): ({x1},{y1}) -> ({x2},{y2}), środek=({mid_x},{mid_y})")
        print(f"[INFO] Skalowanie: {screenshot_height}→{screen_height} (x{scale_y:.3f})")
        print(f"[INFO] Klik na ekranie: ({screen_x}, {screen_y}) [offset=({offset_x},{offset_y})]")

        # 7️⃣ Kliknięcie
        time.sleep(1)
        pyautogui.moveTo(screen_x, screen_y, duration=0.5)
        pyautogui.click()
        print("[ACTION] Kliknięto w środek najdłuższej linii ✅")

        return (x1, y1, x2, y2)

    except Exception as e:
        print(f"[detect_longest_horizontal_line ERROR] {e}")
        return None

def read_number_from_image(image_path):
    """
    OCR z obrazu - staramy się wyciągnąć liczbę (float).
    Zwraca float lub None.
    """
    try:
        if not os.path.exists(image_path):
            print(f"[read_number_from_image] brak pliku {image_path}")
            return None
        img = cv2.imread(image_path)
        if img is None:
            print(f"[read_number_from_image] cv2.imread zwróciło None dla {image_path}")
            return None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # opcjonalne threshold / denoise można dodać jeśli potrzeba
        config = r'--psm 7 -c tessedit_char_whitelist=0123456789.,'
        text = pytesseract.image_to_string(gray, config=config)
        text = text.strip().replace(",", ".")
        # znajdź pierwszą liczbę
        m = re.search(r"(-?\d+\.\d+|-?\d+)", text)
        if m:
            try:
                return float(m.group(0))
            except:
                return None
        return None
    except Exception as e:
        print(f"[read_number_from_image ERROR] {e}")
        return None


def sl_tp(df, side="SELL", sl_price=None, tp_multiplier=1.5, tick_size=0.01):
    """
    Prosty kalkulator entry/sl/tp - w Twoim oryginale entry = ostatnia cena,
    ale tutaj użyjemy danych wejściowych / lub symulacji.
    Dla testu funkcja powinna zwrócić dict {"entry":..., "sl":..., "tp":...}
    """
    # jeżeli df zawiera entry itp., możesz to zmienić; tu przyjmujemy że caller
    # wstrzyknął entry/sl/tp w argumentach funkcji głównej (przekazujemy je wtedy jako df)
    try:
        # Jeśli df to dict z wartościami -> użyj
        if isinstance(df, dict) and "entry" in df:
            entry = float(df["entry"])
            sl = float(df["sl"])
            tp = float(df["tp"])
            return {"entry": entry, "tp": tp, "sl": sl}
        # Domyślne symulowane
        entry = 114385.2
        if side.lower() == "buy":
            tp = entry + 500.0
            sl = entry - 500.0
        else:
            tp = entry - 500.0
            sl = entry + 500.0
        return {"entry": entry, "tp": tp, "sl": sl}
    except Exception as e:
        print(f"[sl_tp ERROR] {e}")
        return None


# ------- Główna funkcja skopiowana i poprawiona -------

def place_futures_order_with_tp_sl_tv(symbol, side, quantity, entry_price, sl_price,
                                      waiting_20, waiting_50, waiting_20_down, waiting_50_down,
                                      df, precision, tp_multiplier, opposite, tick_size):
    """
    Standalone wersja funkcji z dema.py, dopasowana do testów.
    Przyjmuje entry_price, sl_price, tp_price (opcjonalnie w df jako dict).
    Wykonuje screenshoty, OCR, detekcję linii i przesunięcia myszki.
    """
    global chuj, cw, mask_red, mask_blue, mask_all
    cw = False

    def unpack_if_tuple(val, name, index=0):
        if isinstance(val, tuple):
            print(f"[⚠️] {name} przekazane jako tuple: {val} — biorę element {index}")
            return val[index]
        return val

    # Rozpakowanie potencjalnych tuple-ów
    entry_price = unpack_if_tuple(entry_price, "entry_price", 0)
    sl_price = unpack_if_tuple(sl_price, "sl_price", 0)
    tp_multiplier = unpack_if_tuple(tp_multiplier, "tp_multiplier", 0)

    if isinstance(tick_size, tuple):
        tick_size = unpack_if_tuple(tick_size, "tick_size", 1 if len(tick_size) > 1 else 0)
    else:
        tick_size = unpack_if_tuple(tick_size, "tick_size")

    # Jeśli df jest dict zawierający entry/sl/tp to potraktuj go jako źródło
    result = sl_tp(df, side=side, sl_price=sl_price, tp_multiplier=tp_multiplier, tick_size=tick_size)
    if not result:
        print("[❌] sl_tp nie zwróciło wartości – przerywam.")
        return None

    # Priorytet: jeśli caller przekazał jawnie entry_price / sl_price (np. z CLI),
    # to użyj ich zamiast sl_tp result — to było Twoje wymaganie.
    if entry_price is None and "entry" in result:
        entry_price = float(result["entry"])
    else:
        entry_price = float(entry_price)

    if sl_price is None and "sl" in result:
        sl_price = float(result["sl"])
    else:
        sl_price = float(sl_price)

    # jeśli result ma tp -> użyj, ale caller może też podać tp w df (result)
    tp_price = float(result.get("tp", entry_price + tp_multiplier * abs(entry_price - sl_price)))

    # Debug
    print(f"[DEBUG] ENTRY={entry_price}, SL={sl_price}, TP={tp_price}, side={side}, tick_size={tick_size}, tp_mult={tp_multiplier}")

    # wpisz ilość pozycji (tak jak w oryginale)
    do_action(-2170, 160)
    time.sleep(0.3)
    for _ in range(10):
        pyautogui.press("backspace")
        time.sleep(0.05)
    qty = calculate_dynamic_qty(entry_price, sl_price, symbol)
    print(f"[INFO] Obliczona qty = {qty}")
    pyautogui.write(str(qty), interval=0.05)
    time.sleep(0.5)

    # klik BUY/SELL - w oryginale chuj zmieniał się z otoczenia; tutaj ustawiamy globalnie
    chuj = side.lower()
    if chuj == "buy":
        do_action(-2120, 150)
        time.sleep(0.5)
    elif chuj == "sell":
        print("zjebalem")
        do_action(-2250, 160)
        time.sleep(0.5)

    print("[INFO] symulowane kupno (klik) wykonane")
    time.sleep(5)

    # zrób screenshot całego ekranu (możesz dopasować obszar)
    # tutaj bierzemy prosty pełny screenshot dla testu
    do_action(0, 0, 1920, 1080, save_path="twoje_zdjecie.jpg")
    # w oryginale funkcja robi to przy pomocy mss i zapisuje do pliku
    image = cv2.imread("twoje_zdjecie.jpg")
    if image is None:
        print("[❌] Nie udało się wczytać obrazu twoje_zdjecie.jpg")
        return None

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # maski kolorów jak w oryginale
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

    # detekcja linii
    y_line_tuple = detect_longest_horizontal_line(mask_all, image)
    if not y_line_tuple:
        print("[⚠️] Nie wykryto linii (mask_all) — przerywam.")
        return None
    y_line = y_line_tuple[1]
    print(f"[INFO] Wykryta linia y = {y_line}")
    time.sleep(1)

    # Rysowanie linii TP/SL (opcjonalnie)
    if chuj == "buy":
        detect_longest_horizontal_line(mask_blue, image, "blue")
    if chuj == "sell":
        detect_longest_horizontal_line(mask_red, image, "red")

    cw = True
    print("[INFO] przygotowania zakończone, przechodzę do OCR i obliczeń")
    time.sleep(2)

    # Zrzuty obszarów do OCR (tu użyjemy przykładowych boxów; dopasuj do siebie)
    do_action(-500, 201)
    do_action(0, 150, 200, 170, save_path="gorny.png")
    time.sleep(2)
    do_action(-500, 1029)
    do_action(0, 810, 270, 900, save_path="dolny.png")
    time.sleep(2)

    print("[INFO] Robię OCR górny/dolny...")
    time.sleep(1)
    xup = read_number_from_image("gorny.png")
    xdown = read_number_from_image("dolny.png")
    print(f"[DEBUG] xup={xup}, xdown={xdown}")

    if xup is None or xdown is None:
        print("[⚠️] Nie udało się odczytać xup/xdown — przerywam")
        return None

    # Obliczenia pikselowe
    px = (xup - xdown) / 828.0
    px_sl = (entry_price - sl_price) / px
    px_tp = (tp_price - entry_price) / px
    print(f"[DEBUG] px={px}, px_sl={px_sl}, px_tp={px_tp}")
    time.sleep(1)

    # Bezpieczeństwo typów i debug
    if isinstance(y_line, tuple):
        print("[FIX] y_line było tuple — biorę drugi element")
        y_line = y_line[1]
    try:
        y_line = float(y_line)
        px_tp = float(px_tp) + 20
        px_sl = float(px_sl) + 20
    except Exception as e:
        print(f"[ERROR] konwersja typów: {e}")
        return None
       
    scale_y = 1349 / 1080
    real_y = y_line * scale_y

    # Ruchy myszką - BUY
    if chuj == "buy":
        px_tp *= -1
        print(f"[ACTION] moveTo(-765, {real_y}) then dragRel(0, {px_tp})")
        pyautogui.moveTo(-765, real_y, duration=0.2)
        pyautogui.dragRel(0, px_tp, duration=0.2, button='left')
        print(f"[ACTION] moveTo(-715, {real_y}) then dragRel(0, {px_sl})")
        pyautogui.moveTo(-715, real_y, duration=0.2)
        pyautogui.dragRel(0, px_sl, duration=0.2, button='left')

    # Ruchy myszką - SELL
    if chuj == "sell":
        px_sl *= -1
        print(f"[ACTION] moveTo(-765, {real_y}) then dragRel(0, {px_tp})")
        pyautogui.moveTo(-765, real_y, duration=0.2)
        pyautogui.dragRel(0, px_tp, duration=0.2, button='left')

        print(f"[ACTION] moveTo(-715, {real_y}) then dragRel(0, {px_sl} * -1)")
        pyautogui.moveTo(-725, real_y, duration=0.2)
        pyautogui.dragRel(0, px_sl, duration=0.2, button='left')
    print("[✅] Zakończono place_futures_order_with_tp_sl_tv (test) — zwracam TP i SL")
    return tp_price, sl_price


# ------- Wywołanie testowe (możesz zmienić wartości) -------
if __name__ == "__main__":
    # 🔹 Ustawienia testowe
    entry = 114385.2  # główna wartość ENTRY
    side = "sell"       # zmień na "sell" jeśli chcesz testować shorta
    tp_mult = 1.5

    # 🔹 Automatyczne obliczenie SL i TP
    if side == "buy":
        sl = entry - 500
        tp = entry + 500
    else:
        sl = entry + 500
        tp = entry - 500

    print(f"[TEST START] ENTRY={entry}, SL={sl}, TP={tp}")

    # 🔹 Wywołanie funkcji testowej
    tp_price, sl_price = place_futures_order_with_tp_sl_tv(
        symbol="BTCUSDT",
        side=side,
        quantity=0.01,
        entry_price=entry,
        sl_price=sl,
        waiting_20=None,
        waiting_50=None,
        waiting_20_down=None,
        waiting_50_down=None,
        df=None,  # df niepotrzebne, bo podajemy wartości jawnie
        precision=2,
        tp_multiplier=tp_mult,
        opposite=False,
        tick_size=0.01
    )

    print(f"[TEST END] zwrócono: TP={tp_price} SL={sl_price}")