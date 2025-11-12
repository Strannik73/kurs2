from cProfile import label
from datetime import datetime
from turtle import onclick
import pandas as pd
import requests_cache
import requests
from retry_requests import retry
import pandas as pd
import tkinter as tk
import requests

key = "e1cbe0e09b684aac88d8864e1aa3be94"
url = "https://api.weatherbit.io/v2.0/current"

# def err(lat, lon):
#     try:
#         lat = float(lat.replace(',', '.').strip())
#         lon = float(lon.replace(',', '.').strip())
#     except ValueError:
#         return None, "Координаты должны быть числами"
#     if lat<-90 or lat>90:
#         return None, "Широта должна быть в диапазоне -90..90"
#     if lon<-180 or lon>180:
#         return None, "Долгота должна быть в диапазоне -180..180"
#     return lat, lon, None

coord = {
#==========GOMEL=============
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
#==========MINSK=============
}

def data_url(lat, lon):
    parametrs = {
        "lat": lat,
        "lon": lon,
        "key": key,
        "lang": "be",
        "units": "M"
    }
    response = requests.get(url, params=parametrs)
    print(response.status_code)
    data = response.json()
    dt = data["data"][0]
    city = dt.get("city_name", "-")
    temp = dt.get("temp", "-")
    descr = dt.get("weather", {}).get("description", "—")
    return f"{city}: {round(temp)}°C, {descr}"

def err(region_id):
    lat, lon = coord[region_id]
    try: 
        result = data_url(lat, lon)
        label.config(text=result)
    except Exception as e:
        label.config(text=f"Ошибка: {e}")
        
root = tk.Tk()
root.title("Погода в районах Гомельской области")

label_city = tk.Label(root, text="Выберите район", font=("Arial", 16))
label_city.pack(pady=10)

label_temp = tk.Label(root, text="—", font=("Arial", 14))
label_temp.pack(pady=10)

# создаём кнопки для всех районов
frame = tk.Frame(root)
frame.pack(pady=10)

for region_name in coord.keys():
    btn = tk.Button(frame, text=region_name, width=20,
                    command=lambda r=region_name: onclick(r))
    btn.pack(pady=2)

root.mainloop()