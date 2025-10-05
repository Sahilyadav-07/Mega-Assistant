import speech_recognition as sr
import pyttsx3
import subprocess, threading, requests
from rapidfuzz import process
import customtkinter as ctk
from datetime import datetime
import time
from PIL import Image  # <-- NEW for loading logo image
import os
import webbrowser
import pygetwindow as gw

# ---------- APP & THEME ----------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def open_youtube():
    """
    Open YouTube in the installed YouTube app if available,
    otherwise in the system default browser.
    """
    try:
        # This will invoke the system's default handler (browser or app)
        os.system('start "" "https://www.youtube.com"')
    except Exception:
        # Fallback to Python's webbrowser module
        
        webbrowser.open("https://www.youtube.com")

def close_window(title_keyword: str) -> bool:
    """Try to close a window by its title. Returns True if closed, False if not found."""
    try:
        windows = gw.getWindowsWithTitle(title_keyword)
        if windows:
            for w in windows:
                w.close()
            return True
    except Exception as e:
        print(f"close_window error: {e}")
    return False

class MegaAssistant:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("🎙️ Mega Assistant")
        self.root.geometry("700x600")
        self.root.minsize(600, 500)

        # ✅ define variables first
        self.assistant_active = False
        self.timeout_seconds = 30
        self.api_key = "a713b7ad6da355d37d56b7547fccbde3"

        # Settings variables
        self.current_theme = "dark"
        self.zoom_level = 1.0
        self.view_mode = "desktop"  # desktop or phone

        # Configure grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        # Build UI and voice
        self.setup_ui()
        self.setup_voice()

        # ✅ apply zoom AFTER UI exists
        self.apply_zoom()
        
        self.opened_processes ={}
        # Start wake word listener
        threading.Thread(target=self.listen_for_wake_word, daemon=True).start()

    def setup_ui(self):
        # === HEADER SECTION ===
        self.header_frame = ctk.CTkFrame(self.root, height=80, corner_radius=15)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.header_frame.grid_columnconfigure(1, weight=1)

        # Logo/Icon replaced with image
        self.logo_frame = ctk.CTkFrame(self.header_frame, width=60, height=60, corner_radius=30)
        self.logo_frame.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        # ---- LOAD YOUR LOGO IMAGE HERE ----
        # Put the PNG in your assets folder:  D:\Voice assistant(Mega)\assets\mega_logo.png
        # Use absolute path below or relative path if script in same folder:
        logo_path = r"D:\Mega Assistant\assets\mega_logo.png"  # <-- change if needed
        self.logo_image = ctk.CTkImage(light_image=Image.open(logo_path),
                                       dark_image=Image.open(logo_path),
                                       size=(60, 60))
        self.logo_label = ctk.CTkLabel(self.logo_frame, image=self.logo_image, text="")
        self.logo_label.place(relx=0.5, rely=0.5, anchor="center")

        # Title and subtitle
        self.title_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.title_frame.grid(row=0, column=1, sticky="ew", padx=10)

        self.title_label = ctk.CTkLabel(self.title_frame, text="MEGA ASSISTANT",
                                       font=("Arial", 28, "bold"), text_color=("#00BFFF", "#87CEEB"))
        self.title_label.pack(anchor="w")

        self.subtitle_label = ctk.CTkLabel(self.title_frame, text="Your AI Voice Companion",
                                          font=("Arial", 14), text_color="lightgray")
        self.subtitle_label.pack(anchor="w")

        # === MAIN CONTENT AREA ===
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=15)
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # Status bar
        self.status_frame = ctk.CTkFrame(self.main_frame, height=60, corner_radius=10)
        self.status_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        self.status_frame.grid_columnconfigure(1, weight=1)

        self.status_indicator = ctk.CTkFrame(self.status_frame, width=40, height=40, corner_radius=20)
        self.status_indicator.grid(row=0, column=0, padx=15, pady=10)

        self.status_icon = ctk.CTkLabel(self.status_indicator, text="💤", font=("Arial", 20))
        self.status_icon.place(relx=0.5, rely=0.5, anchor="center")

        self.status_text_frame = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        self.status_text_frame.grid(row=0, column=1, sticky="ew", padx=10)

        self.status_label = ctk.CTkLabel(self.status_text_frame, text="Idle - Say 'Hey Mega' to wake up",
                                        font=("Arial", 18, "bold"), anchor="w")
        self.status_label.pack(fill="x", pady=(8, 2))

        self.status_detail = ctk.CTkLabel(self.status_text_frame, text="Waiting for wake word...",
                                         font=("Arial", 13), text_color="gray", anchor="w")
        self.status_detail.pack(fill="x")

        self.progress = ctk.CTkProgressBar(self.status_frame, width=100, height=8, corner_radius=4)
        self.progress.grid(row=0, column=2, padx=15, pady=20, sticky="e")
        self.progress.set(0)

        # === CHAT/LOG AREA ===
        self.chat_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(0, weight=1)

        self.chat_header = ctk.CTkFrame(self.chat_frame, height=35, corner_radius=8)
        self.chat_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 2))

        self.chat_title = ctk.CTkLabel(self.chat_header, text="💬 Conversation Log",
                                      font=("Arial", 16, "bold"))
        self.chat_title.pack(side="left", padx=15, pady=6)

        self.clear_btn = ctk.CTkButton(self.chat_header, text="Clear", width=60, height=25,
                                      command=self.clear_chat, font=("Arial", 11))
        self.clear_btn.pack(side="right", padx=15, pady=6)

        self.text_frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        self.text_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(2, 10))
        self.text_frame.grid_columnconfigure(0, weight=1)
        self.text_frame.grid_rowconfigure(0, weight=1)

        self.text_widget = ctk.CTkTextbox(self.text_frame, corner_radius=8,
                                         font=("Consolas", 13), wrap="word")
        self.text_widget.grid(row=0, column=0, sticky="nsew")
        self.text_widget.configure(state="disabled")

        # === CONTROL BUTTONS ===
        self.control_frame = ctk.CTkFrame(self.root, height=60, corner_radius=15)
        self.control_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))

        self.wake_btn = ctk.CTkButton(self.control_frame, text="🎤 Wake Mega",
                                     command=self.manual_wake, height=38,
                                     font=("Arial", 14, "bold"))
        self.wake_btn.pack(side="left", padx=15, pady=12)

        self.settings_btn = ctk.CTkButton(self.control_frame, text="⚙️ Settings",
                                         width=110, height=38, font=("Arial", 12),
                                         command=self.open_settings)
        self.settings_btn.pack(side="right", padx=15, pady=12)

        self.add_message("🤖 Mega Assistant initialized! Say 'Hey Mega' or 'Mega' to wake me up.", "system")

    def setup_voice(self):
        self.r = sr.Recognizer()
        
        # Improved recognizer settings for better performance
        self.r.dynamic_energy_threshold = True
        self.r.energy_threshold = 300  # Adjust based on your environment
        self.r.pause_threshold = 0.8   # Seconds of silence before considering phrase complete
        self.r.phrase_threshold = 0.3  # Minimum seconds of speaking audio before we consider it a phrase
        self.r.non_speaking_duration = 0.8  # Seconds of non-speaking audio to keep on both sides
        
        # Initialize microphone
        try:
            # Test microphone
            with sr.Microphone() as source:
                self.r.adjust_for_ambient_noise(source, duration=1)
            self.add_message("Microphone initialized successfully!", "system", speak=False)
        except Exception as e:
            self.add_message(f"Microphone initialization failed: {e}", "system", speak=False)
            
        # Initialize text-to-speech
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 180)
            voices = self.engine.getProperty('voices')
            if voices:
                # Try to set a better voice if available
                self.engine.setProperty('voice', voices[0].id)
        except Exception as e:
            self.add_message(f"TTS initialization failed: {e}", "system", speak=False)
        
        self.wake_words = ["mega", "hey mega" , "mehga", "meha", "hey mehga", "hey meha"]
        self.apps = {
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

    def add_message(self, text, sender="mega", speak=True):
        """Add message to chat with timestamp and formatting"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if sender == "user":
            formatted_msg = f"[{timestamp}] 👤 You: {text}\n"
            color = "#4a9eff"
        elif sender == "system":
            formatted_msg = f"[{timestamp}] ⚡ System: {text}\n"
            color = "#ff9500"
        else:  # mega
            formatted_msg = f"[{timestamp}] 🤖 Mega: {text}\n"
            color = "#00d4aa"
        
        self.text_widget.configure(state='normal')
        self.text_widget.insert(ctk.END, formatted_msg)
        self.text_widget.see(ctk.END)
        self.text_widget.configure(state='disabled')
        
        if speak and sender == "mega":
            threading.Thread(target=lambda: (self.engine.say(text), self.engine.runAndWait()), 
                           daemon=True).start()

    def update_status(self, icon, text, detail="", progress_mode="determinate"):
        """Update status with smooth animations"""
        def update():
            self.status_icon.configure(text=icon)
            self.status_label.configure(text=text)
            self.status_detail.configure(text=detail)
            
            if progress_mode == "indeterminate":
                self.progress.configure(mode="indeterminate")
                self.progress.start()
            else:
                self.progress.stop()
                self.progress.configure(mode="determinate")
                self.progress.set(0 if progress_mode == "reset" else 1)
        
        self.root.after(0, update)

    def clear_chat(self):
        self.text_widget.configure(state='normal')
        self.text_widget.delete(1.0, ctk.END)
        self.text_widget.configure(state='disabled')
        self.add_message("Chat cleared!", "system", speak=False)

    def manual_wake(self):
        if not self.assistant_active:
            self.add_message("Mega manually activated! Ready for commands.", "system")
            self.update_status("✅", "Mega is awake", "Listening for commands...", "reset")
            # Start listening immediately in a separate thread
            threading.Thread(target=self.manual_command_mode, daemon=True).start()
        else:
            self.add_message("Mega is already awake!", "system", speak=False)

    def manual_command_mode(self):
        """Special mode for manual activation - takes one command then goes back to sleep"""
        self.assistant_active = True
        cmd = self.take_command_blocking()
        
        if cmd:
            if any(word in cmd for word in ["exit", "quit", "stop", "sleep", "goodbye"]):
                self.add_message("Going back to sleep...")
                self.assistant_active = False
                self.update_status("💤", "Idle", "Say 'Hey Mega' to wake up", "reset")
                return
                
            if not self.handle_command(cmd):
                self.add_message(f"I don't know how to do that. Searching Google for '{cmd}'")
                webbrowser.open(f"https://www.google.com/search?q={cmd}")
            
            # Auto sleep after command unless user says otherwise
            self.add_message("Command completed. Going back to sleep...")
            self.assistant_active = False
            self.update_status("💤", "Idle", "Say 'Hey Mega' to wake up", "reset")
        else:
            self.assistant_active = False
            self.update_status("💤", "Idle", "Say 'Hey Mega' to wake up", "reset")

    def open_settings(self):
        """Open settings window"""
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("⚙️ Mega Settings")
        settings_window.geometry("400x350")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Settings header
        header = ctk.CTkLabel(settings_window, text="⚙️ MEGA SETTINGS", 
                             font=("Arial", 20, "bold"))
        header.pack(pady=20)
        
        # Theme settings
        theme_frame = ctk.CTkFrame(settings_window)
        theme_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(theme_frame, text="🎨 Theme:", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(10,5))
        
        theme_var = ctk.StringVar(value=self.current_theme)
        theme_menu = ctk.CTkOptionMenu(theme_frame, values=["dark", "light"], 
                                      variable=theme_var, command=self.change_theme)
        theme_menu.pack(padx=10, pady=(0,10), anchor="w")
        
        # Zoom settings
        zoom_frame = ctk.CTkFrame(settings_window)
        zoom_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(zoom_frame, text="🔍 Zoom Level:", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(10,5))
        
        zoom_var = ctk.StringVar(value=f"{int(self.zoom_level * 100)}%")
        zoom_menu = ctk.CTkOptionMenu(zoom_frame, values=["80%", "90%", "100%", "110%", "120%", "130%"], 
                                     variable=zoom_var, command=self.change_zoom)
        zoom_menu.pack(padx=10, pady=(0,10), anchor="w")
        
        # View mode settings
        view_frame = ctk.CTkFrame(settings_window)
        view_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(view_frame, text="📱 View Mode:", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(10,5))
        
        view_var = ctk.StringVar(value=self.view_mode)
        view_menu = ctk.CTkOptionMenu(view_frame, values=["desktop", "phone"], 
                                     variable=view_var, command=self.change_view_mode)
        view_menu.pack(padx=10, pady=(0,10), anchor="w")
        
        # Close button
        close_btn = ctk.CTkButton(settings_window, text="✅ Apply & Close", 
                                 command=settings_window.destroy, height=35)
        close_btn.pack(pady=20)

    def change_theme(self, theme):
        """Change application theme"""
        self.current_theme = theme
        ctk.set_appearance_mode(theme)
        self.add_message(f"Theme changed to {theme} mode", "system", speak=False)

    def change_zoom(self, zoom_str):
        """Change zoom level"""
        zoom_value = int(zoom_str.replace("%", "")) / 100
        self.zoom_level = zoom_value
        
        # Apply zoom to fonts
        self.apply_zoom()
        self.add_message(f"Zoom level changed to {zoom_str}", "system", speak=False)

    def apply_zoom(self):
        """Apply zoom to all UI elements"""
        base_title_size = 28
        base_status_size = 18
        base_detail_size = 13
        base_chat_size = 13
        
        # Update fonts based on zoom level
        self.title_label.configure(font=("Arial", int(base_title_size * self.zoom_level), "bold"))
        self.status_label.configure(font=("Arial", int(base_status_size * self.zoom_level), "bold"))
        self.status_detail.configure(font=("Arial", int(base_detail_size * self.zoom_level)))
        self.text_widget.configure(font=("Consolas", int(base_chat_size * self.zoom_level)))

    def change_view_mode(self, mode):
        """Change view mode between desktop and phone"""
        self.view_mode = mode
        if mode == "phone":
            # Phone mode - compact layout
            self.root.geometry("350x500")
            self.root.minsize(300, 400)
        else:
            # Desktop mode - full layout
            self.root.geometry("700x600")
            self.root.minsize(600, 500)
        
        self.add_message(f"View mode changed to {mode}", "system", speak=False)

    def take_command_blocking(self):
        self.update_status("🎤", "Listening...", "Speak now", "indeterminate")
        try:
            with sr.Microphone() as source:
                # Listen for longer and adjust settings for better recognition
                audio = self.r.listen(source, timeout=5, phrase_time_limit=6)
        except sr.WaitTimeoutError:
            self.add_message("No speech detected - timeout", "system", speak=False)
            self.update_status("⚠️", "No speech detected", "Try again", "reset")
            return ""
        
        try:
            self.update_status("🔄", "Processing...", "Recognizing speech", "indeterminate")
            command = self.r.recognize_google(audio).lower()
            self.add_message(command, "user", speak=False)
            self.update_status("✅", "Command received", f"Processing: {command[:30]}...", "reset")
            return command
        except sr.UnknownValueError:
            self.add_message("Could not understand speech. Please try again.", "system")
            self.update_status("⚠️", "Could not understand", "Please repeat", "reset")
        except sr.RequestError as e:
            self.add_message(f"Speech recognition service error: {e}", "system")
            self.update_status("❌", "Service error", "Check internet connection", "reset")
        except Exception as e:
            self.add_message(f"Recognition error: {e}", "system", speak=False)
            self.update_status("❌", "Error occurred", "Try again", "reset")
        
        return ""

    def find_best_match(self, command, choices):
        match, score, _ = process.extractOne(command, choices)
        return match if score > 60 else None

    def handle_command(self, cmd: str) -> bool:
        """Take a text command and perform the appropriate action"""
        cmd = cmd.lower()

    # --- CLOSE COMMANDS ---
        if cmd.startswith("close "):
            app_name = cmd.replace("close ", "", 1).strip()
            best = self.find_best_match(app_name, self.apps.keys())
            if best:
                self.add_message(f"Closing {best}...")
                if best in self.opened_processes and self.opened_processes[best].poll() is None:
                    try:
                        self.opened_processes[best].terminate()
                        self.add_message(f"{best} closed successfully.")
                    except Exception as e:
                        self.add_message(f"Error closing {best}: {e}")
                else:
                    try:
                        subprocess.call(f"taskkill /IM {best}.exe /F", shell=True)
                        self.add_message(f"{best} closed via taskkill.")
                    except Exception as e:
                        self.add_message(f"Failed to close {best}: {e}")
                return True
            else:
                self.add_message(f"I couldn't find an app named {app_name} to close.")
                return True

        # --- Spotify ---
        if "spotify" in cmd:
            self.add_message("Opening Spotify...")
            try:
                proc = subprocess.Popen(self.apps["spotify"], shell=True)
                self.opened_processes["spotify"] = proc
                threading.Timer(
                    2.0,
                    lambda: (
                        webbrowser.open("https://open.spotify.com/")
                        if proc.poll() is not None else None
                    )
                ).start()
            except Exception:
                webbrowser.open("https://open.spotify.com/")
            return True

        # --- WhatsApp ---
        if "whatsapp" in cmd:
            self.add_message("Opening WhatsApp...")
            try:
                proc = subprocess.Popen("start whatsapp:", shell=True)
                self.opened_processes["whatsapp"] = proc
            except Exception:
                webbrowser.open("https://web.whatsapp.com")
            return True

        # --- Time ---
        if "time" in cmd:
            now = datetime.now()
            self.add_message(f"The current time is {now.strftime('%H:%M:%S')}")
            return True

        # --- Weather ---
        if "weather" in cmd:
            city = "Pune"  # default
            parts = cmd.split()
            for i, word in enumerate(parts):
                if word.lower() == "in" and i + 1 < len(parts):
                    city = " ".join(parts[i + 1:])
                    break
            try:
                url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.api_key}&units=metric"
                response = requests.get(url, timeout=5).json()
                if response.get("cod") == 200:
                    temp = response["main"]["temp"]
                    desc = response["weather"][0]["description"]
                    self.add_message(f"The weather in {city} is {temp}°C with {desc}")
                else:
                    self.add_message(f"Could not fetch weather for {city}")
            except requests.exceptions.RequestException:
                self.add_message("Failed to get weather information. Check your internet connection.")
            return True

        # --- YouTube ---
        if "youtube" in cmd:
            self.add_message("Opening YouTube…")
            open_youtube()
            return True

        # --- Google search ---
        if cmd.startswith("google "):
            query = cmd.replace("google ", "", 1).strip()
            if query:
                self.add_message(f"Searching Google for {query}…")
                webbrowser.open(f"https://www.google.com/search?q={query}")
            else:
                self.add_message("Opening Google…")
                webbrowser.open("https://www.google.com")
            return True

        # --- Other apps ---
        best = self.find_best_match(cmd, self.apps.keys())
        if best:
            self.add_message(f"Opening {best}")
            try:
                proc = subprocess.Popen(self.apps[best], shell=True)
                self.opened_processes[best] = proc
            except Exception:
                # fallback: if app entry is 'web' open its web page
                if best == "youtube":
                    open_youtube()
                else:
                    webbrowser.open(f"https://www.google.com/search?q={best}")
            return True
        
        # --- Close Control Panel ---
        if "close control panel" in cmd:
            if not close_window("Control Panel"):
                subprocess.run("taskkill /f /im control.exe", shell=True)
            self.add_message("Closed Control Panel.")
            return True

        # --- Close Settings ---
        if "close settings" in cmd:
            if not close_window("Settings"):
                subprocess.run("taskkill /f /im SystemSettings.exe", shell=True)
            self.add_message("Closed Settings.")
            return True


        return False

    def run_assistant_loop(self):
        self.assistant_active = True
        self.update_status("✅", "Mega is awake", "Ready for commands", "reset")
        
        while self.assistant_active:
            cmd = self.take_command_blocking()
            if not cmd:
                continue
                
            if any(word in cmd for word in ["exit", "quit", "stop", "sleep", "goodbye"]):
                self.add_message("Goodbye! Going back to sleep...")
                self.assistant_active = False
                self.update_status("💤", "Idle", "Say 'Hey Mega' to wake up", "reset")
                break
                
            if not self.handle_command(cmd):
                self.add_message(f"I don't know how to do that. Searching Google for '{cmd}'")
                webbrowser.open(f"https://www.google.com/search?q={cmd}")

    def listen_for_wake_word(self):
        # Adjust for ambient noise once at startup
        try:
            with sr.Microphone() as source:
                self.r.adjust_for_ambient_noise(source, duration=1.0)
        except Exception as e:
            self.add_message(f"Microphone setup error: {e}", "system", speak=False)
            
        while True:
            if not self.assistant_active:
                try:
                    # Listen for wake word
                    with sr.Microphone() as source:
                        audio = self.r.listen(source, timeout=1, phrase_time_limit=3)
                    text = self.r.recognize_google(audio).lower()
                    
                    if any(word in text for word in self.wake_words):
                        self.add_message("Wake word detected! Mega is now awake and ready!", "system")
                        threading.Thread(target=self.run_assistant_loop, daemon=True).start()
                        
                except sr.WaitTimeoutError:
                    pass  # Normal timeout, continue listening
                except sr.UnknownValueError:
                    pass  # Couldn't understand, continue listening
                except sr.RequestError as e:
                    self.add_message(f"Speech service error: {e}", "system", speak=False)
                    time.sleep(5)  # Wait before retrying
                except Exception as e:
                    self.add_message(f"Microphone error: {e}", "system", speak=False)
                    time.sleep(2)
            else:
                # When assistant is active, sleep longer to avoid interference
                time.sleep(0.5)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = MegaAssistant()
    app.run()
