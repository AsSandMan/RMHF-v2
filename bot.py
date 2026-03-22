import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

BOT_TOKEN = "твой_токен_бота"  # ← замени!

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
        f"Привет! Вот твой личный кабинет:\n\n{app_url}\n\nНажми кнопку ниже:",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

async def main():
    print("Бот запущен. Напиши /start в чате.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())