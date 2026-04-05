import os
import threading
import asyncio
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from aiogram import Bot, Dispatcher, types, executor
from database import init_db, add_user, get_user, update_balance

# Настройки
# # Загружаем переменные из .env
# load_dotenv()

# # Теперь достаем токен безопасно
# API_TOKEN = os.getenv('BOT_TOKEN')
if os.path.exists(".env"):
    load_dotenv()

# Пробуем достать токен
API_TOKEN = os.getenv('BOT_TOKEN')

# Маленький лайфхак для отладки (в логи Render выведет длину токена)
if API_TOKEN:
    print(f"DEBUG: Токен найден, длина: {len(API_TOKEN)} символов")
else:
    print("DEBUG: Токен не найден в переменных окружения!")

# Проверка токена перед запуском бота
if not API_TOKEN or ":" not in API_TOKEN:
    raise ValueError("Ошибка: BOT_TOKEN пустой или имеет неверный формат!")

if not API_TOKEN:
    exit("Ошибка: Токен бота не найден! Проверь файл .env или переменные окружения.")

app = Flask(__name__)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- БОТ (aiogram) ---
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    add_user(message.from_user.id, message.from_user.username)
    
    # Кнопка для открытия Web App
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # Замени URL на адрес своего сервера, когда задеплоишь
    web_app = types.WebAppInfo(url="https://rmhf-v2.onrender.com") 
    markup.add(types.KeyboardButton("Открыть Кошелек 💳", web_app=web_app))
    
    await message.reply(f"Привет, {message.from_user.first_name}! Твой счет активирован.", reply_markup=markup)

# --- ВЕБ-ПРИЛОЖЕНИЕ (Flask API) ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get_balance', methods=['GET'])
def get_balance():
    user_id = request.args.get('user_id')
    user = get_user(user_id)
    if user:
        return jsonify({'wallet': user[2], 'piggy': user[3]})
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/transfer', methods=['POST'])
def transfer():
    data = request.json
    success = update_balance(data['user_id'], float(data['amount']))
    return jsonify({'success': success})

# Функция запуска бота в отдельном потоке

def run_bot():
    # Создаем новый цикл событий специально для этого потока
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Запускаем поллинг через этот цикл
    executor.start_polling(dp, skip_updates=True, loop=loop)

if __name__ == '__main__':
    init_db()
    # Запускаем бота в фоне
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Render дает порт через переменную окружения PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)