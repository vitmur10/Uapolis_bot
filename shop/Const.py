from dotenv import load_dotenv
import os
from aiogram import Bot, Dispatcher, Router, types
from aiogram.fsm.storage.memory import MemoryStorage

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TOKEN_NP = os.getenv('TOKEN_NP')

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())