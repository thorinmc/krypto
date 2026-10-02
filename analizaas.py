import sqlite3
from collections import Counter
from datetime import datetime, timedelta

DB_FILE = "bot_obserwator.db"

def load_recent_events(days=7):
    """Załaduj zdarzenia z ostatnich X dni."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        SELECT nazwa, typ, szczegoly, data_czas FROM zdarzenia
        WHERE data_czas >= ?
    """, (since,))
    
    rows = cursor.fetchall()
    conn.close()
    return rows

def analyze_usage(days=7):
    events = load_recent_events(days)
    
    start_apps = []
    audio_changes = []
    chrome_tabs = []
    
    for nazwa, typ, szczegoly, data_czas in events:
        if typ == "start_aplikacji":
            start_apps.append(nazwa)
        elif typ == "zmiana_audio":
            audio_changes.append((nazwa, szczegoly))
        elif typ == "karta_otwarta":
            chrome_tabs.append((nazwa, szczegoly))
    
    print(f"\nAnaliza z ostatnich {days} dni:")
    print("Najczęściej uruchamiane aplikacje:")
    for app, count in Counter(start_apps).most_common(5):
        print(f"  - {app}: {count} razy")
    
    print("\nNajczęściej otwierane karty Chrome:")
    tab_titles = [t[0] for t in chrome_tabs]
    for tab, count in Counter(tab_titles).most_common(5):
        print(f"  - {tab}: {count} razy")
    
    print("\nZmiany statusu audio (przykładowe):")
    for i, (app, status) in enumerate(audio_changes[:5], 1):
        print(f"  {i}. {app} -> {status}")

def main():
    analyze_usage()

if __name__ == "__main__":
    main()