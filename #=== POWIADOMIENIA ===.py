#=== POWIADOMIENIA ===
def send_notification(title, message):
    notification.notify(
        title=title,
        message=message,
        timeout=5  # sekundy, ile dymek ma być widoczny
    )

def watchdog():
    import time

    # Słownik zapamiętujący stan pozycji dla każdego symbolu
    previous_position_state = {symbol: False for symbol in symbols}

    while True:
        for symbol in symbols:
            try:
                is_open = is_position_open(symbol)
                was_open = previous_position_state[symbol]

                # Pozycja właśnie się zamknęła
                if pullback_state[symbol] == False:
                    continue
                else:
                    send_notification("Impuls DEMA aktywny", f"{symbol} → pullback_up_part2 = True")
                    print (f"powinno przysłać pullback_up_2 {symbol}")
                if was_open and not is_open:
                    send_notification("Pozycja zamknięta", f"{symbol} → Pozycja została właśnie zamknięta!")
                    print (f"powinno przysłać otwarto pozycje {symbol}")
                # Pozycja właśnie się otworzyła
                elif not was_open and is_open:
                    send_notification("Pozycja otwarta", f"{symbol} → Nowa pozycja została otwarta!")
                    print (f"powinno przysłać zamknięto pozycje {symbol}")
                # Zapisz aktualny stan na następny obieg
                previous_position_state[symbol] = is_open

            except Exception as e:
                send_notification("Błąd WATCHDOGA", f"{symbol}: {e}")

        time.sleep(30)  # Sprawdza co 30 sekund

watchdog_thread = threading.Thread(target=watchdog, daemon=True)
watchdog_thread.start()


#=== błędy 
def safe_binance_call(func, *args, retries=1000, delay=60, **kwargs):
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except (BinanceAPIException, RequestException, ConnectionError, Timeout) as e:
            print(f"[⛔ BRAK INTERNETU / BŁĄD API] {type(e).__name__}: {str(e)} — oczekiwanie {delay}s...")
            time.sleep(delay)
        except Exception as e:
            print(f"[❌ INNY BŁĄD] {e}")
            break
    return None

def retry_on_time_error(func, *args, retries=3, delay=60, **kwargs):
    for attempt in range(retries):
        try:
            return safe_binance_call(func, *args, delay=delay, **kwargs)
        except BinanceAPIException as e:
            if "-1021" in str(e):
                print("🕒 API -1021: czas systemowy za szybki – pobieram offset...")
                offset = get_time_offset()
                time.sleep(2)
                kwargs["timestamp"] = int(time.time() * 1000 + offset)
                print(f"[🔁 RETRY] Próba ponowna z timestampem + offset {offset} ms")
            else:
                raise
    raise Exception("⛔ Zbyt wiele prób po błędzie czasu (-1021)")