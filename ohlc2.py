import os
import re
import easyocr

IMAGE_FOLDER = r"C:\Users\iwojc\OneDrive\Pulpit\binance-dema-bot\ohlc_dataset\images"
reader = easyocr.Reader(['en'])

def fix_ocr_errors(text):
    text = text.replace(',', '.')  # przecinki -> kropki
    text = text.replace(' ', '')   # usuń spacje
    # wstaw podkreślnik przed H, L, C jeśli nie ma
    text = re.sub(r'(?<=\d)([HLC])', r'_\1', text)
    return text

ohlc_regex = re.compile(r'O?(\d+\.\d+)_H(\d+\.\d+)_L(\d+\.\d+)_C(\d+\.\d+)', re.IGNORECASE)

for filename in os.listdir(IMAGE_FOLDER):
    if filename.startswith("ohlc_") and filename.lower().endswith((".png", ".jpg", ".jpeg")):
        full_path = os.path.join(IMAGE_FOLDER, filename)
        result = reader.readtext(full_path, detail=0)
        if not result:
            print(f"[⚠️] Nie udało się odczytać OCR: {filename}")
            continue

        raw_text = ''.join(result)
        print(f"[ℹ️] OCR {filename}: {raw_text}")

        fixed_text = fix_ocr_errors(raw_text)
        if fixed_text:
            fixed_text = 'O' + fixed_text[1:]
        match = ohlc_regex.search(fixed_text)
        if not match:
            print(f"[⚠️] Nie udało się sparsować OHLC: {filename}")
            continue

        o, h, l, c = match.groups()
        new_name = f"O{o}_H{h}_L{l}_C{c}.png"  # zawsze O na początku
        new_full_path = os.path.join(IMAGE_FOLDER, new_name)

        counter = 1
        while os.path.exists(new_full_path):
            new_name = f"O{o}_H{h}_L{l}_C{c}_{counter}.png"
            new_full_path = os.path.join(IMAGE_FOLDER, new_name)
            counter += 1

        os.rename(full_path, new_full_path)
        print(f"[✅] {filename} -> {new_name}")