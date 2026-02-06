import googlemaps
import re
from sentinel.core.config import ConfigManager

_gmaps_client = None


def get_gmaps():
    """
    Returns a cached Google Maps client instance.
    """
    global _gmaps_client
    if _gmaps_client:
        return _gmaps_client

    cfg = ConfigManager()
    key = cfg.get_key("google_maps")

    if not key:
        return None

    try:
        _gmaps_client = googlemaps.Client(key=key)
        return _gmaps_client
    except ValueError as e:
        print(f"Error initializing Google Maps: {e}")
        return None


def geocode(address):
    """Converts text (Boston, MA) to coordinates (42.36, -71.05)."""
    gmaps = get_gmaps()
    if not gmaps:
        return "❌ Error: Google Maps API key missing."

    try:
        result = gmaps.geocode(address)
        if not result:
            return f"❌ Could not find location: '{address}'"

        loc = result[0]["geometry"]["location"]
        formatted = result[0]["formatted_address"]
        return f"📍 Found: {formatted}\nCoordinates: {loc['lat']}, {loc['lng']}"
    except Exception as e:
        return f"❌ Geocode error: {e}"


def reverse_geocode(lat, lon):
    """Converts coordinates to a readable address."""
    gmaps = get_gmaps()
    if not gmaps: return "❌ Error: API key missing."

    try:
        result = gmaps.reverse_geocode((float(lat), float(lon)))
        return f"📍 Address: {result[0]['formatted_address']}" if result else "❌ No address found."
    except Exception as e:
        return f"❌ Reverse Geocode error: {e}"


def calc_distance(origin, destination, mode="driving"):
    """
    Calculates distance and duration matrix.
    Modes: driving, walking, bicycling, transit
    """
    gmaps = get_gmaps()
    if not gmaps: return "❌ Error: API key missing."

    try:
        matrix = gmaps.distance_matrix(origin, destination, mode=mode)

        if matrix['status'] != 'OK':
            return f"❌ API Error: {matrix['status']}"

        row = matrix["rows"][0]["elements"][0]
        if row["status"] != "OK":
            return f"❌ No route found ({row['status']}). Are the locations correct?"

        return (
            f"🚗 Trip: {origin} ➡️ {destination} ({mode})\n"
            f"📏 Distance: {row['distance']['text']}\n"
            f"⏱️ Duration: {row['duration']['text']}"
        )
    except Exception as e:
        return f"❌ Distance error: {e}"


def get_directions(origin, destination, mode="driving"):
    """
    Returns step-by-step navigation instructions.
    """
    gmaps = get_gmaps()
    if not gmaps: return "❌ Error: API key missing."

    try:
        directions = gmaps.directions(origin, destination, mode=mode)
        if not directions:
            return "❌ No directions found."

        steps = directions[0]["legs"][0]["steps"]
        summary = [f"🗺️ **Directions to {destination} ({mode}):**"]

        for i, step in enumerate(steps, 1):
            instr = re.sub("<[^<]+?>", "", step["html_instructions"])
            dist = step['distance']['text']
            summary.append(f"{i}. {instr} ({dist})")

        return "\n".join(summary)
    except Exception as e:
        return f"❌ Directions error: {e}"


def find_nearby(lat, lon, place_type="restaurant", radius=1000):
    """
    Finds places of a specific type near coordinates.
    Renamed 'type' -> 'place_type' to avoid shadowing Python's built-in.
    """
    gmaps = get_gmaps()
    if not gmaps: return "❌ Error: API key missing."

    try:
        location = (float(lat), float(lon))
        places = gmaps.places_nearby(
            location=location,
            radius=radius,
            type=place_type
        )

        results = [f"🔍 **Nearby {place_type}s:**"]
        found = places.get("results", [])

        if not found:
            return "❌ No places found."

        for p in found[:5]:
            name = p.get("name")
            addr = p.get("vicinity", "No address")
            rating = p.get("rating", "N/A")
            open_now = p.get("opening_hours", {}).get("open_now", "Unknown")
            status = "🟢 Open" if open_now is True else "🔴 Closed" if open_now is False else "🕒 Unknown"

            results.append(f"- **{name}** ({rating}⭐) | {status}\n  {addr}")

        return "\n".join(results)
    except Exception as e:
        return f"❌ Places error: {e}"