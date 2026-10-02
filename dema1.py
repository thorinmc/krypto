# region ======================================================= IMPORTY ============================================================
#endregion
# region ======================================================= XY + TIME Z TV =====================================================
# region ============================================= DANE XY ====================================================
# endregion
# region =============================================== TIME =====================================================
# endregion
# endregion
# region ======================================================= LOGOWANIE ==========================================================
# region ============================================== ALWAYS ====================================================
# endregion
# region =============================================== ONCE =====================================================
# endregion
# endregion
# region ======================================================= FIX OHLC ===========================================================
# region ============================================= 3=9 ====================================================
# endregion
# region ===================================== ZA WYSOKA CENA 300K ============================================
# endregion
# region ===================================== KOLEJNOSC POD KLUCZ ============================================
# endregion
# region ======================================= ZLE LITERY OHLC ==============================================
# endregion
# region ======================================== KROPKI (TEKST) ==============================================
# endregion
# region ======================================== KROPKI (FLOAT) ==============================================
# endregion
# region ==================================== POD KLUCZ Z DODATKAMI ===========================================
# endregion
# endregion
# region ======================================================= FIX CSV ============================================================
# region ======================================== CSV POWSTAŁO ===============================================
# endregion
# region ======================================= CHUJOWE LINIJKI  ============================================
# endregion
# endregion
# region ======================================================= FIRST SCAN =========================================================
# region ========================================= FIRST PATH ================================================
# endregion
# region ======================================== AKTUALNA POZ ===============================================
#endregion
# region ========================================= TEST FLOAT ================================================
# endregion
# region ======================================= DEF FIRST SCAN ==============================================
#endregion
# endregion
# region ======================================================= DODATKI OHLC =======================================================
# region ============================================ CZAS ===================================================
# endregion
# region ======================================= OHLC ZE SCREEN ==============================================
# endregion
# endregion
# region ======================================================= ZAPIS CSV ==========================================================
# region ===================================== ZAPIS OTWARTEJ POZYCJI ========================================
# endregion
# region ======================================== ZATRZYMANIE TRADE ==========================================
# endregion
# region ========================================= USUŃ STARY CSV ============================================
# endregion
# region ====================================== ZATRZYMANIE TRADE END ========================================
# endregion
# endregion
# region ======================================================= DODATKI ============================================================
# region ========================================== DO ACTION ================================================
# endregion
# region ========================================== PRINT ONCE ===============================================
# endregion
# region ============================================ CTRL Q =================================================
# endregion
# region ==================================== WSZYSTKO I NIC (FRACTAL) =======================================
# endregion
# endregion
# region ======================================================= DF/CSV =============================================================
# region ======================================== TEST DF + CSV  =============================================
# endregion
# region ========================================== TIMESTAMP ================================================
# endregion
# region ============================================= ALL ===================================================
# endregion
# region ======================================== FRACTAL DO CSV =============================================
#endregion 
# region ================================== DF DO CSV PRZY BRAKU DANYCH ======================================
# endregion
# region ========================================== DEMA DO DF ===============================================
# endregion
# region ============================================ BINANCE ================================================
# endregion
# endregion
# region ======================================================= NOWA ŚWIECA TV =====================================================
# region ========================================= 1 ZLECENIE ================================================
# endregion
# region =========================================== LOADER ==================================================
# endregion
# region ========================================= ODCZYTANIE ================================================
# endregion
# region ============================================ TIME ===================================================
# endregion
# region =========================================== LOADER ==================================================
# endregion
# endregion
# region ======================================================= OTWARTA POZYCJA ====================================================
# region =========================================== LINIA ==================================================
# endregion
# region =========================================== OPEN POS =================================================
#endregion
#endregion
# region ======================================================= OGÓŁY BINANCE ======================================================
# region ============================================ BŁĘDY ==================================================
# region ===================================== CZAS MS ========================================
# endregion
# region ====================================== -1111 =========================================
# endregion
# endregion
# region ============================================= API ===================================================
# endregion
# region ============================================ CLOSE ==================================================
# endregion
# region ============================================= OPEN ==================================================
# endregion
# endregion
# region ======================================================= ANALIZA RYNKU ======================================================
# region ============================================= AI ====================================================
# endregion
# region ===================================== NAGŁY WZROST/SPADEK ===========================================
# endregion
# region ======================================= ODLEGŁOŚCI DEMA =============================================
# endregion
# endregion
# region ======================================================= LICZENIE ===========================================================
# region ============================================ TICK ===================================================
# endregion
# region ========================================== PERCISION ================================================
# endregion
# region ============================================= QTY ===================================================
# endregion
# region ========================================== WZOR DEMA ================================================
# endregion
# region ============================================ DEMA ===================================================
# endregion
# region ========================================= ALL FRACTAL ===============================================
# endregion
# region ========================================= NEW FRACTAL ===============================================
# endregion
# endregion
# region ======================================================= LICZENIE SL/TP =====================================================
# region ========================================== LOCAL SL =================================================
# endregion
# region ========================================== SL/TP TV =================================================
# endregion
# region ============================================ FIX ====================================================
# region ====================================== PT1 =========================================
# endregion
# region ====================================== PT2 =========================================
# endregion
# endregion
# endregion
# region ======================================================= OGÓŁY TV ===========================================================
# region ========================================= ZAMKNIJ POS ================================================
# endregion
# region ======================================== BINANCE NA TV ===============================================
# endregion
# endregion
# region ======================================================= OTWIERANIE POZYCJI TV ==============================================
# region ============================================= DEF ===================================================

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

    # 🔁 retry jak nie ma linii
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
    jeden_y = int(y_line - 50)

    do_action(1432, int(jeden_y), 1488, int(dwa_y), save_path="entry.png")
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

    # Zrzuty do OCR (górny/dolny)
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

        # używamy extract_float_from_text żeby ogarnąć rzeczy typu '76930.3. dolny.png'
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
    MAX_PX_MOVE = 1070  # ustaw wg swojego monitora
    if abs(px_sl_x) > MAX_PX_MOVE or abs(px_tp_x) > MAX_PX_MOVE:
        close_position_tv()
        print(f"[🚫] px_sl_x={px_sl_x}, px_tp_x={px_tp_x} wyglądają nienormalnie — NIE ruszam myszką.")
        return tp_price_final, sl_price_final

    # Ruchy myszką - BUY
    if chuj == "buy":
        px_tp_x *= -1
        print(f"[ACTION] moveTo(1300, {y_line}) then dragRel(0, {px_tp_x})")
        pyautogui.moveTo(1300, y_line, duration=0.2)
        pyautogui.dragRel(0, px_tp_x, duration=0.2, button='left')

        print(f"[ACTION] moveTo(1350, {y_line}) then dragRel(0, {px_sl_x})")
        pyautogui.moveTo(1350, y_line, duration=0.2)
        pyautogui.dragRel(0, px_sl_x, duration=0.2, button='left')

    # Ruchy myszką - SELL
    if chuj == "sell":
        px_tp_x *= -1
        print(f"[ACTION] moveTo(1300, {y_line}) then dragRel(0, {px_tp_x})")
        pyautogui.moveTo(1300, y_line, duration=0.2)
        pyautogui.dragRel(0, px_tp_x, duration=0.2, button='left')
        px_sl_x *= -1
        print(f"[ACTION] moveTo(1350, {y_line}) then dragRel(0, {px_sl_x} * -1)")
        pyautogui.moveTo(1350, y_line, duration=0.2)
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
# region ============================================= XUP/XDOWN ==================================================
# endregion
# endregion
# region ======================================================= OTWIERANIE POZYCJI BINANCE =========================================
# region =========================================== MONITOR =================================================
# endregion
# region ========================================= OTWIERANIE ================================================
# endregion
# region ========================================== ZAMYKANIE ================================================
# endregion
# region ========================================== OPEN POS =================================================
# endregion
# endregion
# region ======================================================= NOWA ŚWIECA BINANCE ================================================
# endregion
# region !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! WARNINGI !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! *

