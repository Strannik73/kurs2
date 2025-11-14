# uvicorn main:app --reload --host 0.0.0.0 --port 8000
# uvicorn main:app --reload --host 127.0.0.1 --port 8000
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from api import data_url

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
    return templates.TemplateResponse("main.html", {"request": request})


@app.get("/gomel", response_class=HTMLResponse)
async def gomel_page_get(request: Request):
    # Возвращает страницу с пустым начальным состоянием
    return templates.TemplateResponse("gomel.html", {"request": request, "temp": None, "descr": None, "icon_url": ""})


@app.post("/gomel/select", response_class=HTMLResponse)
async def gomel_page_select(request: Request, region: str = Form(...)):
    """
    Обработчик формы. Ожидает поле form name="region".
    Возвращает ту же страницу gomel.html, передавая temp, descr, icon_url для отображения.
    """
    try:
        data = data_url(region)
        temp = data.get("temp")
        descr = data.get("descr")
        icon = data.get("icon")
        icon_url = f"https://www.weatherbit.io/static/img/icons/{icon}.png" if icon else ""
    except ValueError as e:
        temp, descr, icon_url = None, str(e), ""
    except RuntimeError as e:
        temp, descr, icon_url = None, str(e), ""
    except Exception:
        temp, descr, icon_url = None, "Ошибка сервера", ""

    return templates.TemplateResponse(
        "gomel.html",
        {
            "request": request,
            "selected_region": region,
            "temp": temp,
            "descr": descr,
            "icon_url": icon_url
        }
    )


@app.get("/minsk", response_class=HTMLResponse)
async def minsk_page(request: Request):
    return templates.TemplateResponse("minsk.html", {"request": request})


@app.get("/mogilev", response_class=HTMLResponse)
async def mogilev_page(request: Request):
    return templates.TemplateResponse("mogilev.html", {"request": request})


@app.get("/vitebsk", response_class=HTMLResponse)
async def vitebsk_page(request: Request):
    return templates.TemplateResponse("vitebsk.html", {"request": request})


@app.get("/grodno", response_class=HTMLResponse)
async def grodno_page(request: Request):
    return templates.TemplateResponse("grodno.html", {"request": request})


@app.get("/brest", response_class=HTMLResponse)
async def brest_page(request: Request):
    return templates.TemplateResponse("brest.html", {"request": request})


@app.get("/weather/{region_id}")
async def weather(region_id: str):
    try:
        result = data_url(region_id)
        return JSONResponse(content=result, status_code=200)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
