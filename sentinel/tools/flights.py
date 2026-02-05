import requests
from sentinel.core.config import ConfigManager


def search_flights(departure_id, arrival_id, date, travel_type=2):
    cfg = ConfigManager()
    key = cfg.get_key("serp_api")

    if not key:
        return "Error: SerpAPI key missing."

    params = {
        "api_key": key,
        "engine": "google_flights",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": date,
        "type": travel_type,
        "hl": "en",
        "currency": "USD"
    }

    try:
        response = requests.get(
            "https://serpapi.com/search",
            params=params,
            timeout=15
        )

        if response.status_code != 200:
            return f"SerpAPI HTTP Error: {response.status_code}"

        data = response.json()

        if "error" in data:
            return f"API Error: {data['error']}"

        flights = data.get("best_flights") or data.get("other_flights")
        if not flights:
            return "No flights found."

        summary = [f"Found {len(flights)} flights (Top 5 shown):"]

        for i, f in enumerate(flights[:5], 1):
            price = f.get("price", "N/A")
            duration = f.get("total_duration", "N/A")

            leg = f["flights"][0]
            airline = leg.get("airline", "Unknown")
            dep_time = leg["departure_airport"]["time"]
            arr_time = leg["arrival_airport"]["time"]

            summary.append(
                f"{i}. {airline} | ${price} | {duration} min\n"
                f"   Departs: {dep_time} ({departure_id}) -> "
                f"Arrives: {arr_time} ({arrival_id})"
            )

        return "\n".join(summary)

    except Exception as e:
        return f"Flight search failed: {e}"