#=========== DAJ CTRL F BO JEST TO POJEBANE TYLKO DO BINANCE ===============

def safe_binance_call(func, *args, **kwargs):
    return func(*args, **kwargs)
def retry_on_time_error(func, *args, **kwargs):
    return func(*args, **kwargs)





# endregion
# region !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! DEF TRADE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! *

def trade(symbol, tp_multiplier, precision):

# region ============================================== RESET PULLBACK UP =================================================

    #=== resret pullbacku ===
    def reset_pullback_up():
        nonlocal pullback_up_part2, dotknieto_50_up,already_warned_bad_dema_up, already_warned_too_close_dema_up
        nonlocal waiting_20, waiting_50, waiting_20_counter, waiting_50_counter, dotknieto_100
        nonlocal waiting_pullback_up, pullback_up_counter, pullback1_up_counter, dotknieto_50
        nonlocal last_used_fractal_time, dotknieto_20_up, kolejnosc_up_counter, dotknieto_20
        nonlocal wybicie_counter_20_up, wybicie_counter_up, wybicie_counter_50_up
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

# endregion
# region ============================================= RESET PULLBACK DOWN ================================================

    def reset_pullback_down():
        nonlocal pullback_down_part2
        nonlocal waiting_20_down, waiting_50_down
        nonlocal waiting_20_down_counter, waiting_50_down_counter
        nonlocal waiting_pullback_down, pullback_counter, pullback1_counter
        nonlocal last_used_fractal_time_down, kolejnosc_down_counter, wybicie_counter_down
        nonlocal wybicie_counter_20_down, wybicie_counter_50_down, dotknieto_50_down, dotknieto_20_down
        nonlocal already_warned_bad_dema, already_warned_too_close_dema, dotknieto_50_down2
        nonlocal dotknieto_100_down2, dotknieto_20_down2
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
# region ================================================== ALL NONE ======================================================
    
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

