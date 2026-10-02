import psutil
import sqlite3
from datetime import datetime
import time
import threading
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume, IAudioMeterInformation
from flask import Flask, request
import pythoncom
from flask_cors import CORS
import win32gui
import win32process

DB_FILE = "bot_obserwator.db"
poprzednia_zmienna = None

SYSTEM_PROCESSES_TO_IGNORE = {
    "unsecapp.exe",
    "securityhealthsystray.exe",
    "widgetboard.exe",
    "taskhostw.exe",
    "explorer.exe",
    "csrss.exe",
    "wininit.exe",
    "services.exe",
    "svchost.exe",
    "smss.exe",
    "WUDFHost.exe",
    "Lively.PlayerCefSharp.exe",
    "LsaIso.exe",
    "FileSyncHelper.exe",
    "dllhost.exe",
    "FileCoAuth.exe",
    "MoUsoCoreWorker.exe",
    "IdleScheduleEventAction.exe",
    "WindowsPackageManagerServer.exe",
    "msedge.exe",
    "TrustedInstaller.exe",
    "cleanmgr.exe",
    "msedgewebview2.exe",
    "backgroundTaskHost.exe",
    "RuntimeBroker.exe",
    "backgroundTaskHost.exe",
    "HxTsr.exe",
    "WmiPrvSE.exe",
    "GlobalPresenter.exe",
    "ShellExperienceHost.exe",
    "SystemSettingsBroker.exe",
    "OfficeC2RClient.exe",
    "LenovoVantage-(LenovoSecurityAddin).exe",
    "LenovoVantage-(LenovoAuthenticationAddin).exe",
    "LenovoVantage-(LenovoServiceBridgeAddin).exe",
    "LenovoVantage-(SettingsWidgetAddin).exe",
    "LenovoVantage-(BatteryWidgetAddin).exe",
    "LenovoVantage-(IdeaKBDManagerAddin).exe",
    "LenovoVantage-(SmartPanelAddin).exe",
    "LenovoVantage-(DeviceSettingsHeartbeatAddin).exe",
    "LenovoVantage-(SmartDisplayAddin).exe",
    "LenovoVantage-(IdeaNotebookAddin).exe",
    "LenovoVantage-(DeviceSettingsSystemAddin).exe",
    "LenovoVantage-(MultimediaAddin).exe",
    "ConfigServiceAgent.exe",
    "updater.exe",
    "SecurityHealthHost.exe",
    "OneDriveLauncher.exe",
    "ActionsServer.exe",
    "SDXHelper.exe",
    "conhost.exe",
    "dmclient.exe",
    "LenovoVantage-(LenovoSystemUpdateAddin).exe",
    "LenovoVantage-(LenovoSystemUpdateAddin).exe",
    "BGHelper.exe",
}
# --- Inicjalizacja bazy ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uruchomienia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nazwa TEXT,
            sciezka TEXT,
            data_startu TEXT,
            audio_status TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS zdarzenia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pid INTEGER,
            nazwa TEXT,
            typ TEXT,
            szczegoly TEXT,
            data_czas TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS karty_chrome (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tytul TEXT,
            url TEXT,
            data_czas TEXT
        )
    """)

    conn.commit()
    conn.close()

# --- Zapis zdarzeń ---
def save_to_db(nazwa, sciezka, audio_status):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO uruchomienia (nazwa, sciezka, data_startu, audio_status)
        VALUES (?, ?, ?, ?)
    """, (nazwa, sciezka, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), audio_status))
    conn.commit()
    conn.close()

