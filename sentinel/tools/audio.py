import speech_recognition as sr
import threading


def listen(timeout=5):
    def _listen():
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=8)
            return recognizer.recognize_google(audio)

    try:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as ex:
            future = ex.submit(_listen)
            return f"User said: '{future.result(timeout=timeout+2)}'"
    except concurrent.futures.TimeoutError:
        return "Voice timeout."
    except Exception as e:
        return f"Voice error: {e}"



def listen_background(callback):
    """
    Starts a background listener for a hotword (Advanced).
    """
    # Future
    pass