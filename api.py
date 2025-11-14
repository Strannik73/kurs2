# api.py
# Модуль для получения текущей погоды по region_id или по координатам (lat,lon)
# Запуск: используется импортом из main.py

import os
import logging
from typing import Dict, Tuple, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("api")

# Координаты регионов (ключи region_id -> (lat, lon))
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
    "chechersk": (52.92, 30.92),
}

# URL API и ключ (ключ можно переопределить через переменную окружения WEATHERBIT_KEY)
DEFAULT_KEY = "e1cbe0e09b684aac88d8864e1aa3be94"
key = os.getenv("WEATHERBIT_KEY", DEFAULT_KEY)
url = "https://api.weatherbit.io/v2.0/current"

# Сессия с retry для надёжности (повторные попытки при кратковременных ошибках)
_session = requests.Session()
_retries = Retry(total=3, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504), allowed_methods=("GET",))
_adapter = HTTPAdapter(max_retries=_retries)
_session.mount("https://", _adapter)
_session.mount("http://", _adapter)


def _parse_coords_from_str(s: str) -> Optional[Tuple[float, float]]:
    """
    Попытаться распарсить строку вида "lat,lon" или "lat lon" или "lat:lon".
    Возвращает (lat, lon) или None при неуспехе.
    """
    if not isinstance(s, str):
        return None
    for sep in (",", " ", ":", ";"):
        if sep in s:
            parts = [p.strip() for p in s.split(sep) if p.strip()]
            if len(parts) >= 2:
                try:
                    lat = float(parts[0])
                    lon = float(parts[1])
                    return (lat, lon)
                except ValueError:
                    return None
    return None


def data_url(region_id: str) -> dict:
    """
    Возвращает словарь: {"temp": int, "descr": str, "icon": str}
    Поддерживает:
      - существующие ключи из coord (например 'gom', 'br' и т.д.)
      - строку с координатами "lat,lon" (например "52.43,30.98")
    Бросает ValueError если вход некорректен
    Бросает RuntimeError при ошибках сети или некорректном ответе API
    """

    if not region_id or not isinstance(region_id, str):
        raise ValueError("Не указан region_id")

    region_id = region_id.strip()

    # Сначала проверяем — может быть ключ из словаря coord
    if region_id in coord:
        lat, lon = coord[region_id]
    else:
        # Попробуем распарсить координаты из строки
        parsed = _parse_coords_from_str(region_id)
        if parsed is None:
            raise ValueError("Неизвестный регион или некорректные координаты")
        lat, lon = parsed

    params = {
        "lat": lat,
        "lon": lon,
        "key": key,
        "lang": "ru",
        "units": "M",
    }

    try:
        resp = _session.get(url, params=params, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        # Сетевая ошибка или таймаут
        logger.error("Сетевая ошибка при обращении к weatherbit для %s (lat=%s lon=%s): %s", region_id, lat, lon, exc)
        raise RuntimeError(f"Ошибка сети: {exc}")

    try:
        payload = resp.json()
    except ValueError as exc:
        # Не удалось распарсить JSON
        logger.error("Невалидный JSON от weatherbit для %s: %s", region_id, exc)
        raise RuntimeError(f"Невалидный JSON в ответе API: {exc}")

    # Проверяем корректность структуры ответа
    if not isinstance(payload, dict) or "data" not in payload or not payload["data"]:
        logger.error("Неверный ответ от API для %s: %r", region_id, payload)
        raise RuntimeError("Неверный ответ от API: отсутствует поле data")

    item = payload["data"][0]
    if not isinstance(item, dict):
        logger.error("Неверный формат данных в ответе API для %s: %r", region_id, item)
        raise RuntimeError("Неверный формат данных в ответе API")

    # Обрабатываем температуру безопасно
    temp_raw = item.get("temp")
    try:
        temp = round(float(temp_raw)) if temp_raw is not None else 0
    except (TypeError, ValueError):
        logger.warning("Температура некорректна для %s: %r", region_id, temp_raw)
        temp = 0

    weather = item.get("weather") or {}
    descr = weather.get("description") or "-"
    icon = weather.get("icon") or ""

    # Возвращаем только минимально необходимое
    return {"temp": temp, "descr": descr, "icon": icon}
