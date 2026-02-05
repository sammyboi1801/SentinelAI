import base64
import os
import pyautogui
import cv2
from litellm import completion
from sentinel.core.config import ConfigManager


def get_llm_env():
    """
    Dynamically load latest keys into env for LiteLLM.
    """
    cfg = ConfigManager()
    provider = cfg.get("llm.provider")
    model = cfg.get("llm.model")

    if provider == "openai":
        os.environ["OPENAI_API_KEY"] = cfg.get_key("openai") or ""
    elif provider == "anthropic":
        os.environ["ANTHROPIC_API_KEY"] = cfg.get_key("anthropic") or ""
    elif provider == "groq":
        os.environ["GROQ_API_KEY"] = cfg.get_key("groq") or ""

    full_model = f"{provider}/{model}"
    return full_model


def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _analyze_image(image_path, prompt):
    try:
        full_model = get_llm_env()
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
            f"Vision Error: {e}\n"
            f"Tip: Ensure model supports vision "
            f"(e.g. gpt-4o, claude-3-5-sonnet, llava)."
        )


def analyze_screen(prompt="Describe the contents of this screen"):
    screenshot_path = "temp_vision.png"
    try:
        pyautogui.screenshot(screenshot_path)
        result = _analyze_image(screenshot_path, prompt)
        return f"[Vision Result]: {result}"
    except Exception as e:
        return f"Screen capture error: {e}"


def capture_webcam(prompt="Describe what you see"):
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return "Error: Could not open webcam."

        ret, frame = cap.read()
        cap.release()

        if not ret:
            return "Error: Failed to capture image."

        filename = "temp_webcam.png"
        cv2.imwrite(filename, frame)

        result = _analyze_image(filename, prompt)
        return f"[Webcam Result]: {result}"

    except Exception as e:
        return f"Webcam error: {e}"
