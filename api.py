# http://127.0.0.1:8000/docs#/default/weather_weather__region_id__get
import requests
from typing import Dict, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Координаты регионов
coord: Dict[str, Tuple[float, float]] = {
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

# Оставляем key и url как в вашем оригинале
key = "e1cbe0e09b684aac88d8864e1aa3be94"
url = "https://api.weatherbit.io/v2.0/current"

# Сессия с retry для надёжности запросов
_session = requests.Session()
_retries = Retry(total=3, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504))
_adapter = HTTPAdapter(max_retries=_retries)
_session.mount("https://", _adapter)
_session.mount("http://", _adapter)


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
        resp = _session.get(url, params=params, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Ошибка сети: {exc}")

    try:
        payload = resp.json()
    except ValueError as exc:
        raise RuntimeError(f"Невалидный JSON в ответе API: {exc}")

    if not isinstance(payload, dict) or "data" not in payload or not payload["data"]:
        raise RuntimeError("Неверный ответ от API: отсутствует поле data")

    item = payload["data"][0]
    if not isinstance(item, dict):
        raise RuntimeError("Неверный формат данных в ответе API")

    temp_raw = item.get("temp")
    try:
        temp = round(float(temp_raw)) if temp_raw is not None else 0
    except (TypeError, ValueError):
        temp = 0

    weather = item.get("weather") or {}
    descr = weather.get("description") or "-"
    icon = weather.get("icon") or ""

    return {"temp": temp, "descr": descr, "icon": icon}
