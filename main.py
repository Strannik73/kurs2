# main.py
import os
import logging
import mimetypes
from typing import Callable, List

from fastapi import FastAPI, Request, Path, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import TemplateNotFound


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("main")

app = FastAPI()

TEMPLATES_DIR = "templates"
STATIC_DIR = "static"
IMGS_DIR = "imgs"

for d in (TEMPLATES_DIR, STATIC_DIR, IMGS_DIR):
    if not os.path.isdir(d):
        logger.warning("Директория не найдена: %s", d)

try:
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    logger.info("Mounted /static -> %s", STATIC_DIR)
except Exception as exc:
    logger.exception("Не удалось смонтировать /static: %s", exc)

try:
    app.mount("/imgs", StaticFiles(directory=IMGS_DIR), name="imgs")
    logger.info("Mounted /imgs -> %s", IMGS_DIR)
except Exception as exc:
    logger.exception("Не удалось смонтировать /imgs: %s", exc)

templates = Jinja2Templates(directory=TEMPLATES_DIR)

def _static_url(path: str) -> str:
    return f"/static/{path.lstrip('/')}"
templates.env.globals['static'] = _static_url

def _img_url(path: str) -> str:
    return f"/imgs/{path.lstrip('/')}"
templates.env.globals['img'] = _img_url

CITIES: List[str] = ["gomel", "minsk", "mogilev", "vitebsk", "grodno", "brest"]

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    try:
        return templates.TemplateResponse("main.html", {"request": request})
    except TemplateNotFound:
        logger.error("templates/main.html не найден")
        return HTMLResponse("<h1>Главная страница не найдена (templates/main.html)</h1>", status_code=200)
    except Exception:
        logger.exception("Ошибка при рендеринге main.html")
        raise HTTPException(status_code=500, detail="Ошибка сервера")

@app.get("/health", response_class=PlainTextResponse)
async def health():
    return "ok"

def make_city_handler(city_name: str) -> Callable[[Request], HTMLResponse]:
    async def handler(request: Request):
        city = city_name.strip().lower()
        candidates = [f"{city}.html", f"{city}.htm"]
        for tmpl in candidates:
            try:
                return templates.TemplateResponse(tmpl, {"request": request})
            except TemplateNotFound:
                continue
            except Exception:
                logger.exception("Ошибка при рендеринге шаблона %s", tmpl)
                raise HTTPException(status_code=500, detail="Ошибка сервера при рендеринге шаблона")
        try:
            logger.info("Шаблон для %s не найден, возвращаем main.html", city)
            return templates.TemplateResponse("main.html", {"request": request})
        except TemplateNotFound:
            logger.error("templates/main.html не найден (fallback)")
            return HTMLResponse(f"<h1>Шаблон для {city} не найден</h1>", status_code=200)
        except Exception:
            logger.exception("Ошибка при рендеринге main.html (fallback)")
            raise HTTPException(status_code=500, detail="Ошибка сервера")
    return handler

# Регистрируем маршруты для городов и тестовые plain маршруты
for c in CITIES:
    app.add_api_route(f"/{c}", make_city_handler(c), methods=["GET"], response_class=HTMLResponse)

    async def _plain(_: Request, city=c):
        return PlainTextResponse(f"OK {city}")
    app.add_api_route(f"/_plain_{c}", _plain, methods=["GET"], response_class=PlainTextResponse)

# Безопасная функция для imgs (защита от path traversal)
def _safe_imgs_path(filename: str) -> str:
    if ".." in filename or filename.startswith("/") or "\\" in filename:
        raise HTTPException(status_code=400, detail="Некорректное имя файла")
    return os.path.join(IMGS_DIR, filename)

# Универсальный маршрут для отдачи файла из imgs: /images/{filename}
@app.get("/images/{filename}", name="image_file")
async def image_file(filename: str = Path(..., description="Имя файла в папке imgs")):
    path = _safe_imgs_path(filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Файл не найден")
    content_type, _ = mimetypes.guess_type(path)
    return FileResponse(path, media_type=content_type or "application/octet-stream")

# Удобный маршрут: /image/{city} отдаёт закреплённое изображение города
CITY_IMAGE_MAP = {
    "gomel": "gomel1.svg",
    "brest": "brest.png",
    "minsk": "minsk.png",
    "mogilev": "mogilev.png",
    "vitebsk": "vitebsk.png",
    "grodno": "grodno.png",
}

@app.get("/image/{city}", name="image_by_city")
async def image_by_city(city: str = Path(..., description="Код города")):
    city_key = city.strip().lower()
    filename = CITY_IMAGE_MAP.get(city_key)
    if not filename:
        raise HTTPException(status_code=404, detail="Изображение для города не задано")
    path = _safe_imgs_path(filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Файл не найден")
    content_type, _ = mimetypes.guess_type(path)
    return FileResponse(path, media_type=content_type or "application/octet-stream")

# Catch-all fallback (в конце)
@app.get("/{other}", response_class=HTMLResponse)
async def catch_all(request: Request, other: str):
    try:
        return templates.TemplateResponse("main.html", {"request": request})
    except Exception:
        logger.exception("Ошибка в catch-all при рендеринге main.html")
        return HTMLResponse("<h1>Главная страница (fallback) недоступна</h1>", status_code=200)

if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    logger.info("Запускаем app на %s:%s", host, port)
    uvicorn.run("main:app", host=host, port=port, reload=True)
