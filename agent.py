"""
Desktop Automation Agent
AI-powered desktop automation with vision and multi-step task execution.
Supports multiple LLM providers: Ollama, OpenAI, Anthropic, Google Gemini.
"""

import os
import json
import time
import subprocess
import re
import pyautogui
import requests
from typing import Dict, List, Optional, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Disable pyautogui failsafe for automation
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================
# CONFIGURATION
# ============================================

DEFAULT_CONFIG = {
    "provider": "ollama",  # ollama, openai, anthropic, gemini
    "model": "qwen2.5:7b",
    "vision_model": "llava:v1.6",
    "api_key": None,
    "ollama_url": "http://localhost:11434",
}

def load_config() -> dict:
    """Load configuration from file or environment."""
    config = DEFAULT_CONFIG.copy()

    # Load from config file
    if os.path.exists('data/config.json'):
        try:
            with open('data/config.json', 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            print(f"Config load error: {e}")

    # Environment overrides
    if os.environ.get('LLM_PROVIDER'):
        config['provider'] = os.environ['LLM_PROVIDER']
    if os.environ.get('LLM_MODEL'):
        config['model'] = os.environ['LLM_MODEL']
    if os.environ.get('OPENAI_API_KEY'):
        config['api_key'] = os.environ['OPENAI_API_KEY']
        config['provider'] = 'openai'
    if os.environ.get('ANTHROPIC_API_KEY'):
        config['api_key'] = os.environ['ANTHROPIC_API_KEY']
        config['provider'] = 'anthropic'
    if os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY'):
        config['api_key'] = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
        config['provider'] = 'gemini'

    return config

CONFIG = load_config()


# ============================================
# LLM PROVIDERS
# ============================================

def call_ollama(prompt: str, model: str = None) -> str:
    """Call Ollama local LLM."""
    model = model or CONFIG.get('model', 'qwen2.5:7b')
    url = CONFIG.get('ollama_url', 'http://localhost:11434')

    try:
        response = requests.post(
            f"{url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60
        )
        if response.status_code == 200:
            return response.json().get('response', '')
    except Exception as e:
        print(f"Ollama error: {e}")
    return None


def call_openai(prompt: str, model: str = None) -> str:
    """Call OpenAI API."""
    api_key = CONFIG.get('api_key')
    if not api_key:
        return None

    model = model or CONFIG.get('model', 'gpt-4o-mini')

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 1024
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"OpenAI error: {e}")
    return None


def call_anthropic(prompt: str, model: str = None) -> str:
    """Call Anthropic API."""
    api_key = CONFIG.get('api_key')
    if not api_key:
        return None

    model = model or CONFIG.get('model', 'claude-3-haiku-20240307')

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": model,
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()['content'][0]['text']
    except Exception as e:
        print(f"Anthropic error: {e}")
    return None


def call_gemini(prompt: str, model: str = None) -> str:
    """Call Google Gemini API."""
    api_key = CONFIG.get('api_key')
    if not api_key:
        return None

    model = model or CONFIG.get('model', 'gemini-2.0-flash')

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        response = requests.post(
            url,
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1024}
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Gemini error: {e}")
    return None


def call_llm(prompt: str) -> str:
    """Call the configured LLM provider."""
    provider = CONFIG.get('provider', 'ollama')

    if provider == 'ollama':
        return call_ollama(prompt)
    elif provider == 'openai':
        return call_openai(prompt)
    elif provider == 'anthropic':
        return call_anthropic(prompt)
    elif provider == 'gemini':
        return call_gemini(prompt)
    else:
        # Default to Ollama
        return call_ollama(prompt)


# ============================================
# DESKTOP AUTOMATION TOOLS
# ============================================