# endregion
# region ================================================== ODPALANIE =====================================================
    
    while True:
        if str(x).lower() == "tv" and symbol != "BTCUSDT":
            return

        now = datetime.now()

        last_checked = last_checked_candles[symbol]
        is_open = retry_on_time_error(is_position_open, symbol)
        new_candle_time = wait_for_closed_candle(symbol, last_checked)

        df = get_futures_klines(symbol, interval='1m', limit=3)

        # 🔒 GUARD 1 — brak danych OHLC
        if df is None or df.empty:
            print(f"[TRADE ⚠️] {symbol}: brak danych OHLC — pomijam iterację")
            time.sleep(1)
            continue

        df = apply_dema_indicators(df)

        # 🔒 GUARD 2 — brak DEMA
        if df is None or df.empty:
            print(f"[TRADE ⚠️] {symbol}: brak DEMA — pomijam iterację")
            time.sleep(1)
            continue

        # 🔒 dopiero TERAZ wolno dotykać index
        df.index = pd.to_datetime(df.index)

        if len(df) < 2:
            print(f"[TRADE ⚠️] {symbol}: za mało świec")
            continue

        last_checked_candle = df.index[-2]
        last_checked_candles[symbol] = new_candle_time

        if x == "tv":
            row = df.iloc[-1]   # TV → świeca zamknięta
        else:
            row = df.iloc[-2]

        if not all(k in row for k in ["DEMA_short", "DEMA_medium", "DEMA_long"]):
            print(f"[TRADE ⚠️] Brak kolumn DEMA w row ({symbol})")
            continue

        # ⏱ Czekaj aż pojawi się świeca po last_checked_candle
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
# region ===================================================== DF =========================================================
                
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
# region ============================================== RESETY CLOSE AI ===================================================
            
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

                # Dopiero teraz bezpiecznie pobierz row
                if x == "tv": 
                    row = df.iloc[-1]   # TradingView → ostatnia świeca już zamknięta
                else:
                    row = df.iloc[-2]

                # Jeśli jest otwarta pozycja LONG i zanikła kolejność DEMA → zamknij
                if position == "long" and not (row['DEMA_short'] > row['DEMA_medium'] > row['DEMA_long']):
                    close_position(symbol)
                    reset_pullback_up()
                    print(f"[ZAMKNIĘCIE] [{datetime.now().strftime('%H:%M')}] Trend wzrostowy DEMA zanikł — {symbol}")
                    continue

                # Jeśli jest otwarta pozycja SHORT i zanikła kolejność DEMA → zamknij
                if position == "short" and not (row['DEMA_short'] < row['DEMA_medium'] < row['DEMA_long']):
                    close_position(symbol)
                    reset_pullback_down()
                    print(f"[ZAMKNIĘCIE] [{datetime.now().strftime('%H:%M')}] Trend spadkowy DEMA zanikł — {symbol}")
                    continue
                latest_fractal = fractal(symbol, df)
                if df is None or df.empty:
                    print("[⛔ trade] df jest None/puste — NIE wywołuję fractal()")
                    continue 

                # 🔁 RESET DLA UP — jeśli aktywny pullback lub waiting, ale zła kolejność DEMA
                if pullback_up_part2 or waiting_20 or waiting_50:
                    if not (row['DEMA_short'] > row['DEMA_medium'] > row['DEMA_long']):
                        print(f"[RESET_UP] [{datetime.now().strftime('%H:%M')}] Zła kolejność DEMA przy aktywnym pullback — {symbol}")
                        reset_pullback_up()
                        continue
                                
                # 🔁 RESET DLA DOWN — jeśli aktywny pullback lub waiting, ale zła kolejność DEMA
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
                continue  # Pomija resztę tej iteracji

