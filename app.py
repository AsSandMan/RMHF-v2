import os
import threading
import asyncio
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
from aiogram import Bot, Dispatcher, types, executor
from database import *

load_dotenv()
API_TOKEN = os.getenv('BOT_TOKEN')
if API_TOKEN:
    API_TOKEN = API_TOKEN.strip()

app = Flask(__name__)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- ЛОГИКА БОТА ---
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    add_user(message.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # ЗАМЕНИ НА СВОЮ ССЫЛКУ ОТ RENDER
    web_app = types.WebAppInfo(url="https://rmhf-v2.onrender.com") 
    markup.add(types.KeyboardButton("Открыть Бухгалтерию 💰", web_app=web_app))
    await message.reply("Привет! Твой личный фин-помощник готов.", reply_markup=markup)

# --- МАРШРУТЫ WEB APP ---
@app.route('/')
def index():
    user_id = request.args.get('user_id') or request.headers.get('X-User-Id')
    if not user_id: return "Запустите через Telegram"
    
    user, last_tr = get_user_data(user_id)
    if not user:
        add_user(user_id)
        user, last_tr = get_user_data(user_id)
        
    total = user['cash'] + user['card'] + user['savings']
    return render_template('index.html', balance=user, last_tr=last_tr, total=total, user_id=user_id)

@app.route('/<user_id>/add', methods=['GET', 'POST'])
def add(user_id):
    if request.method == 'POST':
        add_transaction(user_id, request.form.get('type'), float(request.form.get('amount')),
                        request.form.get('category'), request.form.get('account'), request.form.get('note'))
        return redirect(url_for('index', user_id=user_id))
    return render_template('add.html', user_id=user_id)

@app.route('/transfer', methods=['POST'])
def transfer_money():
    user_id = request.form.get('user_id')
    make_transfer(user_id, request.form.get('from_account'), request.form.get('to_account'), float(request.form.get('amount')))
    return redirect(url_for('index', user_id=user_id))

@app.route('/<user_id>/work-stats')
def work_stats(user_id):
    stats = get_work_stats(user_id, datetime.now().strftime("%m.%Y"))
    return render_template('work_stats.html', stats=stats, user_id=user_id)

@app.route('/<user_id>/add-work', methods=['POST'])
def add_work(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO work_days (user_id, date, earnings) VALUES (?, ?, ?)", 
                   (user_id, datetime.now().strftime("%d.%m.%Y"), float(request.form.get('earnings', 0))))
    conn.commit()
    conn.close()
    return redirect(url_for('work_stats', user_id=user_id))

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    executor.start_polling(dp, skip_updates=True)

if __name__ == '__main__':
    init_db()
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)