def open_application(app_name: str) -> dict:
    """Open an application by name."""
    app_map = {
        'notepad': 'notepad.exe',
        'calculator': 'calc.exe',
        'chrome': 'chrome.exe',
        'firefox': 'firefox.exe',
        'edge': 'msedge.exe',
        'explorer': 'explorer.exe',
        'word': 'winword.exe',
        'excel': 'excel.exe',
        'powerpoint': 'powerpnt.exe',
        'outlook': 'outlook.exe',
        'vscode': 'code',
        'terminal': 'wt.exe',
        'cmd': 'cmd.exe',
        'powershell': 'powershell.exe',
    }

    app_lower = app_name.lower().strip()
    exe = app_map.get(app_lower, app_name)

    try:
        subprocess.Popen(exe, shell=True)
        time.sleep(1.5)
        return {'success': True, 'message': f'Opened {app_name}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def type_text(text: str) -> dict:
    """Type text using keyboard."""
    try:
        pyautogui.typewrite(text, interval=0.02) if text.isascii() else pyautogui.write(text)
        return {'success': True, 'message': f'Typed: {text[:50]}...'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def press_key(key: str) -> dict:
    """Press a keyboard key."""
    try:
        pyautogui.press(key)
        return {'success': True, 'message': f'Pressed: {key}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def hotkey(*keys) -> dict:
    """Press a keyboard shortcut."""
    try:
        pyautogui.hotkey(*keys)
        return {'success': True, 'message': f'Hotkey: {"+".join(keys)}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def click(x: int = None, y: int = None) -> dict:
    """Click at position or current cursor location."""
    try:
        if x is not None and y is not None:
            pyautogui.click(x, y)
        else:
            pyautogui.click()
        return {'success': True, 'message': f'Clicked at {pyautogui.position()}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def wait(seconds: float) -> dict:
    """Wait for specified seconds."""
    time.sleep(seconds)
    return {'success': True, 'message': f'Waited {seconds}s'}


def screenshot() -> str:
    """Take a screenshot and return the path."""
    try:
        from vision import capture_screen
        return capture_screen()
    except:
        path = os.path.join(os.path.expanduser('~'), 'screenshot.png')
        pyautogui.screenshot(path)
        return path


# ============================================
# AI PLANNING & EXECUTION
# ============================================

PLAN_PROMPT = '''You are a desktop automation agent. Create a step-by-step plan to accomplish this task.

TASK: "{task}"

AVAILABLE ACTIONS:
- open_app(name): Open an application (notepad, chrome, excel, calculator, etc.)
- type(text): Type text
- press(key): Press a key (enter, tab, escape, etc.)
- hotkey(key1, key2): Press keyboard shortcut (ctrl, c for copy)
- click(x, y): Click at screen position
- wait(seconds): Wait for app to load
- screenshot(): Take screenshot to verify

Return a JSON array of steps. Each step has: action, params, description.

Example for "Open notepad and type hello":
[
  {"action": "open_app", "params": {"name": "notepad"}, "description": "Open Notepad"},
  {"action": "wait", "params": {"seconds": 1}, "description": "Wait for Notepad to load"},
  {"action": "type", "params": {"text": "hello"}, "description": "Type hello"}
]

Return ONLY valid JSON array, no other text.'''


def create_plan(task: str) -> List[dict]:
    """Use LLM to create an execution plan."""
    prompt = PLAN_PROMPT.format(task=task)
    response = call_llm(prompt)

    if not response:
        return None

    # Extract JSON from response
    try:
        # Clean up response
        response = response.strip()
        response = re.sub(r'^```json?\s*', '', response)
        response = re.sub(r'\s*```$', '', response)

        plan = json.loads(response)
        return plan if isinstance(plan, list) else None
    except json.JSONDecodeError as e:
        print(f"Plan parse error: {e}")
        return None


def execute_step(step: dict) -> dict:
    """Execute a single step from the plan."""
    action = step.get('action', '')
    params = step.get('params', {})

    try:
        if action == 'open_app':
            return open_application(params.get('name', ''))
        elif action == 'type':
            return type_text(params.get('text', ''))
        elif action == 'press':
            return press_key(params.get('key', ''))
        elif action == 'hotkey':
            keys = params.get('keys', [])
            if isinstance(keys, str):
                keys = [k.strip() for k in keys.split(',')]
            return hotkey(*keys)
        elif action == 'click':
            return click(params.get('x'), params.get('y'))
        elif action == 'wait':
            return wait(params.get('seconds', 1))
        elif action == 'screenshot':
            path = screenshot()
            return {'success': True, 'message': f'Screenshot saved: {path}', 'path': path}
        else:
            return {'success': False, 'error': f'Unknown action: {action}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def execute_plan(plan: List[dict]) -> dict:
    """Execute all steps in the plan."""
    results = []

    for i, step in enumerate(plan):
        desc = step.get('description', f'Step {i+1}')
        print(f"  [{i+1}/{len(plan)}] {desc}")

        result = execute_step(step)
        results.append({
            'step': i + 1,
            'description': desc,
            'success': result.get('success', False),
            'message': result.get('message') or result.get('error')
        })

        if not result.get('success'):
            break

        time.sleep(0.2)  # Small delay between steps

    success = all(r['success'] for r in results)
    return {
        'success': success,
        'results': results,
        'message': 'All steps completed' if success else 'Execution stopped due to error'
    }


# ============================================
# MAIN PROCESSOR
# ============================================

def process(user_input: str) -> dict:
    """Process user input and execute task."""
    user_input = user_input.strip()

    if not user_input:
        return {'success': False, 'error': 'No input provided'}

    # Help command
    if user_input.lower() in ['help', '?', 'hi', 'hello']:
        return {
            'success': True,
            'message': '''DESKTOP AUTOMATION AGENT

Just describe what you want to do:

Examples:
  "Open calculator"
  "Open notepad and type Hello World"
  "Open Chrome and search for Python tutorials"
  "Take a screenshot"

The agent will plan and execute the steps automatically.

Powered by: ''' + CONFIG.get('provider', 'ollama').upper()
        }

    # Quick commands (no LLM needed)
    lower = user_input.lower()

    if lower.startswith('open '):
        app = user_input[5:].strip()
        return open_application(app)

    if lower == 'screenshot':
        path = screenshot()
        return {'success': True, 'message': f'Screenshot saved: {path}'}

    # Complex task - use LLM planning
    print(f"\n[TASK] {user_input}")
    print("[PLANNING]...")

    plan = create_plan(user_input)

    if not plan:
        return {
            'success': False,
            'error': 'Could not create plan. Check your LLM configuration.'
        }

    print(f"[PLAN] {len(plan)} steps")
    print("[EXECUTING]...")

    result = execute_plan(plan)

    # Format response
    steps_summary = '\n'.join([
        f"  {'✓' if r['success'] else '✗'} {r['description']}"
        for r in result.get('results', [])
    ])

    return {
        'success': result['success'],
        'message': f"Task: {user_input}\n\nSteps:\n{steps_summary}\n\n{result['message']}"
    }


# ============================================
# API ENDPOINTS
# ============================================

class AgentRequest(BaseModel):
    task: Optional[str] = None
    query: Optional[str] = None
    message: Optional[str] = None

class AgentResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


@app.get("/health")
def health():
    return {
        "status": "ok",
        "provider": CONFIG.get('provider'),
        "model": CONFIG.get('model')
    }


@app.get("/config")
def get_config():
    safe_config = CONFIG.copy()
    if safe_config.get('api_key'):
        safe_config['api_key'] = '***hidden***'
    return safe_config


@app.post("/agent")
async def agent(req: AgentRequest):
    task = req.task or req.query or req.message or ""

    if not task:
        return AgentResponse(success=False, error="No input provided")

    result = process(task)

    return AgentResponse(
        success=result.get('success', False),
        message=result.get('message'),
        error=result.get('error')
    )


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    print(f"""
{'='*50}
DESKTOP AUTOMATION AGENT
{'='*50}
Provider: {CONFIG.get('provider', 'ollama').upper()}
Model: {CONFIG.get('model', 'qwen2.5:7b')}
Server: http://localhost:5001
{'='*50}

Ready for commands!
    """)

    uvicorn.run(app, host="0.0.0.0", port=5001)
