"""
Voice Control for Desktop Automation Agent

Requires:
    pip install SpeechRecognition pyaudio

Usage:
    python voice_control.py
"""

import requests
import time

try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    print("SpeechRecognition not installed. Run: pip install SpeechRecognition pyaudio")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False


class VoiceControl:
    def __init__(self, backend_url="http://localhost:5001"):
        self.backend_url = backend_url
        self.wake_words = ['hey agent', 'hello agent', 'agent']

        if SPEECH_AVAILABLE:
            self.recognizer = sr.Recognizer()

        if TTS_AVAILABLE:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty('voices')
            if len(voices) > 1:
                self.engine.setProperty('voice', voices[1].id)
            self.engine.setProperty('rate', 180)

        print("Voice Control initialized")
        print("Say 'Hey Agent' followed by your command")

    def speak(self, text):
        """Text-to-speech output."""
        print(f"Agent: {text}")
        if TTS_AVAILABLE:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                print(f"TTS error: {e}")

    def listen(self, timeout=5):
        """Listen for voice input."""
        if not SPEECH_AVAILABLE:
            return None

        try:
            with sr.Microphone() as source:
                print("Listening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout)

            text = self.recognizer.recognize_google(audio)
            print(f"Heard: {text}")
            return text.lower()

        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"Listen error: {e}")
            return None

    def execute_command(self, command):
        """Send command to the agent backend."""
        try:
            self.speak("On it")

            response = requests.post(
                f"{self.backend_url}/agent",
                json={"task": command},
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.speak("Done")
                else:
                    error = data.get('error', 'Unknown error')
                    self.speak(f"Sorry, {error}")
            else:
                self.speak("Backend error")

        except requests.exceptions.ConnectionError:
            self.speak("Backend is not running. Start agent.py first.")
        except requests.exceptions.Timeout:
            self.speak("Request timed out")
        except Exception as e:
            self.speak("Error executing command")
            print(f"Execute error: {e}")

    def start_listening(self):
        """Main voice control loop."""
        if not SPEECH_AVAILABLE:
            print("ERROR: SpeechRecognition not available")
            print("Install with: pip install SpeechRecognition pyaudio")
            return

        self.speak("Voice control active. Say hey agent to give commands")

        while True:
            try:
                text = self.listen(timeout=10)

                if text and any(wake in text for wake in self.wake_words):
                    # Remove wake word from command
                    command = text
                    for wake in self.wake_words:
                        command = command.replace(wake, '').strip()

                    if command:
                        print(f"Command: {command}")
                        self.execute_command(command)
                    else:
                        # Wake word detected but no command - ask for input
                        self.speak("Yes?")
                        command = self.listen(timeout=10)
                        if command:
                            self.execute_command(command)
                        else:
                            self.speak("I didn't catch that")

                time.sleep(0.5)

            except KeyboardInterrupt:
                print("\nVoice control stopped")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)


if __name__ == '__main__':
    print("=" * 50)
    print("VOICE CONTROL FOR DESKTOP AGENT")
    print("=" * 50)
    print()
    print("Examples:")
    print("  'Hey Agent, open calculator'")
    print("  'Hey Agent, take a screenshot'")
    print("  'Hey Agent, open notepad and type hello'")
    print()
    print("=" * 50)

    voice = VoiceControl()
    voice.start_listening()
