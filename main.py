from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

import requests


try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup


TOKEN = '5381068144:AAGUwiodpHeMSq_wQVNHM1utcvDqQ00FkPY'
top_vuzes = {"ВШЭ": 1, "ИТМО": 1, "МФТИ": 0.8, "МИФИ": 0.7, "МГТУ им. Баумана": 0.6, "МИСиС": 0.5, "СПбГУ": 0.6,
                 "МЭИ": 0.5, "МАИ": 0.5, "СПбПУ": 0.5}

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


button_hi = KeyboardButton('Оценить шансы')

greet_kb = ReplyKeyboardMarkup()
greet_kb.add(button_hi)


def get_chance(i):
    tds = i.find_all("td")
    op_list = tds[-1]
    value = 0
    for j in op_list.children:
        if j.text == "" or "{" not in j.text or "ОК [Б]" not in j.text: continue
        if j.text.split(", ")[0] not in top_vuzes: continue
        koeff = top_vuzes[j.text.split(", ")[0]]
        cur = int(j.text.split("{")[1].split("/")[0])
        maxs = int(j.text.split("/")[1].split("}")[0])
        value += max(koeff * ((maxs - cur) / maxs), 0)
    return value

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply("Привет! Здесь ты можешь оценить свои шансы на поступление, и посмотреть статистику", reply_markup=greet_kb)


@dp.message_handler()
async def process_start_command(message: types.Message, state: FSMContext):

    # read the config file to memory

    filecontents = requests.get("http://admlist.ru/mirea/6a1910ea92c40bfa4f22cc0166b7b0f4.html").content

    # decode the bytes format to text - this speeds up soup 10x
    # parse the xml



    soup = BeautifulSoup(filecontents, 'lxml')
    table = soup.find_all("tr")[3:]
    alls = []

    valid_1 = []
    valid_2 = []
    valid_3 = []
    for i in table[154:]:
        tds = i.find_all("td")
        op_list = tds[-1]
        if int(tds[-2].text) == 281:
            if int(tds[6].text) == 95:
                if int(tds[7].text) == 82:
                    if int(tds[8].text) < 94:
                        continue
                elif int(tds[7].text) < 82:
                    continue
            elif int(tds[6].text) < 95:
                continue
        if tds[0].b and int(tds[-2].text) >= 281 and tds[4].text == "Да":
            valid_1.append(i)
        if op_list.b and int(tds[-2].text) >= 281:
            valid_2.append(i)
        if op_list.b == None and int(tds[-2].text) >= 281:
            valid_3.append(i)
        if int(tds[-2].text) >= 281:
            alls.append(i)

    # print("Все:", len(alls))
    # print("Количество поданных согласий:", len(valid_1))
    # print("Количество унесших согласие в другое место:", len(valid_2))
    # print("Количество неопределившихся:", len(valid_3))
    ukhod_values = []
    for i in valid_2:
        tds = i.find_all("td")
        op_list = tds[-1]
        value = 0
        for j in op_list.children:
            if j.text == "" or "{" not in j.text or "ОК [Б]" not in j.text: continue
            if j.text.split(", ")[0] not in top_vuzes: continue
            koeff = top_vuzes[j.text.split(", ")[0]]
            cur = int(j.text.split("{")[1].split("/")[0])
            maxs = int(j.text.split("/")[1].split("}")[0])
            value += max(koeff * ((maxs - cur) / maxs), 0)
        if value == 0: continue
        ukhod_values.append(value)

    # print(ukhod_values)

    min_koef = min(ukhod_values)
    max_koef = max(ukhod_values)

    low_chance = []
    middle_chance = []
    high_chance = []

    for i in valid_3:
        chance = get_chance(i)
        if chance < min_koef + ((max_koef - min_koef) * 0.3):
            low_chance.append(i)
        elif chance < min_koef + ((max_koef - min_koef) * 0.6):
            middle_chance.append(i)
        else:
            high_chance.append(i)
    # print("Из них:")
    # print("\tНизкий шанс, что уйдет:", len(low_chance))
    # print("\tСредний шанс, что уйдет:", len(middle_chance))
    # print("\tВысокий шанс, что уйдет:", len(high_chance))
    await message.answer(f"Все: {len(alls)}"
                         f"\nКоличество поданных согласий: {len(valid_1)}"
                         f"\nКоличество унесших согласие в другое место: {len(valid_2)}"
                         f"\nКоличество неопределившихся: {len(valid_3)}"
                         f"\nИз них:"
                         f"\nНизкий шанс, что уйдет: {len(low_chance)}"
                         f"\nСредний шанс, что уйдет: {len(middle_chance)}"
                         f"\nВысокий шанс, что уйдет: {len(high_chance)}")
executor.start_polling(dp)