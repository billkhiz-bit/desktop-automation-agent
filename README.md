# Desktop Automation Agent

AI-powered desktop automation with planning and multi-step task execution for Windows.

## Features

- **Multi-Provider LLM Support** - Ollama, OpenAI, Anthropic, Google Gemini
- **Smart Planning** - LLM breaks natural language into executable steps
- **Desktop Control** - Open apps, type text, click, keyboard shortcuts
- **Vision** - Screenshot capture for verification
- **Voice Control** - Hands-free operation with wake word detection

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Choose Your LLM Provider

**Option A: Ollama (Free, Local)**
```bash
ollama pull qwen2.5:7b
```

**Option B: Cloud Providers**
```bash
# OpenAI
export OPENAI_API_KEY=your_key

# Anthropic
export ANTHROPIC_API_KEY=your_key

# Google Gemini
export GEMINI_API_KEY=your_key
```

### 3. Run

```bash
python agent.py
```

## Example Commands

```
"Open calculator"
"Open notepad and type Hello World"
"Open Chrome and search for Python tutorials"
"Take a screenshot"
```

## How It Works

```
User: "Open notepad and type hello"
                ↓
         [LLM Planning]
                ↓
    1. open_app("notepad")
    2. wait(1 second)
    3. type("hello")
                ↓
        [Execute Steps]
                ↓
            Done!
```

The agent uses the LLM to break down natural language commands into discrete automation steps, then executes them sequentially using PyAutoGUI.

## Project Structure

| File | Description |
|------|-------------|
| `agent.py` | Core agent with LLM integration, task planning, and execution engine. Supports Ollama/OpenAI/Anthropic/Gemini. Runs FastAPI server on port 5001. |
| `ui.py` | PyQt5 chat interface. Dark theme, draggable window, async requests. Optional - agent works standalone. |
| `vision.py` | Screen capture utility. Saves timestamped screenshots to ~/Desktop/screenshots. |
| `voice_control.py` | Voice interface with "Hey Agent" wake word. Uses SpeechRecognition + pyttsx3 for TTS. |
| `requirements.txt` | Core deps: fastapi, pyautogui, requests, Pillow |
| `data/config.example.json` | Configuration template for LLM provider and model selection |

## Configuration

Copy `data/config.example.json` to `data/config.json`:

```json
{
  "provider": "ollama",
  "model": "qwen2.5:7b",
  "api_key": null
}
```

| Provider | Models |
|----------|--------|
| ollama | qwen2.5:7b, llama3, mistral, phi3 |
| openai | gpt-4o-mini, gpt-4o, gpt-3.5-turbo |
| anthropic | claude-3-haiku, claude-3-sonnet |
| gemini | gemini-2.0-flash, gemini-pro |

## API

The agent exposes a REST API on `http://localhost:5001`:

```bash
# Health check
curl http://localhost:5001/health

# Execute task
curl -X POST http://localhost:5001/agent \
  -H "Content-Type: application/json" \
  -d '{"task": "open calculator"}'
```

## Optional Features

**Chat UI:**
```bash
pip install PyQt5
python ui.py
```

**Voice Control:**
```bash
pip install SpeechRecognition pyaudio pyttsx3
python voice_control.py
# Say "Hey Agent, open calculator"
```

## Requirements

- Windows 10/11
- Python 3.10+
- LLM provider (Ollama recommended for free local inference)

## License

MIT
