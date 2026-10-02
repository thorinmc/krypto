import subprocess
import time

# Ścieżka do Twojego pliku test1.exe
exe_path = r"C:\Users\iwojc\OneDrive\Pulpit\binance-dema-bot\test1.exe"

# Pętla, która odpala program 2 razy
for _ in range(2):
    subprocess.run([exe_path])
    time.sleep(1.2)  # odczekaj 1.2 sekundy