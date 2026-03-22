from flask import Flask, render_template, request, redirect, url_for
import os
import json
from datetime import datetime
import asyncio
import threading
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)

DATA_DIR = "user_data"
os.makedirs(DATA_DIR, exist_ok=True)

def get_data_file(user_id):
    return os.path.join(DATA_DIR, f"home_finance_{user_id}.json")

def load_data(user_id):
    filename = get_data_file(user_id)
    if not os.path.exists(filename):
        default = {"balance": {"cash": 0, "card": 0, "other": 0, "savings": 0}, "transactions": []}
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default

    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            for key in ["cash", "card", "other", "savings"]:
                data["balance"].setdefault(key, 0)
            return data
    except:
        return {"balance": {"cash": 0, "card": 0, "other": 0, "savings": 0}, "transactions": []}

def save_data(user_id, data):
    filename = get_data_file(user_id)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/<int:user_id>")
def index(user_id):
    data = load_data(user_id)
    balance = data["balance"]
    total = sum(balance.values())
    all_tr = data.get("transactions", [])
    last_tr = all_tr[-10:][::-1] if all_tr else []
    return render_template("index.html", balance=balance, total=total, last_tr=last_tr, user_id=user_id)

@app.route("/<int:user_id>/add", methods=["GET", "POST"])
def add(user_id):
    if request.method == "POST":
        data = load_data(user_id)
        amount = float(request.form.get("amount", 0))
        tr_type = request.form.get("type", "expense")
        amount = -abs(amount) if tr_type == "expense" else abs(amount)
        if amount == 0:
            return redirect(url_for("index", user_id=user_id))
        category = request.form.get("category", "Прочее")
        account = request.form.get("account", "cash")
        note = request.form.get("note", "")
        tr = {"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "type": "доход" if amount > 0 else "расход", "amount": amount, "category": category, "account": account, "note": note}
        data["transactions"].append(tr)
        data["balance"][account] = data["balance"].get(account, 0) + amount
        save_data(user_id, data)
        return redirect(url_for("index", user_id=user_id))
    return render_template("add.html", user_id=user_id)

# ───────────────────────────────────────────────
# Бот в фоне
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    app_url = f"https://remihf-bot.onrender.com/{user_id}"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Открыть бухгалтерию", url=app_url)]
    ])
    await message.answer(f"Привет! Твой кабинет:\n{app_url}", reply_markup=keyboard, disable_web_page_preview=True)

async def run_bot():
    await dp.start_polling(bot)

def start_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot())

# Запускаем бота в отдельном потоке
threading.Thread(target=start_bot, daemon=True).start()

# Запускаем Flask
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)