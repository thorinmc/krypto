import cv2
import numpy as np
import mss
from PIL import Image
import pyautogui
import time
import os
import pytesseract

def do_action(*args, save_path="screenshot.png"):
    """
    args:
      - (x, y) -> klik w punkt
      - (left, top, right, bottom) -> screenshot
    """
    if len(args) == 2:  # klik
        x, y = args
        pyautogui.moveTo(x, y)
        print(f"[🖱] poszedł do punktu: ({x}, {y})")

    elif len(args) == 4:  # screenshot
        left, top, right, bottom = args
        width = right - left
        height = bottom - top

        with mss.mss() as sct:
            monitor_area = {
                "left": int(left),
                "top": int(top),
                "width": int(width),
                "height": int(height)
            }
            screenshot = sct.grab(monitor_area)
            img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            img.save(save_path)
            return img

    else:
        raise ValueError("Podaj 2 liczby (x, y) dla kliknięcia albo 4 liczby (left, top, right, bottom) dla screena.")

# ===== Detekcja i narysowanie bardzo grubej linii =====
def detect_and_draw_longest_line(mask, image, color_name, y_threshold=1000):
    edges = cv2.Canny(mask, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=80, maxLineGap=10)

    if lines is None:
        print(f"[❌] Nie znaleziono linii {color_name}.")
        return image, None

    max_length = 0
    longest_line = None

    for line in lines:
        x1, y1, x2, y2 = line[0]
        length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

        # tylko prawie poziome linie poniżej y_threshold
        if abs(y2 - y1) < 5 and y1 < y_threshold and y2 < y_threshold:
            if length > max_length:
                max_length = length
                longest_line = (x1, y1, x2, y2)

    if longest_line is not None:
        x1, y1, x2, y2 = longest_line
        color = (255, 0, 0) if color_name == "blue" else (0, 0, 255)
        cv2.line(image, (x1, y1), (x2, y2), color, 40)
        print(f"[🔥] Gruba linia {color_name} ({x1},{y1})–({x2},{y2}), długość {max_length:.1f}, y={y1}")
        return image, longest_line
    else:
        print(f"[ℹ️] Brak poziomych linii {color_name} poniżej y={y_threshold}.")
        return image, None

# ===== Testowa wersja is_position_open =====
def is_position_open(symbol):
    print(f"[TV MODE] Szukam grubych linii dla {symbol}...")

    image = np.array(do_action(-1920, 0, 0, 1080))
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # 💡 BRAKOWAŁO TEJ LINII:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Niebieski
    lower_blue = np.array([100, 150, 50])
    upper_blue = np.array([140, 255, 255])
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

    # Czerwony
    lower_red1 = np.array([0, 150, 50])
    upper_red1 = np.array([10, 255, 255])
    mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
    lower_red2 = np.array([160, 150, 50])
    upper_red2 = np.array([180, 255, 255])
    mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)

    # Wykryj linie i pogrub
    image, blue_line = detect_and_draw_longest_line(mask_blue, image, "blue")
    image, red_line = detect_and_draw_longest_line(mask_red, image, "red")

    # Zapisz i pokaż wynik
    cv2.imwrite("wynik_thicc.png", image)
    cv2.imshow("GRUBE LINIE", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    if blue_line or red_line:
        print("[✅] Pozycja otwarta (wykryto grubą linię).")
        return True
    else:
        print("[ℹ️] Brak grubych linii — pozycja zamknięta.")
        return False

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


def get_longest_line_y(image):
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

    _, blue_line = detect_and_draw_longest_line(mask_blue, image.copy(), "blue")
    _, red_line = detect_and_draw_longest_line(mask_red, image.copy(), "red")

    line = None
    if blue_line and red_line:
        len_blue = np.sqrt((blue_line[2] - blue_line[0])**2 + (blue_line[3] - blue_line[1])**2)
        len_red = np.sqrt((red_line[2] - red_line[0])**2 + (red_line[3] - red_line[1])**2)
        line = blue_line if len_blue > len_red else red_line
    elif blue_line:
        line = blue_line
    elif red_line:
        line = red_line

    if line:
        y_line = line[1]
        scale_y = 1349 / 1080
        real_y = y_line * scale_y
        do_action(-570, real_y)
        time.sleep(3)
        print("git")
        dwa_y = y_line - 16
        jeden_y = y_line - 36
        do_action(-485, jeden_y, -430, dwa_y, save_path="entry.png")  # screenshot
        entry_price = read_number_from_image("entry.png")
        print(f"entry {entry_price}")

        return y_line
    else:
        print("[ℹ️] Nie wykryto żadnej linii — y_line = None")
        return None

# ===== Start =====
if __name__ == "__main__":
    image = np.array(do_action(-1920, 0, 0, 1080))
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    y_line = get_longest_line_y(image)
    print(f"\n[✅] Wynikowy Y = {y_line}")