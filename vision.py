"""
Vision Module - Screen capture and optional AI understanding.
"""

import os
import pyautogui
from datetime import datetime
from PIL import Image


def capture_screen(region=None) -> str:
    """
    Take a screenshot and save it.

    Args:
        region: Optional tuple (x, y, width, height) for partial capture

    Returns:
        Path to saved screenshot
    """
    # Create screenshots directory
    screenshots_dir = os.path.join(os.path.expanduser('~'), 'Desktop', 'screenshots')
    os.makedirs(screenshots_dir, exist_ok=True)

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(screenshots_dir, f"screenshot_{timestamp}.png")

    # Capture
    if region:
        screenshot = pyautogui.screenshot(region=region)
    else:
        screenshot = pyautogui.screenshot()

    screenshot.save(filepath)
    return filepath


def get_screen_size() -> tuple:
    """Get screen dimensions."""
    return pyautogui.size()


def describe_screen(image_path: str, llm_func=None) -> str:
    """
    Use vision LLM to describe what's on screen.

    Args:
        image_path: Path to screenshot
        llm_func: Optional function to call vision LLM

    Returns:
        Description of screen contents
    """
    if not os.path.exists(image_path):
        return "Screenshot not found"

    if llm_func:
        # Use provided LLM function for vision
        return llm_func(image_path)

    return f"Screenshot saved: {image_path}"


# Simple test
if __name__ == "__main__":
    path = capture_screen()
    print(f"Screenshot saved: {path}")
    print(f"Screen size: {get_screen_size()}")
