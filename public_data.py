import json
import time
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

NWS_BASE_URL = "https://api.weather.gov"
USER_AGENT = "cascadia-agent/0.1 (learning project; https://github.com/aneeshdeshpande98/cascadia-agent)"
REQUEST_TIMEOUT_SECONDS = 10
CACHE_TTL_SECONDS = 300

_cache: dict[str, tuple[float, Any]] = {}

KNOWN_LOCATIONS = {
    "paradise": {"name": "Paradise, Mt. Rainier", "lat": 46.7865, "lon": -121.7355},
    "camp muir": {"name": "Camp Muir, Mt. Rainier", "lat": 46.8350, "lon": -121.7329},
    "mt. rainier": {"name": "Paradise, Mt. Rainier", "lat": 46.7865, "lon": -121.7355},
    "mount rainier": {"name": "Paradise, Mt. Rainier", "lat": 46.7865, "lon": -121.7355},
    "timberline lodge": {"name": "Timberline Lodge, Mt. Hood", "lat": 45.3311, "lon": -121.7113},
    "mt. hood": {"name": "Timberline Lodge, Mt. Hood", "lat": 45.3311, "lon": -121.7113},
    "mount hood": {"name": "Timberline Lodge, Mt. Hood", "lat": 45.3311, "lon": -121.7113},
    "baker": {"name": "Mt. Baker Ski Area", "lat": 48.8574, "lon": -121.6662},
    "mt. baker": {"name": "Mt. Baker Ski Area", "lat": 48.8574, "lon": -121.6662},
    "mount baker": {"name": "Mt. Baker Ski Area", "lat": 48.8574, "lon": -121.6662},
    "snoqualmie pass": {"name": "Snoqualmie Pass", "lat": 47.4244, "lon": -121.4132},
    "stevens pass": {"name": "Stevens Pass", "lat": 47.7461, "lon": -121.0890},
    "crystal mountain": {"name": "Crystal Mountain", "lat": 46.9354, "lon": -121.4748},
    "artist point": {"name": "Artist Point", "lat": 48.8465, "lon": -121.6929},
}


def get_nws_forecast(location: str) -> dict[str, Any]:
    """Fetch live public National Weather Service forecast and alerts for a known location."""
    resolved = _resolve_location(location)
    if not resolved:
        return {
            "location": location,
            "found": False,
            "error": (
                "Location is not in the known public-data lookup list. "
                f"Known locations: {', '.join(sorted(KNOWN_LOCATIONS.keys()))}."
            ),
            "source": "National Weather Service API",
        }

    lat = resolved["lat"]
    lon = resolved["lon"]

    try:
        point_data = _get_json(f"{NWS_BASE_URL}/points/{lat:.4f},{lon:.4f}")
        properties = point_data["properties"]
        forecast_url = properties["forecast"]
        hourly_url = properties["forecastHourly"]

        forecast_data = _get_json(forecast_url)
        hourly_data = _get_json(hourly_url)
        alerts_data = _get_json(
            f"{NWS_BASE_URL}/alerts/active?{urlencode({'point': f'{lat:.4f},{lon:.4f}'})}"
        )
    except (HTTPError, URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
        return {
            "location": location,
            "resolved_location": resolved["name"],
            "found": True,
            "error": f"Could not fetch live NWS data: {exc}",
            "source": "National Weather Service API",
        }

    periods = forecast_data.get("properties", {}).get("periods", [])[:5]
    hourly_periods = hourly_data.get("properties", {}).get("periods", [])[:6]
    alerts = alerts_data.get("features", [])

    return {
        "location": location,
        "resolved_location": resolved["name"],
        "coordinates": {"lat": lat, "lon": lon},
        "forecast_office": properties.get("cwa"),
        "grid": {
            "office": properties.get("gridId"),
            "x": properties.get("gridX"),
            "y": properties.get("gridY"),
        },
        "daily_periods": [_format_forecast_period(period) for period in periods],
        "next_6_hours": [_format_hourly_period(period) for period in hourly_periods],
        "active_alert_count": len(alerts),
        "active_alerts": [_format_alert(alert) for alert in alerts[:5]],
        "source": "National Weather Service API",
        "source_urls": {
            "point": f"{NWS_BASE_URL}/points/{lat:.4f},{lon:.4f}",
            "forecast": forecast_url,
            "hourly": hourly_url,
            "alerts": f"{NWS_BASE_URL}/alerts/active?point={lat:.4f},{lon:.4f}",
        },
    }


def _resolve_location(location: str) -> Optional[dict[str, Any]]:
    key = location.lower().strip()
    if key in KNOWN_LOCATIONS:
        return KNOWN_LOCATIONS[key]

    for known_key, value in KNOWN_LOCATIONS.items():
        if key in known_key or known_key in key:
            return value

    return None


def _get_json(url: str) -> Any:
    cached = _cache.get(url)
    if cached:
        cached_at, payload = cached
        if time.time() - cached_at < CACHE_TTL_SECONDS:
            return payload

    request = Request(
        url,
        headers={
            "Accept": "application/geo+json, application/json",
            "User-Agent": USER_AGENT,
        },
    )
    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        payload = json.loads(response.read().decode("utf-8"))
        _cache[url] = (time.time(), payload)
        return payload


def _format_forecast_period(period: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": period.get("name"),
        "start_time": period.get("startTime"),
        "end_time": period.get("endTime"),
        "temperature": period.get("temperature"),
        "temperature_unit": period.get("temperatureUnit"),
        "wind_speed": period.get("windSpeed"),
        "wind_direction": period.get("windDirection"),
        "short_forecast": period.get("shortForecast"),
        "detailed_forecast": period.get("detailedForecast"),
    }


def _format_hourly_period(period: dict[str, Any]) -> dict[str, Any]:
    return {
        "start_time": period.get("startTime"),
        "temperature": period.get("temperature"),
        "temperature_unit": period.get("temperatureUnit"),
        "wind_speed": period.get("windSpeed"),
        "wind_direction": period.get("windDirection"),
        "short_forecast": period.get("shortForecast"),
        "precipitation_probability": (
            period.get("probabilityOfPrecipitation", {}).get("value")
            if isinstance(period.get("probabilityOfPrecipitation"), dict)
            else None
        ),
    }


def _format_alert(alert: dict[str, Any]) -> dict[str, Any]:
    properties = alert.get("properties", {})
    return {
        "event": properties.get("event"),
        "headline": properties.get("headline"),
        "severity": properties.get("severity"),
        "certainty": properties.get("certainty"),
        "urgency": properties.get("urgency"),
        "effective": properties.get("effective"),
        "expires": properties.get("expires"),
        "instruction": properties.get("instruction"),
    }
