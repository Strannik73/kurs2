from datetime import datetime
import pandas as pd
import requests_cache
import requests
from retry_requests import retry
import pandas as pd

key = "e1cbe0e09b684aac88d8864e1aa3be94"
url = "https://api.weatherbit.io/v2.0/current"

response = requests.get(url)
print(response.status_code)
data = response.json()


data = {'@TG_nick': [], 'Motion': [], 'API': [], 'Date': [], 'Time': [], 'API_answer': []}
df = pd.DataFrame(data)

def logger(func):
    async def wrapper(*args):
        func_return = await func(*args)
        message = args[0]
        if len(func_return) == 3:
            motion = func_return[0]
            api = func_return[1]
            api_answer = func_return[2]
        else:
            motion = func_return[0]
            api = 'None'
            api_answer = 'None'
        df.loc[len(df.index)] = [message.from_user.username, motion, api, datetime.now().date(), datetime.now().time(), api_answer]
        df.to_csv('log.csv', index=True, index_label='Unic_ID')
    return wrapper


@logger
async def with_photo(message: types.Message):
    await message.answer(url)
    code_resp = requests.get(url)
    motion = 'kartinka'
    return [motion, url, code_resp]