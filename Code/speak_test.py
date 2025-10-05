# import pyttsx3

# engine = pyttsx3.init()

# engine.say("Hello! I am your desktop assistant. I can talk now.")
# engine.runAndWait()

import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')

for idx, voice in enumerate(voices):
    print(idx, voice.id)

# pick one voice
engine.setProperty('voice', voices[0].id)
engine.say("Hello! This is a voice test.")
engine.runAndWait()
