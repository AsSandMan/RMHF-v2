import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.filters import CommandStart
from dotenv import load_dotenv
import os

# ───────────────────────────────────────────────
# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Открыть бухгалтерию",
                web_app=WebAppInfo(url="https://remihf-bot.onrender.com/")
            )
        ]
    ])

    await message.answer(
        "Добро пожаловать! Нажми кнопку ниже, чтобы открыть приложение:",
        reply_markup=keyboard
    )

async def main():
    print("Бот запущен. Напиши /start в чате.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())