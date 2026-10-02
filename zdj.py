import pyscreenshot as ImageGrab
from PIL import Image
import pyautogui
import time

# współrzędne piksela na ekranie (np. 100, 200)
x = 220
y = 135

# zrób screenshot całego ekranu
img = ImageGrab.grab()  # typ: PIL.Image

width, height = img.size
print(f"Rozmiar ekranu: {width}x{height}")

if 0 <= x < width and 0 <= y < height:
    r, g, b = img.getpixel((x, y))
    print(f"Pozycja: x={x}, y={y}")
    print(f"RGB: ({r}, {g}, {b})")
    hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b)
    print(f"HEX: {hex_color}")
else:
    print("Podane współrzędne są poza ekranem.")

def do_action(*args, save_path="screenshot.png"):
    """
    args:
      - (x, y) -> klik w punkt (LPM)
      - (left, top, right, bottom) -> screenshot obszaru

    Implementacja tylko na bazie pyautogui (bez mss),
    dzięki czemu omijamy XGetImage() failed.
    """
    # 🔹 2 argumenty → klik
    if len(args) == 2:
        x, y = args
        pyautogui.click(x=x, y=y)
        print(f"[🖱] Kliknięto punkt: ({x}, {y})")
        return

    # 🔹 4 argumenty → screenshot
    elif len(args) == 4:
        left, top, right, bottom = args

        # pyautogui.screenshot używa (left, top, width, height)
        width = right - left
        height = bottom - top

        if width <= 0 or height <= 0:
            print(f"[❌] Nieprawidłowy obszar screena: left={left}, top={top}, right={right}, bottom={bottom}")
            return None

        try:
            img = pyautogui.screenshot(region=(left, top, width, height))
        except Exception as e:
            print(f"[❌] ScreenshotError (pyautogui): {e} dla regionu {(left, top, width, height)}")
            return None

        img.save(save_path)
        print(f"[📸] Zapisano screenshot: {save_path} (region: left={left}, top={top}, width={width}, height={height})")
        return img

    else:
        raise ValueError(
            "Podaj 2 liczby (x, y) dla kliknięcia albo 4 liczby (left, top, right, bottom) dla screena."
        )


# 🔹 przykłady użycia (odkomentuj co potrzebujesz):
if hex_color.lower() == "#0f0f0f":
    do_action(1575, 900)
    do_action(220, 1055)
    do_action(220, 1005)
    do_action(1570, 700)