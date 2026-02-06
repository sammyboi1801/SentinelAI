import speech_recognition as sr
import threading
import time

_STOP_LISTENING = None

def listen(timeout=5):
    """
    Actively listens for a single command.
    Blocks until speech is finished or timeout is reached.
    """
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            print("🎤 Listening...")

            recognizer.adjust_for_ambient_noise(source, duration=0.5)

            try:
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                text = recognizer.recognize_google(audio)
                return f"User said: '{text}'"

            except sr.WaitTimeoutError:
                return "❌ Voice timeout: I didn't hear anything."
            except sr.UnknownValueError:
                return "❌ I couldn't understand that (Audio unclear)."
            except sr.RequestError:
                return "❌ Internet error: Could not reach Google Speech service."

    except OSError:
        return "❌ Microphone error: Is PyAudio installed? (pip install pyaudio)"
    except Exception as e:
        return f"❌ Voice System Error: {e}"


def listen_background(callback_func):
    """
    Starts a background thread that continuously listens for speech.
    When speech is detected, it calls 'callback_func(text)'.
    """
    global _STOP_LISTENING

    if _STOP_LISTENING:
        return "⚠️ Background listener is already running."

    try:
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()

        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)

        def _callback(recognizer, audio):
            try:
                text = recognizer.recognize_google(audio)
                if text:
                    callback_func(text)
            except sr.UnknownValueError:
                pass
            except sr.RequestError:
                print("⚠️ [Voice] Offline or API down.")

        _STOP_LISTENING = recognizer.listen_in_background(microphone, _callback)

        return "✅ Background listener started (Google Speech)."

    except Exception as e:
        return f"❌ Failed to start background listener: {e}"


def stop_background():
    """
    Stops the background listening thread.
    """
    global _STOP_LISTENING
    if _STOP_LISTENING:
        _STOP_LISTENING(wait_for_stop=False)
        _STOP_LISTENING = None
        return "🛑 Background listener stopped."
    return "Listener was not running."