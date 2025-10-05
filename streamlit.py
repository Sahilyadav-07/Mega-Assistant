import speech_recognition as sr
import pyttsx3
import subprocess
import webbrowser
from rapidfuzz import process
import threading
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from datetime import datetime
import requests

r = sr.Recognizer()
engine = pyttsx3.init()

wake_words = ["mega", "hey mega"]

apps = {
    "notepad": r"notepad",
    "spotify": r"spotify",  
    "whatsapp": r"start whatsapp:",
    "file explorer": r"explorer",
    "settings": r"start ms-settings:",
    "visual studio code": r"code",
    "google chrome": r"start chrome",
    "edge": r"start msedge",
    "brave": r"start brave",
    "firefox": r"start firefox",
    "youtube": "web",
    "paint": r"mspaint",
    "command prompt": r"cmd",
    "powershell": r"powershell",
    "snipping tool": r"snippingtool",
    "control panel": r"control",
    "task manager": r"taskmgr"
}

assistant_active = False
assistant_timer = None
timeout_seconds = 30

# ------------- GUI -------------
root = tk.Tk()
root.title("Mega Assistant")
root.geometry("500x400")

text_widget = ScrolledText(root, state='disabled', wrap=tk.WORD)
text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Microphone state
mic_label = tk.Label(root, text="🟢 Listening for wake word...", fg="green", font=("Arial", 12, "bold"))
mic_label.pack(pady=2)

# Status label
status_label = tk.Label(root, text="💤 Idle", fg="blue", font=("Arial", 12, "bold"))
status_label.pack(pady=2)


def say_and_print(text, speak=True):
    text_widget.config(state='normal')
    text_widget.insert(tk.END, text + "\n")
    text_widget.see(tk.END)
    text_widget.config(state='disabled')
    if speak:
        engine.say(text)
        engine.runAndWait()


def reset_timer():
    global assistant_timer
    if assistant_timer:
        assistant_timer.cancel()
    assistant_timer = threading.Timer(timeout_seconds, go_to_sleep)
    assistant_timer.start()


def go_to_sleep():
    global assistant_active
    assistant_active = False
    say_and_print("💤 No activity detected. Mega going back to sleep.")
    mic_label.config(text="🟢 Listening for wake word...")
    status_label.config(text="💤 Idle")


def take_command():
    mic_label.config(text="🎤 Mega is listening for your command...")
    status_label.config(text="🎤 Listening...")
    with sr.Microphone() as source:
        try:
            audio = r.listen(source, timeout=3, phrase_time_limit=4)
        except sr.WaitTimeoutError:
            say_and_print("⚠️ I didn’t hear anything, please speak again.", speak=False)
            status_label.config(text="⚠️ No speech detected")
            mic_label.config(text="🟢 Listening for wake word...")
            return ""
    try:
        command = r.recognize_google(audio).lower()
        say_and_print(f"✅ You said: {command}", speak=False)
        status_label.config(text="✅ Heard command")
        return command
    except sr.UnknownValueError:
        say_and_print("⚠️ Sorry, Mega could not understand. Please repeat.", speak=False)
        status_label.config(text="⚠️ Could not understand")
        return ""
    except sr.RequestError:
        say_and_print("❌ Speech recognition service error.", speak=False)
        status_label.config(text="❌ Service error")
        return ""


def find_best_match(command, choices):
    match, score, _ = process.extractOne(command, choices)
    if score > 60:
        return match
    return None


