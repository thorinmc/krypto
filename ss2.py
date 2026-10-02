import time
import pyautogui
from PIL import Image
import mss
import os
import re

# Obszar do screenshotów
OHLC_BOX = (-1460, 90, -1166, 110)

# Ścieżka do zapisu
SAVE_DIR = r"C:\Users\iwojc\OneDrive\Pulpit\binance-dema-bot\ohlc_dataset\images"
os.makedirs(SAVE_DIR, exist_ok=True)

# Zakres ruchu myszką
START_X = -430
END_X = -1815
Y_POS = 200

def get_start_counter():
    """Sprawdza istniejące pliki i zwraca numer startowy kolejnego pliku."""
    files = os.listdir(SAVE_DIR)
    nums = []
    for f in files:
        match = re.match(r"ohlc_(\d{4})\.png", f)
        if match:
            nums.append(int(match.group(1)))
    return max(nums, default=0) + 1

def scan_with_mouse():
    with mss.mss() as sct:
        counter = get_start_counter()
        try:
            for x in range(START_X, END_X - 1, -1):  # krok co 4px w lewo
                pyautogui.moveTo(x, Y_POS)

                # Screenshot wybranego obszaru
                left, top, right, bottom = OHLC_BOX
                width = right - left
                height = bottom - top
                monitor = {"left": left, "top": top, "width": width, "height": height}
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

                # Zapis z numeracją
                filename = os.path.join(SAVE_DIR, f"ohlc_{counter:04d}.png")
                img.save(filename)
                print(f"[📸] Zapisano {filename}")
                counter += 1

                time.sleep(0.05)  # króciutka pauza

        except KeyboardInterrupt:
            print("\n[⏹] Przerwano skanowanie przez Ctrl+C!")

if __name__ == "__main__":
    time.sleep(2)  # chwila na ustawienie panelu
    scan_with_mouse()