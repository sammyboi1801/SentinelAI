import base64
import os
import time
import cv2
import pyautogui
from litellm import completion
from sentinel.core.config import ConfigManager
from sentinel.paths import USER_DATA_DIR


SCREENSHOT_PATH = USER_DATA_DIR / "vision_cache_screen.png"
WEBCAM_PATH = USER_DATA_DIR / "vision_cache_cam.png"


def get_llm_config():
    """
    Loads keys and formats the model string for LiteLLM.
    """
    cfg = ConfigManager()
    provider = cfg.get("llm.provider", "openai")
    model = cfg.get("llm.model", "gpt-4o")

    if provider == "openai":
        os.environ["OPENAI_API_KEY"] = cfg.get_key("openai") or ""
    elif provider == "anthropic":
        os.environ["ANTHROPIC_API_KEY"] = cfg.get_key("anthropic") or ""
    elif provider == "groq":
        os.environ["GROQ_API_KEY"] = cfg.get_key("groq") or ""

    return f"{provider}/{model}"


def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _analyze_image(image_path, prompt):
    try:
        full_model = get_llm_config()
        base64_img = encode_image(image_path)

        message = {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_img}"}
                }
            ]
        }

        response = completion(
            model=full_model,
            messages=[message],
            max_tokens=500
        )

        return response.choices[0].message.content

    except Exception as e:
        return (
            f"❌ Vision Error: {e}\n"
            f"Tip: Ensure your model ({full_model}) supports image inputs."
        )


def analyze_screen(prompt="Describe the contents of this screen"):
    try:
        pyautogui.screenshot(str(SCREENSHOT_PATH))
        result = _analyze_image(SCREENSHOT_PATH, prompt)
        return f"🖥️ [Screen Analysis]: {result}"
    except Exception as e:
        return f"❌ Screen capture error: {e}"


def capture_webcam(prompt="Describe what you see"):
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return "❌ Error: Could not open webcam."

        for _ in range(10):
            cap.read()

        ret, frame = cap.read()
        cap.release()

        if not ret:
            return "❌ Error: Failed to capture image."

        cv2.imwrite(str(WEBCAM_PATH), frame)

        result = _analyze_image(WEBCAM_PATH, prompt)
        return f"📷 [Webcam Analysis]: {result}"

    except Exception as e:
        return f"❌ Webcam error: {e}"