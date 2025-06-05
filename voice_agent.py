#!/usr/bin/env python3
"""
voice_agent.py
===============
Simple voice interface for interacting with the JARVIS assistant.
Uses SpeechRecognition to capture microphone input and pyttsx3 for
text-to-speech output.
"""

from __future__ import annotations

import sys

try:
    import speech_recognition as sr
except ImportError as e:
    sys.exit("SpeechRecognition package is required. Install it with 'pip install SpeechRecognition pyaudio'.")

try:
    import pyttsx3
except ImportError:
    sys.exit("pyttsx3 package is required. Install it with 'pip install pyttsx3'.")

from core.orchestrator import Orchestrator


def main() -> None:
    try:
        orchestrator = Orchestrator()
    except Exception as e:
        print(f"Failed to initialize Orchestrator: {e}")
        return

    recognizer = sr.Recognizer()
    tts_engine = pyttsx3.init()

    print("\n🎙️  Voice interface ready! Say 'exit' to quit.\n")

    while True:
        with sr.Microphone() as source:
            print("Listening...")
            audio = recognizer.listen(source)

        try:
            user_input = recognizer.recognize_google(audio)
            print(f"User said: {user_input}")
        except sr.UnknownValueError:
            print("Could not understand audio. Please try again.")
            continue
        except sr.RequestError as e:
            print(f"Speech recognition service error: {e}")
            continue

        if user_input.lower() in {"exit", "quit", "stop"}:
            print("Exiting voice interface.")
            break

        response = orchestrator.chat(user_input)
        print(f"JARVIS: {response}\n")

        tts_engine.say(response)
        tts_engine.runAndWait()


if __name__ == "__main__":
    main()
