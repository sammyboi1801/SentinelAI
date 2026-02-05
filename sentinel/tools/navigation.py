import googlemaps
import re
from sentinel.core.config import ConfigManager


def get_gmaps():
    cfg = ConfigManager()
    key = cfg.get_key("google_maps")
    if not key:
        return None
    return googlemaps.Client(key=key)


def geocode(address):
    gmaps = get_gmaps()
    if not gmaps:
        return "Error: Google Maps API key missing in config"

    try:
        result = gmaps.geocode(address)
        if not result:
            return "No results."

        loc = result[0]["geometry"]["location"]
        formatted = result[0]["formatted_address"]
        return f"Address: {formatted}\nCoordinates: {loc['lat']}, {loc['lng']}"
    except Exception as e:
        return f"Geocode error: {e}"


def reverse_geocode(lat, lon):
    gmaps = get_gmaps()
    if not gmaps:
        return "Error: Google Maps API key missing in config"

    try:
        lat = float(lat)
        lon = float(lon)
        result = gmaps.reverse_geocode((lat, lon))
        return f"Address: {result[0]['formatted_address']}" if result else "No address."
    except Exception as e:
        return f"Reverse Geocode error: {e}"


def calc_distance(origin, destination, mode="driving"):
    gmaps = get_gmaps()
    if not gmaps:
        return "Error: Google Maps API key missing in config"

    try:
        matrix = gmaps.distance_matrix(origin, destination, mode=mode)
        row = matrix["rows"][0]["elements"][0]
        if row["status"] != "OK":
            return f"Error: {row['status']}"

        return (
            f"Trip: {origin} -> {destination} ({mode})\n"
            f"Distance: {row['distance']['text']}\n"
            f"Duration: {row['duration']['text']}"
        )
    except Exception as e:
        return f"Distance error: {e}"


def get_directions(origin, destination, mode="driving"):
    gmaps = get_gmaps()
    if not gmaps:
        return "Error: Google Maps API key missing in config"

    try:
        directions = gmaps.directions(origin, destination, mode=mode)
        if not directions:
            return "No directions."

        steps = directions[0]["legs"][0]["steps"]
        summary = [f"Directions ({mode}):"]

        for i, step in enumerate(steps, 1):
            instr = re.sub("<[^<]+?>", "", step["html_instructions"])
            summary.append(f"{i}. {instr} ({step['distance']['text']})")

        return "\n".join(summary)
    except Exception as e:
        return f"Directions error: {e}"


def find_nearby(lat, lon, type="restaurant", radius=1000):
    gmaps = get_gmaps()
    if not gmaps:
        return "Error: Google Maps API key missing in config"

    try:
        location = (float(lat), float(lon))
        places = gmaps.places_nearby(
            location=location,
            radius=radius,
            type=type
        )

        results = []
        for p in places.get("results", [])[:10]:
            name = p.get("name")
            addr = p.get("vicinity", "No address")
            rating = p.get("rating", "N/A")
            results.append(f"- {name} ({rating}*) - {addr}")

        return "\n".join(results) if results else "No places found."
    except Exception as e:
        return f"Places error: {e}"
