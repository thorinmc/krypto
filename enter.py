import pyautogui
import time

#pyautogui.click(1090,365)
pyautogui.click(1450,365)
time.sleep(5)
img = pyautogui.screenshot(region=(1433, 349, 1400, 315))
img.save("entry.png")



#365 