import cv2
import numpy as np
import pyautogui
import mss
from PIL import Image
import time
import os
import pytesseract

#(-2170, 160) ilość kupowana
kys = False

x = "sell"



def do_action(*args, save_path="screenshot.png"):
    """
    args:
      - (x, y) -> klik w punkt
      - (left, top, right, bottom) -> screenshot
    """
    if len(args) == 2:  # klik
        if kys:
            x, y = args
            pyautogui.moveTo(x, y)
            print(f"[🖱] Kliknięto punkt: ({x}, {y})")
        else:
            x, y = args
            pyautogui.click(x, y)
            print(f"[🖱] Kliknięto punkt: ({x}, {y})")

    elif len(args) == 4:  # screenshot
        left, top, right, bottom = args
        width = right - left
        height = bottom - top

        with mss.mss() as sct:
            monitor_area = {
                "left": left,
                "top": top,
                "width": width,
                "height": height
            }
            screenshot = sct.grab(monitor_area)
            img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            img.save(save_path)
            print(f"[📸] Zapisano screenshot: {save_path}")
            return img

    else:
        raise ValueError("Podaj 2 liczby (x, y) dla kliknięcia albo 4 liczby (left, top, right, bottom) dla screena.")




#kup sprzedaj
if x == "buy":
    do_action(-2120, 150)
if x == "sell":
    do_action(-2250, 160)
time.sleep(2)

do_action(-1920, 0, 0, 1080, save_path="twoje_zdjecie.jpg")  # screenshot



# Wczytaj obraz
image = cv2.imread("twoje_zdjecie.jpg")
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

# Minimalna wysokość linii (10 px wyżej niż y=1032)
y_threshold = 1032 - 10  # 1022

# Funkcja do wykrywania najdłuższej linii poziomej powyżej y_threshold
def detect_longest_horizontal_line(mask, image, color_name, y_threshold):
    edges = cv2.Canny(mask, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)
    
    min_length_required = 500  # minimalna długość linii
    max_length = 0
    longest_line = None
    
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            # Sprawdzamy, czy linia jest prawie pozioma, powyżej progu i ma długość >= 500 px
            length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            if abs(y2 - y1) < 5 and y1 < y_threshold and y2 < y_threshold and length >= min_length_required:
                if length > max_length:
                    max_length = length
                    longest_line = (x1, y1, x2, y2)
    
    if longest_line is not None:
        x1, y1, x2, y2 = longest_line
        # Rysujemy tylko najdłuższą linię
        if color_name == "blue":
            cv2.line(image, (x1, y1), (x2, y2), (255, 0, 0), 2)
        elif color_name == "red":
            cv2.line(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
        print(f"{color_name} longest line above y={y_threshold}: ({x1}, {y1}) -> ({x2}, {y2}), length: {max_length:.2f}")
    else:
        print(f"No {color_name} line found above y={y_threshold} with length >= {min_length_required}px")

# Wykrywamy najdłuższe linie powyżej progu
detect_longest_horizontal_line(mask_blue, "blue")
detect_longest_horizontal_line(mask_red, "red")

kys = True
do_action(-500, 201)
do_action(-340, 150, -270, 170, save_path="gorny.png")
do_action(-500, 1029)
do_action(-340, 810, -270, 840, save_path="dolny.png")








def fix_number(num_str):
    """Konwersja stringa na float, jeśli zawiera kropkę"""
    try:
        return float(num_str)
    except:
        return None

def read_number_from_image(image_path):
    if not os.path.exists(image_path):
        print(f"[⚠️] Brak pliku {image_path} – nic nie zwracam.")
        return None

    img = Image.open(image_path)
    # Zakładamy, że na obrazie tylko cyfry i przecinki
    custom_config = r'--psm 6 -c tessedit_char_whitelist=0123456789,'
    text = pytesseract.image_to_string(img, config=custom_config)

    # Zamiana przecinka na kropkę
    text = text.replace(",", ".").strip()

    try:
        number = float(text)
    except:
        print(f"[⚠️] Nie udało się przekonwertować '{text}' na float")
        return None

    return number

# Odczyt z gorny.png i dolny.png
xup = read_number_from_image("gorny.png")
xdown = read_number_from_image("dolny.png")

print(f"xup = {xup}")
print(f"xdown = {xdown}")