# endregion
# region ================================================= PULLBACK UP ====================================================
# region ====================================== WSTĘP =========================================
            if (not pullback_up_part2 and
                row['low'] > row['DEMA_short'] and
                row['low'] > row['DEMA_medium'] and
                row['low'] > row['DEMA_long'] and
                row['DEMA_short'] > row['DEMA_medium'] > row['DEMA_long']):

                pullback_up_part2 = True
                print("pullback")
                pullback_state[symbol] = True
                pullback1_up_counter = 0
                continue
                
            if pullback_up_part2:
                # 🔁 RESET jeśli kolejność DEMA się rozsypała, zanim dotknęło DEMA
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
# region ================================================ PULLBACK DOWN ===================================================
# region ====================================== WSTĘP =========================================

            if (not pullback_down_part2 and
                row['high'] < row['DEMA_short'] and
                row['high'] < row['DEMA_medium'] and
                row['high'] < row['DEMA_long'] and
                row['DEMA_short'] < row['DEMA_medium'] < row['DEMA_long']):

                pullback_down_part2 = True
                print("pullback short")
                continue
            
            if pullback_down_part2:
                # 🔁 RESET jeśli DEMA się rozjechały zanim dotknęło DEMA
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
# region ==================================================== EXCEL =======================================================

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
# region =============================================== ODPALENIE TRADE ==================================================

#============================= DEF Z DEBUG ===========================
def start_trade_thread(symbol):
    while True:
        try:
            trade(symbol, tp_multiplier, precision)
        except Exception as e:
            print(f"[THREAD CRASH] {symbol}: {type(e).__name__} — {e}")
            traceback.print_exc()
            print(f"[RESTART] {symbol} → wątek ruszy ponownie za 20s...\n")
            time.sleep(20)

#=============================== ODPALENIE ============================
threads = []
for symbol in symbols:
    thread = threading.Thread(target=start_trade_thread, args=(symbol,), daemon=True)
    thread.start()
    threads.append(thread)

# endregion
# endregion
# region !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! PO DEF TRADE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! *