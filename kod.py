import pyautogui
from PIL import Image
import time

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
do_action(1450,365)
time.sleep(5)
do_action(1453, 322, 1515, 349, save_path="entry.png")



#do_action(2200, 1100)
#time.sleep(10)
#do_action(1300, 100)
#for _ in range(10):
    #pyautogui.press('left')

#pyautogui.scroll(-3)  