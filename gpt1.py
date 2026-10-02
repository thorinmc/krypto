import subprocess
import time
import speech_recognition as sr
import pyttsx3

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Słucham...")
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio, language="pl-PL")
    except:
        return ""

def send_message_via_test1(message):
    # Wywołanie Twojego C++ exe
    subprocess.run(["C:\\ścieżka\\do\\test1.exe", message])

if __name__ == "__main__":
    while True:
        print("Nasłuchuję hasła 'chatgpt'...")
        text = listen().lower()
        if "chatgpt" in text:
            speak("Dajesz")
            print("Nagrywam wiadomość...")
            message = listen()
            print(f"[TY] {message}")
            send_message_via_test1(message)
            speak("Wiadomość wysłana.")