from fastapi import FastAPI, Request
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
async def gomel_page(request: Request):
    return templates.TemplateResponse("gomel.html", {"request": request})

@app.get("/weather/{region_id}")
async def weather(region_id: str):
    try:
        result = data_url(region_id)
        return JSONResponse(result)  # гарантированно JSON
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
