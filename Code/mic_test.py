import speech_recognition as sr
# Initialize recognizer
r = sr.Recognizer()

# Capture microphone input
with sr.Microphone() as source:
    print("Say something...")
    audio = r.listen(source)

# Recognize speech using Google API
try:
    text = r.recognize_google(audio)
    print("You said:", text)
except Exception as e:
    print("Sorry, I could not understand. Error:", e)
