import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')

for idx, voice in enumerate(voices):
    print(idx, voice.id)


engine.setProperty('voice', voices[0].id)
engine.say("Hello! This is a voice test.")
engine.runAndWait()
