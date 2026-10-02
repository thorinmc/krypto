import json
import os
import time
import speech_recognition as sr
import pyttsx3
from datetime import datetime
from fuzzywuzzy import fuzz
import openai
import pyaudio
import wave
import numpy as np
import simpleaudio as sa
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


LOG_FILE = "chats_log.json"

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


def record_audio(duration=4, filename="original.wav"):
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1024

    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    print("Nagrywam...")
    frames = []

    for _ in range(0, int(RATE / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Koniec nagrywania.")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

def amplify_audio(input_filename, output_filename, factor=3.0):
    wav = wave.open(input_filename, 'rb')
    params = wav.getparams()
    frames = wav.readframes(params.nframes)
    audio_data = np.frombuffer(frames, dtype=np.int16)

    amplified = audio_data * factor
    amplified = np.clip(amplified, -32768, 32767).astype(np.int16)

    out_wav = wave.open(output_filename, 'wb')
    out_wav.setparams(params)
    out_wav.writeframes(amplified.tobytes())
    out_wav.close()

def listen():
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1.5  # ile sekund ciszy ma poczekać przed zakończeniem nagrywania
    recognizer.energy_threshold = 6000  # czułość mikrofonu
    with sr.Microphone() as source:
        print("🎤 Słucham...")
        audio = recognizer.listen(source)  # brak phrase_time_limit
    try:
        text = recognizer.recognize_google(audio, language="pl-PL")
        print("Usłyszano:", text)
        return text
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        print("Błąd połączenia z Google Speech API")
        return ""
    
def load_chat_log():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_chat_log(log):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=4, ensure_ascii=False)

def wait_for_hotword():
    print("Nasłuchuję hasła 'chatgpt'...")
    while True:
        text = listen()
        if not text:
            continue
        normalized = text.replace(" ", "").lower()
        if fuzz.partial_ratio("chatgpt", normalized) > 80:
            speak("Dajesz")
            return
        
def record_message(duration=4, filename="original.wav"):
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1024

    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    print("🎤 Nagrywam wiadomość...")
    frames = []

    for _ in range(0, int(RATE / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Zapis do pliku
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    # Rozpoznawanie mowy
    recognizer = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        audio_data = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio_data, language="pl-PL")
        print(f"[TY] {text}")
        return text
    except sr.UnknownValueError:
        print("Nie rozpoznano mowy")
        return ""
    except sr.RequestError:
        print("Błąd połączenia z Google Speech API")
        return ""

def find_or_create_chat(message):
    log = load_chat_log()
    best_match = None
    best_score = 0

    for chat in log:
        score = fuzz.partial_ratio(message, chat["topic"])
        if score > best_score:
            best_score = score
            best_match = chat

    if best_match and best_score > 60:
        print(f"Znaleziono pasujący czat: {best_match['topic']} ({best_score}%)")
        return best_match
    else:
        new_chat = {
            "id": len(log) + 1,
            "topic": message[:50],
            "created_at": datetime.now().isoformat(),
            "messages": []
        }
        log.append(new_chat)
        save_chat_log(log)
        print(f"Utworzono nowy czat: {new_chat['topic']}")
        return new_chat

def update_chat_log(chat_id, user_message, bot_response):
    log = load_chat_log()
    for chat in log:
        if chat["id"] == chat_id:
            if "messages" not in chat:
                chat["messages"] = []
            chat["messages"].append({"user": user_message, "bot": bot_response})
            break
    save_chat_log(log)

def summarize_or_full(response):
    if len(response.split()) > 15:
        return "Skrót: " + " ".join(response.split()[:15]) + "..."
    return response
def play_audio(filename):
    # Otwiera plik WAV i odtwarza
    wave_obj = sa.WaveObject.from_wave_file(filename)
    play_obj = wave_obj.play()
    play_obj.wait_done()  # czeka aż odtworzy się całe audio

if __name__ == "__main__":
    while True:
        wait_for_hotword()            # nasłuchuje hasła
        message = record_message()    # nagrywa wiadomość
        if not message:
            continue

        # Zapisz oryginał audio
        original_file = "original.wav"
        record_audio(filename=original_file)

        # Wzmocnij audio
        amplified_file = "amplified.wav"
        amplify_audio(original_file, amplified_file, factor=3.0)

        # Odtwórz wzmocnione audio, żeby wiedzieć czy głośność ok
        play_audio(amplified_file)

        # Zapisz tekst do pliku, który odczyta test1.exe
        with open("message.txt", "w", encoding="utf-8") as f:
            f.write(message)

        # Wywołaj EXE, żeby wkleił wiadomość do ChatGPT
        import subprocess
        EXE_PATH = r"C:\Users\iwojc\OneDrive\Pulpit\binance-dema-bot\test1.exe"
        subprocess.run([EXE_PATH])

        # Zapisz wiadomość w logu
        chat = find_or_create_chat(message)