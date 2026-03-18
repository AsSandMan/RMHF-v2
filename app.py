from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
import hmac
import hashlib
from datetime import datetime

# ───────────────────────────────────────────────
# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Создаём приложение Flask
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # для теста; потом можно сузить

# ───────────────────────────────────────────────
# Функции валидации Telegram initData
def is_valid_telegram_initdata(init_data: str) -> bool:
    if not BOT_TOKEN:
        return False
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

def get_user_id_from_initdata(init_data_str: str) -> int | None:
    try:
        params = dict(p.split("=", 1) for p in init_data_str.split("&") if "=" in p)
        user_json = params.get("user")
        if user_json:
            user_data = json.loads(user_json)
            return user_data.get("id")
    except:
        pass 
    return None

# ───────────────────────────────────────────────
# Защита всех маршрутов
@app.before_request
def check_telegram_auth():
    if request.path.startswith("/static/"):
        return

    init_data = (
        request.headers.get("X-Telegram-WebApp-InitData") or
        request.args.get("tg_init_data") or
        request.form.get("tg_init_data")
    )

    # Локальный тест
    if "localhost" in request.host or "127.0.0.1" in request.host:
        request.user_id = 600376786  # ← замени на свой Telegram ID для теста
        return

    print(f"[DEBUG] Request method: {request.method}")
    print(f"[DEBUG] Headers: {dict(request.headers)}")
    print(f"[DEBUG] Args: {request.args}")
    print(f"[DEBUG] Form: {request.form}")
    print(f"[DEBUG] init_data found: {bool(init_data)}")
    if init_data:
        print(f"[DEBUG] init_data length: {len(init_data)}")

    # Если нет init_data → это прямой доступ по ссылке
    if not init_data:
        return render_template("not_in_telegram.html"), 403

    if not is_valid_telegram_initdata(init_data):
        return abort(403, "Недействительная авторизация Telegram")

    user_id = get_user_id_from_initdata(init_data)
    if not user_id:
        return abort(403, "Не удалось определить пользователя")

    # Сохраняем user_id для использования в маршрутах
    request.user_id = user_id

# ───────────────────────────────────────────────
# Работа с данными (персональные файлы)
def load_data():
    user_id = getattr(request, "user_id", None)
    if not user_id:
        abort(500, "User ID not found")

    filename = f"home_finance_{user_id}.json"

    if not os.path.exists(filename):
        default_data = {
            "balance": {"cash": 0, "card": 0, "other": 0, "savings": 0},
            "transactions": []
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)
        return default_data

    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                default_data = {
                    "balance": {"cash": 0, "card": 0, "other": 0, "savings": 0},
                    "transactions": []
                }
                with open(filename, "w", encoding="utf-8") as fw:
                    json.dump(default_data, fw, ensure_ascii=False, indent=2)
                return default_data

            data = json.loads(content)
            default_balance = {"cash": 0, "card": 0, "other": 0, "savings": 0}
            for key in default_balance:
                data["balance"].setdefault(key, 0)
            return data
    except Exception as e:
        print(f"Ошибка чтения {filename}: {e}")
        default_data = {
            "balance": {"cash": 0, "card": 0, "other": 0, "savings": 0},
            "transactions": []
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)
        return default_data

def save_data(data):
    user_id = getattr(request, "user_id", None)
    if not user_id:
        abort(500, "User ID not found")

    filename = f"home_finance_{user_id}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ───────────────────────────────────────────────
# Маршруты
@app.route("/")
def index():
    data = load_data()
    balance = data["balance"]
    total = sum(balance.values())

    all_tr = data.get("transactions", [])
    completed_tr = [t for t in all_tr if t.get("status") != "planned"]
    planned_tr = [t for t in all_tr if t.get("status") == "planned"]

    last_tr = completed_tr[-10:][::-1]

    return render_template(
        "index.html",
        balance=balance,
        total=total,
        last_tr=last_tr,
        planned_tr=planned_tr
    )

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
            data["balance"][account] = data["balance"].get(account, 0) + amount

            save_data(data)
            return redirect(url_for("index"))

        except ValueError:
            return render_template("add.html", error="Сумма должна быть числом")

    return render_template("add.html")

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

# Запуск (локально и на сервере)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)