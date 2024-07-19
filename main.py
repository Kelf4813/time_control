import asyncio
from datetime import datetime
import os
import time

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app import config as cfg
from app import database as db
from app import draw_statistics as ds
from app import modules as md

hours = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]


class UserState(StatesGroup):
    start = State()
    add_rate = State()
    add_description = State()
    add_date = State()


storage = MemoryStorage()
bot = Bot(token=cfg.token)
dp = Dispatcher(bot, storage=storage)

accept_buttons = [KeyboardButton(text="Подтвердить✅"),
                  KeyboardButton(text="Отмена❌")]
main_buttons = [KeyboardButton(text="Статистика📊"),
                KeyboardButton(text="Добавить☑️")]
statistic_buttons = [KeyboardButton(text="За сегодня"),
                     KeyboardButton(text="За 30 Дней")]

accept_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
    *accept_buttons)
statistic_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
    *statistic_buttons)
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
    *main_buttons)


def delete_img(file_path):
    if os.path.isfile(file_path):
        os.remove(file_path)


@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if db.check_user(user_id):
        db.add_user(user_id)
    msg = 'FAQ'
    await message.answer(msg, reply_markup=main_keyboard)
    await state.set_state(UserState.start.state)


@dp.message_handler(state=UserState.add_rate)
async def handle_add_case(message: types.Message, state: FSMContext):
    if message.text.isdigit() and 1 <= int(message.text) <= 10:
        await state.update_data(rate=message.text)
        await state.set_state(UserState.add_description.state)
        await message.answer("Напиши что делал этот час")
    else:
        await message.reply("Напиши число от 1 до 10")


@dp.message_handler(state=UserState.add_description)
async def handle_add_rate(message: types.Message, state: FSMContext):
    data = await state.get_data()
    mes = f"Оценка: {data['rate']}\nТекст: {message.text}"
    await state.update_data(description=message.text)
    await message.answer(mes, reply_markup=accept_keyboard)
    await state.set_state(UserState.start.state)


@dp.message_handler(state=UserState.start, text='Подтвердить✅')
async def handle_add_rate(message: types.Message, state: FSMContext):
    await state.update_data(user_id=message.from_user.id)
    data = await state.get_data()
    if 'time' not in data or 'date' not in data:
        await state.update_data(time=int(time.time()))
        await state.update_data(date=md.time_to_date(int(time.time())))
        data = await state.get_data()
    db.add_data(data)
    if time.localtime(data['time']).tm_hour >= 22:
        user_id = message.from_user.id
        with open('img/result.png', 'rb') as photo:
            current_date = datetime.now()
            today_date = current_date.strftime('%d:%m')
            ds.draw_day(today_date, user_id)
            mes = md.statistics_mes(today_date)
            await bot.send_photo(user_id, photo=photo, caption=mes,
                                 reply_markup=main_keyboard)
    else:
        await bot.send_message(message.from_user.id, "Готово",
                               reply_markup=main_keyboard)


@dp.message_handler(state=UserState.start, text='Отмена❌')
async def handle_add_rate(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await message.delete()
    await bot.send_message(message.from_user.id, "Отмена❌",
                           reply_markup=main_keyboard)

    if 'date' in data:
        await state.set_state(UserState.start.state)
        await bot.send_message(message.from_user.id, "Отмена❌",
                               reply_markup=main_keyboard)
    else:
        await state.finish()
        await state.set_state(UserState.add_rate.state)
        await message.answer("Напиши число от 1 до 10")


@dp.message_handler(state=UserState.start, text="Статистика📊")
async def handle_add_rate(message: types.Message):
    await message.delete()
    await bot.send_message(message.from_user.id, "Статистика📊",
                           reply_markup=statistic_keyboard)


@dp.message_handler(state=UserState.start, text="За сегодня")
async def handle_add_rate(message: types.Message):
    user_id = message.from_user.id
    current_date = datetime.now()
    today_date = current_date.strftime('%d:%m')
    mes = ds.draw_day(today_date, user_id)
    img_path = f'img/{user_id}_day.png'
    if os.path.isfile(img_path):
        with open(img_path, 'rb') as photo:
            await bot.send_photo(user_id, photo=photo, caption=mes,
                                 reply_markup=main_keyboard)
        delete_img(img_path)
    else:
        await bot.send_message(message.from_user.id,
                               "Статистики пока нет",
                               reply_markup=main_keyboard)


@dp.message_handler(state=UserState.start, text="За 30 Дней")
async def handle_add_rate(message: types.Message):
    user_id = message.from_user.id
    ds.draw_30d(user_id)
    img_path = f'img/{user_id}_month.png'
    if os.path.isfile(img_path):
        with open(img_path, 'rb') as photo:
            await bot.send_photo(user_id, photo=photo,
                                 reply_markup=main_keyboard)
        delete_img(img_path)
    else:
        await bot.send_message(message.from_user.id,
                               "Статистики пока нет",
                               reply_markup=main_keyboard)


@dp.message_handler(state=UserState.start, text="Добавить☑️")
async def handle_add_rate(message: types.Message, state: FSMContext):
    await message.answer("Напиши дату в формате Час:День:Месяц")
    await state.set_state(UserState.add_date.state)


@dp.message_handler(lambda message: 'статистика ' in message.text.lower(),
                    state=UserState.start)
async def handle_add_rate(message: types.Message):
    user_id = message.from_user.id
    today_date = message.text.lower().split()[1]
    mes = ds.draw_day(today_date, user_id)
    img_path = f'img/{user_id}_day.png'
    if os.path.isfile(img_path):
        with open(img_path, 'rb') as photo:
            if mes:
                await bot.send_photo(user_id, photo=photo, caption=mes,
                                     reply_markup=main_keyboard)
            else:
                await bot.send_message(user_id, 'Такой даты нет',
                                       reply_markup=main_keyboard)
    else:
        await bot.send_message(message.from_user.id,
                               "Статистики пока нет",
                               reply_markup=main_keyboard)


@dp.message_handler(state=UserState.add_date)
async def handle_add_rate(message: types.Message, state: FSMContext):
    data_time = md.str_to_time(message.text)
    user_id = message.from_user.id
    if not data_time:
        await message.reply("Напиши дату в формате Час:День:Месяц")
    else:
        await state.update_data(time=md.str_to_time(message.text))
        data = await state.get_data()
        date_send = time.localtime(data['time'])
        if date_send.tm_hour in hours:
            if 0 < date_send.tm_mday < 32 and 0 < date_send.tm_mon < 13:
                await state.set_state(UserState.add_rate.state)
                await state.update_data(date=md.time_to_date(data['time']))
                data = await state.get_data()

                if db.check_date(user_id, md.time_to_date(data['time'])):
                    await message.answer("Эта дата уже записана")
                    await state.set_state(UserState.start.state)
                elif data['time'] > time.time():
                    await message.answer("Нельзя записать будущую дату")
                    await state.set_state(UserState.start.state)
                else:
                    await message.answer('Оцени час от 1 до 10')
            else:
                await message.reply("Неверная дата")
        else:
            await message.reply("Можно заполнить только 7-22")


async def main():
    while True:
        current_time = datetime.now()
        if current_time.minute == 0 and current_time.hour in hours:
            new_state = UserState.add_rate
            users = db.all_users()
            for user_id in users:
                await bot.send_message(user_id[0], 'Оцени час от 1 до 10')
                state = FSMContext(storage=storage, chat=user_id[0],
                                   user=user_id[0])
                await state.set_state(new_state.state)
            await asyncio.sleep(60)
        await asyncio.sleep(5)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    executor.start_polling(dp, skip_updates=True)
