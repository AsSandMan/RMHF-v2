from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
import hmac
import hashlib
from datetime import datetime

# Загружаем .env (если есть)
load_dotenv()

# Токен бота из переменных окружения (.env или Render)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Создаём приложение Flask ПЕРВЫМ ДЕЛОМ
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # для теста; потом можно сузить

DATA_FILE = "home_finance.json"

# Функция валидации Telegram initData
def is_valid_telegram_initdata(init_data: str) -> bool:
    if not BOT_TOKEN:
        return False  # на локалхосте можно временно отключить проверку
    try:
        params = dict(p.split("=", 1) for p in init_data.split("&") if "=" in p)
        received_hash = params.pop("hash", None)
        if not received_hash:
            return False

        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        return calculated == received_hash
    except:
        return False

# Защита всех маршрутов (кроме статики)
@app.before_request
def check_telegram_auth():
    if request.path.startswith("/static/"):
        return

    init_data = (request.headers.get("X-Telegram-WebApp-InitData") or
                request.args.get("tg_init_data") or
                request.args.get("tgWebAppData"))

    # Для локальной разработки отключаем проверку
    if "localhost" in request.host or "127.0.0.1" in request.host:
        return

    if not init_data or not is_valid_telegram_initdata(init_data):
        abort(403, "Invalid Telegram authentication")

# ───────────────────────────────────────────────
# Функции работы с данными (без изменений)
def load_data():
    default_structure = {
        "balance": {"cash": 0, "card": 0, "other": 0, "savings": 0},
        "transactions": []
    }
    
    if not os.path.exists(DATA_FILE):
        return default_structure

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return default_structure
            
            data = json.loads(content)
            
            # Проверяем наличие всех ключей в балансе
            for wallet in default_structure["balance"]:
                if wallet not in data["balance"]:
                    data["balance"][wallet] = 0
            
            return data
    except Exception as e:
        print(f"Ошибка чтения: {e}")
        return default_structure

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ───────────────────────────────────────────────
# Маршруты (без изменений)
@app.route("/")
def index():
    data = load_data()
    balance = data["balance"]
    total = sum(balance.values())
    
    all_tr = data.get("transactions", [])
    completed_tr = [t for t in all_tr if t.get("status") != "planned"]
    planned_tr = [t for t in all_tr if t.get("status") == "planned"]
    
    last_tr = completed_tr[-10:][::-1]  # Последние 10

    return render_template(
        "index.html",
        balance=balance,
        total=total,
        last_tr=last_tr,
        planned_tr=planned_tr
    )

@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    if request.method == "POST":
        data = load_data()
        from_acc = request.form.get("from_account")
        to_acc = request.form.get("to_account")
        amount = float(request.form.get("amount", 0))

        if from_acc != to_acc and amount > 0:
            data["balance"][from_acc] -= amount
            data["balance"][to_acc] += amount
            
            tr = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "type": "перевод",
                "amount": amount,
                "category": "Перевод",
                "account": f"{from_acc} → {to_acc}",
                "status": "completed"
            }
            data["transactions"].append(tr)
            save_data(data)
        return redirect(url_for("index"))
    
    return render_template("transfer.html")

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        try:
            data = load_data()
            
            amount_str = request.form.get("amount", "0").strip()
            amount = float(amount_str) if amount_str else 0.0
            
            tr_type = request.form.get("type", "expense")
            if tr_type == "expense":
                amount = -abs(amount)
            elif tr_type == "income":
                amount = abs(amount)
            else:
                amount = 0.0
            
            category = request.form.get("category", "Прочее").strip()
            account = request.form.get("account", "cash").strip()
            note = request.form.get("note", "").strip()

            if amount == 0:
                return redirect(url_for("index"))

            tr = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "type": "доход" if amount > 0 else "расход",
                "amount": amount,
                "category": category,
                "account": account,
                "note": note
            }
            
            data["transactions"].append(tr)
            if account in data["balance"]:
                data["balance"][account] += amount
            else:
                data["balance"][account] = amount
            
            save_data(data)
            return redirect(url_for("index"))
            
        except ValueError:
            return render_template("add.html", error="Сумма должна быть числом")

    return render_template("add.html")

# Запуск приложения
if __name__ == "__main__":
    # Для локального запуска (python app.py)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)