def handle_command(cmd):
    if "spotify" in cmd:
        say_and_print("🎵 Opening Spotify...")
        try:
        # Try to open desktop app first
            proc = subprocess.Popen(apps["spotify"], shell=True)
            # Give it a short moment and check if process immediately ended
            threading.Timer(2.0, lambda: (
                webbrowser.open("https://open.spotify.com/")
                if proc.poll() is not None else None)
            ).start()
        except Exception:
            say_and_print("Opening Spotify web player")
            webbrowser.open("https://open.spotify.com/")
        return True


    if "youtube" in cmd:
        query = cmd.replace("search", "").replace("youtube", "").strip()
        if query:
            say_and_print(f"Mega is searching YouTube for {query}")
            webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
        else:
            say_and_print("Opening YouTube")
            webbrowser.open("https://www.youtube.com")
        return True

    if "google" in cmd or "search" in cmd:
        query = cmd.replace("search", "").replace("google", "").strip()
        if query:
            say_and_print(f"Mega is searching Google for {query}")
            webbrowser.open(f"https://www.google.com/search?q={query}")
        return True

    if "wikipedia" in cmd:
        topic = cmd.replace("wikipedia", "").replace("search", "").strip()
        if topic:
            say_and_print(f"Mega is opening Wikipedia page for {topic}")
            webbrowser.open(f"https://en.wikipedia.org/wiki/{topic}")
        else:
            say_and_print("Opening Wikipedia homepage")
            webbrowser.open("https://www.wikipedia.org")
        return True

    if "time" in cmd:
        now = datetime.now()
        say_and_print(f"⏰ The current time is {now.strftime('%H:%M:%S')}")
        return True

    if "weather" in cmd:
        city = "Pune"
        parts = cmd.split()
        for i, word in enumerate(parts):
            if word.lower() == "in" and i + 1 < len(parts):
                city = " ".join(parts[i + 1:])
                break
        try:
            api_key = "a713b7ad6da355d37d56b7547fccbde3"
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            response = requests.get(url, timeout=5).json()
            if response.get("cod") == 200:
                temp = response["main"]["temp"]
                desc = response["weather"][0]["description"]
                say_and_print(f"☁️ The weather in {city} is {temp}°C with {desc}")
            elif response.get("cod") == "404":
                say_and_print(f"City '{city}' not found. Please check the city name.")
            else:
                say_and_print("Could not fetch weather. Try again later.")
        except requests.exceptions.RequestException:
            say_and_print("Failed to get weather information. Check your internet connection.")
        return True

    best = find_best_match(cmd, apps.keys())
    if best:
        say_and_print(f"Mega is opening {best}")
        subprocess.Popen(apps[best], shell=True)
        return True

    return False


def run_assistant():
    global assistant_active
    assistant_active = True
    mic_label.config(text="✅ Mega is active...")
    status_label.config(text="✅ Mega awake")
    while assistant_active:
        reset_timer()
        cmd = take_command()
        if not cmd:
            continue
        if "exit" in cmd or "quit" in cmd or "stop" in cmd:
            say_and_print("Goodbye! Mega is going back to sleep.")
            assistant_active = False
            mic_label.config(text="🟢 Listening for wake word...")
            status_label.config(text="💤 Idle")
            break
        if not handle_command(cmd):
            say_and_print(f"Mega doesn't know how to do that. Searching Google for '{cmd}'")
            webbrowser.open(f"https://www.google.com/search?q={cmd}")


def listen_for_wake_word():
    global assistant_active
    mic_label.config(text="🟢 Listening for wake word...")
    status_label.config(text="💤 Idle")
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.3)
        while True:
            if not assistant_active:
                try:
                    audio = r.listen(source, timeout=5, phrase_time_limit=5)
                    text = r.recognize_google(audio).lower()
                    print(f"Heard: {text}")
                    if any(word in text for word in wake_words):
                        say_and_print("✅ Mega is awake and ready!")
                        mic_label.config(text="✅ Mega active")
                        status_label.config(text="✅ Mega awake")
                        threading.Thread(target=run_assistant, daemon=True).start()
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except sr.RequestError:
                    say_and_print("❌ Speech service error. Check your internet connection.")
                    status_label.config(text="❌ Service error")


threading.Thread(target=listen_for_wake_word, daemon=True).start()
root.mainloop()