def log_event(pid, nazwa, typ, szczegoly):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO zdarzenia (pid, nazwa, typ, szczegoly, data_czas)
        VALUES (?, ?, ?, ?, ?)
    """, (pid, nazwa, typ, szczegoly, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def log_chrome_tab(title, url):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO karty_chrome (tytul, url, data_czas)
        VALUES (?, ?, ?)
    """, (title, url, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# --- Sprawdzanie audio ---
def get_audio_status():
    audio_map = {}
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        if session.Process:
            try:
                volume_interface = session._ctl.QueryInterface(ISimpleAudioVolume)
                meter_interface = session._ctl.QueryInterface(IAudioMeterInformation)
                volume = volume_interface.GetMasterVolume()
                peak = meter_interface.GetPeakValue()

                if peak > 0:
                    audio_map[session.Process.name().lower()] = f"gra (głośność: {volume:.2f})"
                else:
                    audio_map[session.Process.name().lower()] = "pauza"
            except Exception:
                pass
    return audio_map

def zapisz_zdarzenie(typ, nazwa, szczegoly="", pid=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO zdarzenia (pid, nazwa, typ, szczegoly, data_czas)
        VALUES (?, ?, ?, ?, ?)
    """, (pid or 0, nazwa, typ, szczegoly, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
def get_active_window_process_name():
    hwnd = win32gui.GetForegroundWindow()
    if hwnd:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            proc = psutil.Process(pid)
            return proc.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
    return None


# --- Monitor procesów ---
def monitor():
    pythoncom.CoInitialize()
    print("[BOT] Start monitorowania procesów i audio...")

    # Pobieramy procesy działające przed startem bota
    uruchomione_pid_na_start = {p.info['pid'] for p in psutil.process_iter(['pid'])}
    uruchomione = {}

    while True:
        audio_status_map = get_audio_status()
        current_pids = set()

        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                pid = proc.info['pid']
                nazwa = proc.info['name'].lower() if proc.info['name'] else ""

                # Ignorujemy procesy startowe
                if pid in uruchomione_pid_na_start:
                    continue

                # Ignorujemy procesy systemowe
                if proc.info['name'] in SYSTEM_PROCESSES_TO_IGNORE:
                    continue

                current_pids.add(pid)
                sciezka = proc.info['exe'] or ""
                status = audio_status_map.get(nazwa.lower(), "brak audio")

                if pid not in uruchomione:
                    uruchomione[pid] = {
                        "nazwa": proc.info['name'],
                        "status_audio": status
                    }
                    save_to_db(proc.info['name'], sciezka, status)
                    log_event(pid, proc.info['name'], "start_aplikacji", f"Ścieżka: {sciezka}")
                    print(f"[NOWA APLIKACJA] {proc.info['name']} ({sciezka}) | Audio: {status}")

                elif uruchomione[pid]["status_audio"] != status:
                    uruchomione[pid]["status_audio"] = status
                    log_event(pid, proc.info['name'], "zmiana_audio", status)
                    print(f"[ZMIANA AUDIO] {proc.info['name']} -> {status}")

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # Zamknięte aplikacje
        ended_pids = set(uruchomione.keys()) - current_pids
        for pid in ended_pids:
            nazwa = uruchomione[pid]["nazwa"]
            log_event(pid, nazwa, "zamkniecie_aplikacji", "Proces zakończył działanie")
            print(f"[ZAMKNIĘCIE APLIKACJI] {nazwa} (PID {pid}) zakończył działanie")
            del uruchomione[pid]

        # Aktywne okno
        global poprzednia_zmienna
        current_active_app = get_active_window_process_name()
        if poprzednia_zmienna != current_active_app:
            log_event(None, current_active_app, "aktywna_aplikacja", "Zmiana aktywnego okna")
            print(f"[AKTYWNA APLIKACJA] {current_active_app}")
            poprzednia_zmienna = current_active_app

        time.sleep(2)
# --- Serwer Flask odbierający karty Chrome ---
app = Flask(__name__)
CORS(app) 

@app.route('/tabs', methods=['POST'])
def receive_tabs():
    data = request.get_json()
    print(f"[{datetime.now()}] Otrzymano listę kart z Chrome:")
    for tab in data.get("tabs", []):
        tytul = tab.get("title", "")
        url = tab.get("url", "")
        print(f" - {tytul} ({url})")
        zapisz_zdarzenie("karta_otwarta", tytul, szczegoly=url, pid=0)
    return {"status": "ok"}

# --- Uruchamianie wszystkiego ---
if __name__ == "__main__":
    init_db()

    # Wątek monitorowania procesów
    t1 = threading.Thread(target=monitor, daemon=True)
    t1.start()

    # Start serwera Flask
    print("[BOT] Oczekiwanie na dane z Chrome...")
    app.run(port=5000)