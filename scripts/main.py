import os
import aiogram 
import time
import configparser

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from callback_func import *
from app_scrapper import *



BOT_COMMANDS = """
/****BOT_COMMANDS****/
/help - вызвать подсказки
/start - показать кнопки
/status - проверить алерты
/fake_aleft - вызвать фейковый алерт
"""

bot = Bot(os.getenv('API_ID') + ':' + os.getenv('API_HASH'))
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

### START KEYBOARD ###

btn_alerts = KeyboardButton(text='⚠️Проверить алерты')
btn_gp = KeyboardButton(text='🚬Статистика GooglePlay')
btn_as = KeyboardButton(text='🔵Статистика AppStore')
kb = [[btn_alerts], [btn_gp, btn_as]]
start_keyboard = ReplyKeyboardMarkup(kb)

######################

with open('whitelist.txt') as f:
	ws = [int(i.strip()) for i in f.readlines()]

def check_ws(func):
	async def wrapper(message: types.Message):
		if message.from_user.id in ws:
			await func(message)
		else:
			await bot.send_message(chat_id=message.from_user.id, text='⚠ Я тебя не знаю. Попроси администратора добавить тебя')
	return wrapper
		
def logged(func):
	async def wrapper(message: types.Message):
		with open('log.txt', 'a', encoding='utf-8') as f:
		    f.write(f'{message.from_user.id} | {message.text} | {dt.datetime.now()}\n')
		await func(message)
	return wrapper


@dp.message_handler(commands=['help'])
@logged
@check_ws
async def help_command(message: types.Message):
	await bot.send_message(chat_id=message.from_user.id, text=BOT_COMMANDS)
	await message.delete()

@dp.message_handler(commands=['start'])
@logged
@check_ws
async def start_command(message: types.Message):
	await bot.send_message(chat_id=message.from_user.id, 
					   text='Выберите действие', 
					   reply_markup=start_keyboard)
	await message.delete()

@dp.message_handler(regexp='Проверить алерты')
@logged
@check_ws
async def alerts_command(message: types.Message):
	await report_alerts(check_alerts_all(), message.from_user.id)

async def report_alerts(alerts: dict, chat_id: int):
	msg = f"""
	Рейтинг приложения в GooglePlay {'✅' if not alerts['gp'] else '❌'}\n
	Рост комментариев в GooglePlay {'✅' if not alerts['com_GP'] else '❌'}\n
	Рейтинг приложения в AppleStore {'✅' if not alerts['ap'] else '❌'}\n
	Рост комментариев в AppleStore {'✅' if not alerts['com_AS'] else '❌'}
	"""
	await bot.send_message(chat_id=chat_id, text=msg)



@dp.message_handler(regexp='🚬Статистика GooglePlay')
@logged
@check_ws
async def gp_command(message: types.Message):
	start = time.time()
	table_manager(name='gp')
	await bot.send_photo(message.from_user.id, open('avg.png', "rb"), caption='Мониториг среднего рейтинга')
	await bot.send_photo(message.from_user.id, open('count.png', "rb"), caption='Мониториг количества отзывов')
	print(time.time() - start)

@dp.message_handler(regexp='🔵Статистика AppStore')
@logged
@check_ws
async def as_command(message: types.Message):
	table_manager(name='ap')
	await bot.send_photo(message.from_user.id, open('avg.png', "rb"), caption='Мониториг среднего рейтинга')
	await bot.send_photo(message.from_user.id, open('count.png', "rb"), caption='Мониториг количества отзывов')

@dp.message_handler()
@logged
@check_ws
async def message_logger(message: types.Message): 
	#handles other msg
	pass


###### SCHEDULER ########
def update_datasets():
	with open('log.txt', 'a', encoding='utf-8') as f:
		print('Выполняется актуализация данных')
		f.write(f'Выполняется актуализация данных | {dt.datetime.now()}\n')
		save_df()
		scrap_reviews()
		print('Актуализация данных закончена')
		f.write(f'Актуализация данных закончена | {dt.datetime.now()}\n')


def check_alerts():
	with open('log.txt', 'a', encoding='utf-8') as f:
		print('Проверка предупреждений')
		f.write(f'Проверка предупреждений | {dt.datetime.now()}\n')
		res = check_alerts_all()
		if any(res.values()):
			report_alerts(res, 1491427573)

async def on_startup(_):
	scheduler.start()
	scheduler.add_job(update_datasets, "interval", hours=2)
	scheduler.add_job(check_alerts, "interval", hours=2)


########################

if __name__ == '__main__':
	executor.start_polling(dp, skip_updates=True, on_startup=on_startup)