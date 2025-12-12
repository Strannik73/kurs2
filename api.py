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
    #===gomel
    "br": (51.78022008012895, 30.271741574508955),
    "buda": (52.714267028968756, 30.802356998411106),
    "vetka": (52.56426315412645, 31.241810131761177),
    "gom": (52.43384344239014, 31.19237165673237),
    "dobrush": (52.39937045231686, 31.429748865506337),
    "elsk": (51.805289104681684, 29.24291412843042),
    "zhit": (52.2226675803839, 28.05641921594576),
    "zhlobin": (52.88546212912893, 30.181242910734614),
    "kalin": (52.12351813506252, 29.400601160914462),
    "korm": (53.14113256286872, 30.878739381108446),
    "lel": (51.788744186449215, 28.45214426479251),
    "loev": (51.93635369926692, 30.758322559436778),
    "moz": (52.034432431924124, 29.31726451058395),
    "narovl": (51.806848937322435, 29.542551210003385),
    "oktyabr": (52.656118093749825, 29.037598245677092),
    "petr": (52.132296485835155, 28.594793361547133),
    "rech": (52.38431715743771, 30.53692010682822),
    "rogach": (53.07638797873189, 30.112262836036514),
    "svetl": (52.644886695068585, 29.96854545882067),
    "hoyniki": (51.892096567199964, 30.204306456618816),
    "chechersk": (52.914538846371926, 30.98889736072511),
    #===brest
    "baran": (53.13793334196031, 26.0774020853999),
    "berezov": (52.535662787846945, 24.978395430202884),
    "brestsk": (52.10751670386272, 23.855859137092388),
    "gantsevich": (52.75698027714213, 26.435371922420472),
    "drogich": (52.18292848324583, 25.172802224963185),
    "zhabink": (52.195149263976155, 23.927270267243987),
    "ivan": (52.13787057235844, 25.62465789930878),
    "ivatsevich": (52.70068801483246, 25.10830049667418),
    "kamenetsk": (52.40227917812577, 23.816268873240894),
    "kobrinsk": (52.21343719108604, 24.357664753111543),
    "luninetsk": (52.26916521290703, 26.937524061326528),
    "liahovich": (53.03559742135427, 26.45412564183882),
    "maloritsk": (51.787468641949616, 24.00210883800575),
    "pinsk": (52.110670995647986, 26.239438870196224),
    "pruzhansk": (52.55871552727594, 24.452047149656757),
    "stolinsk": (51.89677584796369, 26.874823619433),
    #===grodno
    "berestovitski": (53.18821995517449, 24.011441647973093),
    "volkovisski": (53.15559712012693, 24.45113803470285),
    "voronovski": (54.15073486113309, 25.307998855559166),
    "grodnenski": (53.66092137447922, 23.79059761081633),
    "dyatlovski": (53.454229614641804, 25.313746061526928),
    "zelvenski": (53.14775310845625, 24.820188602547308),
    "ivevski": (53.92827888505572, 25.788026100187157),
    "korelichski": (53.57000555910009, 26.14078162728567),
    "lidski": (53.90771608935626, 25.304351145549138),
    "mostovski": (53.40720151004455, 24.577631725307498),
    "novogrudski": (53.61250520699776, 25.890160305335716),
    "ostrovetski": (54.61316589763457, 26.042513652744645),
    "oshmyanski": (54.42167890544536, 26.06537743614721),
    "svislochski": (53.03433459515149, 24.101107771537485),
    "slonimski": (53.09479971268434, 25.320480901738343),
    "smorgonski": (54.48221546448632, 26.420351339572775),
    "schuchinski": (53.605809994977164, 24.72353195513805),
    #===minsk
    "berezenski": (53.83456789862581, 29.07131351663585),
    "borisovsk": (54.218291918307834, 28.59117406080058),
    "vileiski": (54.490487663949935, 27.033170509461296),
    "volozhinski": (54.08630708919092, 26.667349975020297),
    "dzherzhinsk": (53.6820201679875, 27.274873362574095),
    "kletsk": (53.06038616790798, 26.706545051633178),
    "kopilsk": (53.1518120081157, 27.158326903594464),
    "krupsk": (54.303080518352395, 29.06728897038189),
    "logoiski": (54.20359787829503, 27.845060012018084),
    "lubansk": (52.79376513944323, 28.02979841770102),
    "minski": (53.899746573678016, 27.571456513542902),
    "molodechnensk": (54.31084173292104, 26.843204274945084),
    "miadelsk": (54.87718163858148, 26.941513327319125),
    "nesvizh": (53.22241076944275, 26.672198351737393),
    "puhovichsk": (53.52973394578215, 28.249683632996987),
    "slutsk": (53.02474246218501, 27.546105394285156),
    "smolevichsk": (54.02839332603768, 28.087762847585555),
    "soligorsk": (52.78627132124344, 27.524757552640324),
    "starodorozhsk": (53.03424861876759, 28.268106954011557),
    "stolbtsovsk": (53.48001493727228, 26.71602445488833),
    "uzdensk": (53.46437708976704, 27.200965064375843),
    "chervensk": (53.713872555922755, 28.412935713871),
    #===mogilev
    "belinichski": (),
    "bobruisk": (),
    "bihovsk": (),
    "klichevski": (),
    "goretski": (),
    "dribinski": (),
    "kirovski": (),
    "klimovichsk": (),
    "kostukovichski": (),
    "krasnopolsk": (),
    "krichevsk": (),
    "kruglyansk": (),
    "mstislavsk": (),
    "mogilevsk": (),
    "osipovichski": (),
    "slavgorodski": (),
    "hotinski": (),
    "chausski": (),
    "cherikovsk": (),
    "shklovski": (),
    "glusski": (),
    #===vitebsk
    "beshenkovichski": (),
    "braslavski": (),
    "verhnedvinski": (),
    "vitebski": (),
    "glubokski": (),
    "gorodokski": (),
    "dokshitski": (),
    "dubrovenski": (),
    "lepelski": (),
    "lioznenski": (),
    "miorski": (),
    "orshanski": (),
    "polotski": (),
    "postavski": (),
    "rossonski": (),
    "sennenski": (),
    "tolochinski": (),
    "ushachski": (),
    "chashnikski": (),
    "sharkovschinski": (),
    "shumilinski": ()

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
        payload = resp.json()
    except requests.exceptions.RequestException as exc:
        # Сетевая ошибка или таймаут
        logger.error("Сетевая ошибка: %s", exc)
        raise RuntimeError(f"Ошибка сети: {exc}")
    except ValueError as exc:
        logger.error("Невалидный JSON: %s", exc)
        raise RuntimeError(f"Невалидный JSON: {exc}")

    if not isinstance(payload, dict) or "data" not in payload or not payload["data"]:
        raise RuntimeError("Неверный ответ от API: отсутствует поле data")

    item = payload["data"][0]
    temp_raw = item.get("temp")
    try:
        temp = round(float(temp_raw)) if temp_raw is not None else 0
    except (TypeError, ValueError):
        temp = 0

    weather = item.get("weather") or {}
    descr = weather.get("description") or "-"
    icon = weather.get("icon") or ""
    city = item.get("city_name") or "Неизвестно"

    return {"city": city, "temp": temp, "descr": descr, "icon": icon}
