# python -m uvicorn main:app --reload
import hashlib
import os
import logging
import mimetypes
from turtle import pd
from typing import Callable, List
import uuid

from fastapi import FastAPI, Form, Request, Path, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import TemplateNotFound
from requests_cache import datetime, timedelta

from api import data_url   # импортируем нашу функцию погоды

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

# Новый эндпоинт для погоды
@app.get("/weather/{region_id}", response_class=JSONResponse)
async def weather(region_id: str):
    try:
        data = data_url(region_id)
        return JSONResponse(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

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

for c in CITIES:
    app.add_api_route(f"/{c}", make_city_handler(c), methods=["GET"], response_class=HTMLResponse)

    async def _plain(_: Request, city=c):
        return PlainTextResponse(f"OK {city}")
    app.add_api_route(f"/_plain_{c}", _plain, methods=["GET"], response_class=PlainTextResponse)

def _safe_imgs_path(filename: str) -> str:
    if ".." in filename or filename.startswith("/") or "\\" in filename:
        raise HTTPException(status_code=400, detail="Некорректное имя файла")
    return os.path.join(IMGS_DIR, filename)

@app.get("/images/{filename}", name="image_file")
async def image_file(filename: str = Path(..., description="Имя файла в папке imgs")):
    path = _safe_imgs_path(filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Файл не найден")
    content_type, _ = mimetypes.guess_type(path)
    return FileResponse(path, media_type=content_type or "application/octet-stream")

CITY_IMAGE_MAP = {
    "gomel": "gomel.svg",
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



# app = FastAPI()
# app.mount("/static", StaticFiles(directory="static"), name="static")
# templates = Jinja2Templates(directory="templates")

# USERS = "users.csv"
# log = "log.csv"
# SESSION_TTL = timedelta(days=10)
# sessions = {}
# white_urls = ["/", "/login", "/logout", "/register"]  

# logdata = {'user': [], 'role': [], 'action': [], 'Date': [], 'Time': [], }
# if os.path.exists(log):
#     lg = pd.read_csv(log)
#     # Убедимся, что структура корректна
#     expected_columns = list(logdata.keys())
#     for col in expected_columns:
#         if col not in lg.columns:
#             lg[col] = None
#     lg = lg[expected_columns]
# else:
#     lg = pd.DataFrame(logdata)

# def hash_password(password) -> str:
#     return hashlib.sha256(str(password).encode("utf-8")).hexdigest()

# df = pd.read_csv("users.csv")


# if "password" in df.columns:
#     df["password_hash"] = df["password"].apply( hash_password)
#     # df = df.drop(columns=["password"])

# df.to_csv("users.csv", index=False)


# @app.middleware("http")
# async def check_session(request: Request, call_next):
#     if request.url.path.startswith("/static") or request.url.path in white_urls:
#         return await call_next(request)
    
#     session_id = request.cookies.get("session_id")
#     session_data = sessions.get(session_id)

#     if not session_data:
#         return RedirectResponse(url="/login")
    
#     created = session_data.get("created")
#     if datetime.now() - created > SESSION_TTL:
#         sessions.pop(session_id, None)
#         return RedirectResponse(url="/login")
    
#     return await call_next(request)


# @app.get("/", response_class=HTMLResponse)
# @app.get("/login", response_class=HTMLResponse)
# def get_login_page(request: Request):
#     return templates.TemplateResponse("login.html", {"request": request})

# @app.post("/login")
# def post_login(request: Request, 
#                username: str = Form(...), 
#                password: str = Form(...)):
    
#     try:
#         users = pd.read_csv(USERS)
#         users = users.loc[:, ~users.columns.str.contains('^Unnamed')]
#     except Exception:
#         users = pd.DataFrame(columns=["users", "password", "password_hash","role"])

#     if "role" not in users.columns:
#         users["role"] = "user"

#     if username in users["users"].values:
#         password_hash = users.loc[users["users"] == username, "password_hash"].values[0]
#         role = users.loc[users["users"] == username, "role"].values[0]

#         if password_hash == hash_password(password):
#             session_id = str(uuid.uuid4())
#             sessions[session_id] = {
#                 "created": datetime.now(),
#                 "username": username,
#                 "avatar": "static/avatars/default.png",
#                 "password_hash": password_hash,
#                 "password": password,
#                 "role": role
#             }
#             response = RedirectResponse(url="/main", status_code=303)
#             response.set_cookie(key="session_id", value=session_id, httponly=True)
#             response.set_cookie(key="username", value=username, httponly=True)
#             response.set_cookie(key="role", value=role, httponly=True)

#             lg.loc[len(lg.index)] = [username, role, "вход", datetime.now().date(), datetime.now().time()]
#             lg.to_csv('log.csv', index=True, index_label='№')
#             return response
        
#         return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный пароль"})
    
#     return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный логин"})


# @app.get("/register", response_class=HTMLResponse)
# def get_register_page(request: Request):
#     return templates.TemplateResponse("register.html", {"request": request})

# @app.post("/register")
# def post_register(request: Request, 
#                   username: str = Form(...), 
#                   password: str = Form(...)):
    
#     try:
#         users = pd.read_csv(USERS)
#         users = users.loc[:, ~users.columns.str.contains('^Unnamed')]
#     except Exception:
#         users = pd.DataFrame(columns=["users", "password", "password_hash", "role"])

#     if "role" not in users.columns:
#         users["role"] = "user"

#     if username in users["users"].values:
#         return templates.TemplateResponse("register.html", {"request": request, "error": "такой пользователь существует"})
    
#     password_hash = hash_password(password)
#     role = "admin" if username == "admin" else "user"
#     new_user = pd.DataFrame([{"users": username, 
#                               "password": str(password),
#                               "password_hash": password_hash,
#                               "role": role}])
#     users = pd.concat([users, new_user], ignore_index=True)
#     users.to_csv(USERS, index=False)

#     session_id = str(uuid.uuid4())
#     sessions[session_id] = {
#         "created": datetime.now(),
#         "username": username,
#         "password": password,
#         "password_hash": password_hash,
#         "role": role
#     }
#     response = RedirectResponse(url="/main", status_code=303)
#     response.set_cookie(key="session_id", value=session_id, httponly=True)
#     response.set_cookie(key="username", value=username, httponly=True)
#     response.set_cookie(key="role", value=role, httponly=True)

#     lg.loc[len(lg.index)] = [username, role, "регистрация", datetime.now().date(), datetime.now().time()]
#     lg.to_csv('log.csv', index=True, index_label='№')
#     return response


# @app.get("/main", response_class=HTMLResponse)
# def main_page(request: Request):
#     session_id = request.cookies.get("session_id")
#     users = None
#     if session_id and session_id in sessions:
#         session_data = sessions[session_id]
#         if isinstance(session_data, dict):
#             users = {
#                 "username": session_data.get("username"),
#                 "password_hash": session_data.get("password_hash", ""),
#                 "password": session_data.get("username"),
#                 "role": session_data.get("role", "user")
#             }
#     return templates.TemplateResponse("main.html", {"request": request, "user": users})

# @app.get("/logout", response_class=HTMLResponse)
# def logout(request: Request):
#     session_id = request.cookies.get("session_id")
#     if session_id:
#         sessions.pop(session_id, None)
#     return RedirectResponse(url="/login", status_code=303)

# # @app.post("/old")
# # async def redirect_after_update():
# #     return RedirectResponse(url="/login")

# @app.exception_handler(404)
# async def not_found(request: Request, exc):
#     return templates.TemplateResponse("404.html", {"request": request}, status_code=404)


# @app.exception_handler(403)
# async def forbidden(request: Request, exc):
#     return templates.TemplateResponse("403.html", {"request": request}, status_code=403)
