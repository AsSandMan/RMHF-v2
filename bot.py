import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
import os

# ───────────────────────────────────────────────
# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    app_url = f"https://remihf-bot.onrender.com/{user_id}"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Открыть Мою бухгалтерию", url=app_url)]
    ])

    await message.answer(
        f"Привет! Твой личный кабинет:\n\n{app_url}\n\nНажми кнопку:",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

async def main():
    print("Бот запущен")
    await dp.start_polling(bot)

# Фейковый сервер, чтобы Render не убивал процесс
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_dummy_server():
    server_address = ('', int(os.environ.get("PORT", 10000)))
    httpd = HTTPServer(server_address, DummyHandler)
    print(f"Фейковый сервер на порту {server_address[1]} для Render")
    httpd.serve_forever()

if __name__ == "__main__":
    # Запускаем фейковый сервер в отдельном потоке
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    # Запускаем бота
    asyncio.run(main())