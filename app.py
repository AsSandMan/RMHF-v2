import hmac
import hashlib
from flask import request, abort
from dotenv import load_dotenv
import os

# Загружаем .env только если файл существует
load_dotenv()  # автоматически ищет .env в корне проекта

BOT_TOKEN = os.getenv("BOT_TOKEN")


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

# ------------------ защита всех маршрутов ------------------

@app.before_request
def check_telegram_auth():
    if request.path.startswith("/static/"):  # пропускаем статику
        return

    init_data = request.headers.get("X-Telegram-WebApp-InitData") or \
                request.args.get("tg_init_data")  # на случай GET-запросов

    # Для локальной разработки можно временно отключить
    if "localhost" in request.host or "127.0.0.1" in request.host:
        return  # ← раскомментируй на время тестов

    if not init_data or not is_valid_telegram_initdata(init_data):
        abort(403, "Invalid Telegram authentication")



from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
from datetime import datetime
import webview  # pywebview

app = Flask(__name__)

DATA_FILE = "home_finance.json"

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
            
            # Проверяем наличие всех необходимых ключей в балансе
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

@app.route("/")
def index():
    data = load_data()
    balance = data["balance"]
    total = sum(balance.values())
    
    # Разделяем: только выполненные транзакции для истории
    all_tr = data.get("transactions", [])
    completed_tr = [t for t in all_tr if t.get("status") != "planned"]
    planned_tr = [t for t in all_tr if t.get("status") == "planned"]
    
    last_tr = completed_tr[-10:][::-1] # Последние 10

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
            # Списываем с одного, добавляем на другой
            data["balance"][from_acc] -= amount
            data["balance"][to_acc] += amount
            
            # Записываем как техническую транзакцию
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
                amount = 0.0  # защита от мусора
            
            category = request.form.get("category", "Прочее").strip()
            account = request.form.get("account", "cash").strip()
            note = request.form.get("note", "").strip()

            if amount == 0:
                # Можно добавить flash-сообщение об ошибке, но пока просто пропустим
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
            # Некорректная сумма — можно вернуть с ошибкой
            return render_template("add.html", error="Сумма должна быть числом")

    # GET — показываем пустую форму
    return render_template("add.html")

# Запуск как десктоп-приложение
if __name__ == "__main__":
    # Для разработки можно запускать так:
    # app.run(debug=True, port=5050)

    # Для десктоп-версии:
    window = webview.create_window(
        "Моя Бухгалтерия",
        "http://127.0.0.1:5050",
        width=1100,
        height=800,
        resizable=True,
        frameless=False,  # можно True для кастомного вида
        easy_drag=True
    )
    # Запускаем flask в отдельном потоке
    import threading
    server = threading.Thread(target=app.run, kwargs={"port": 5050, "use_reloader": False, "debug": False})
    server.daemon = True
    server.start()

    webview.start()