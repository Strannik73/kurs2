import requests

key = "e1cbe0e09b684aac88d8864e1aa3be94"
url = "https://api.weatherbit.io/v2.0/current"

coord = {
    "br": (51.8, 30.3),
    "buda": (52.72, 30.57),
    "vetka": (52.56, 31.18),
    "gom": (52.43, 30.98),
    "dobrush": (52.41, 31.32),
    "elsk": (51.75, 29.15),
    "zhit": (52.22, 27.85),
    "zhlobin": (52.89, 30.03),
    "kalin": (52.63, 29.33),
    "korm": (53.11, 30.63),
    "lel": (51.63, 28.1),
    "loev": (51.95, 30.8),
    "moz": (52.05, 29.27),
    "narovl": (51.8, 29.5),
    "oktyabr": (52.65, 28.9),
    "petr": (52.13, 28.9),
    "rech": (52.36, 30.4),
    "rogach": (53.09, 30.05),
    "svetl": (52.63, 29.73),
    "hoyniki": (51.9, 29.5),
    "chechersk": (52.92, 30.92)
}

def data_url(region_id: str) -> dict:
    if region_id not in coord:
        raise ValueError("Неизвестный регион")

    lat, lon = coord[region_id]
    params = {
        "lat": lat,
        "lon": lon,
        "key": key,
        "lang": "ru",
        "units": "M"
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        if "data" not in data or not data["data"]:
            raise RuntimeError("Неверный ответ от API")

        dt = data["data"][0]
        return {
            "city": dt.get("city_name", "-"),
            "temp": round(dt.get("temp", 0)),
            "descr": dt.get("weather", {}).get("description", "-"),
            "icon": dt.get("weather", {}).get("icon", "")
        }

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Ошибка сети: {e}")
    except Exception as e:
        raise RuntimeError(f"Ошибка обработки данных: {e}")
