import requests


def get_current_weather(location=""):
    """
    Gets current weather for a location (or auto-detects if empty).
    Uses wttr.in (No API key required).
    """
    try:
        url = f"https://wttr.in/{location}?format=4"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            return f"Weather: {response.text.strip()}"
        else:
            return "Error fetching weather."
    except Exception as e:
        return f"Weather connection error: {e}"


def get_weather_forecast(location=""):
    """
    Gets a 3-day forecast description from wttr.in
    """
    try:
        url = f"https://wttr.in/{location}?format=j2"
        response = requests.get(url, timeout=5)

        if response.status_code != 200:
            return "Error fetching forecast."

        data = response.json()

        # ---- Current conditions ----
        current = data["current_condition"][0]
        desc = current["weatherDesc"][0]["value"]
        temp = current["temp_C"]
        feels = current["FeelsLikeC"]

        # ---- 3-day forecast ----
        forecast_lines = []
        for day in data["weather"][:3]:
            date = day["date"]
            min_t = day["mintempC"]
            max_t = day["maxtempC"]
            forecast_lines.append(
                f"{date}: {min_t}°C → {max_t}°C"
            )

        forecast_text = "\n".join(forecast_lines)

        return (
            f"Current: {desc}, {temp}°C (Feels like {feels}°C)\n\n"
            f"3-Day Forecast:\n{forecast_text}"
        )

    except Exception:
        return get_current_weather(location)
