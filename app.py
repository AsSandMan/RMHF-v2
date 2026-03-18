from flask import Flask, render_template, request, redirect, url_for, abort
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)

DATA_FILE_PREFIX = "home_finance_"

# ───────────────────────────────────────────────
# Получаем user_id из запроса (от фронтенда)
def get_user_id():
    # Сначала пытаемся взять из заголовка (Telegram Mini App)
    user_id = request.headers.get("X-User-Id")
    if user_id:
        return int(user_id)
    
    # Для теста в браузере
    if "localhost" in request.host or "127.0.0.1" in request.host:
        return 600376786  # ← твой Telegram ID
    
    abort(403, "User ID not found")

# ───────────────────────────────────────────────
def load_data():
    user_id = get_user_id()
    filename = f"{DATA_FILE_PREFIX}{user_id}.json"

    if not os.path.exists(filename):
        default = {
            "balance": {"cash": 0, "card": 0, "other": 0, "savings": 0},
            "transactions": []
        }
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
        return {
            "balance": {"cash": 0, "card": 0, "other": 0, "savings": 0},
            "transactions": []
        }

def save_data(data):
    user_id = get_user_id()
    filename = f"{DATA_FILE_PREFIX}{user_id}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ───────────────────────────────────────────────
@app.route("/")
def index():
    data = load_data()
    balance = data["balance"]
    total = sum(balance.values())

    all_tr = data.get("transactions", [])
    last_tr = all_tr[-10:][::-1]

    return render_template(
        "index.html",
        balance=balance,
        total=total,
        last_tr=last_tr
    )

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        data = load_data()

        amount = float(request.form.get("amount", 0))
        tr_type = request.form.get("type", "expense")
        if tr_type == "expense":
            amount = -abs(amount)
        else:
            amount = abs(amount)

        category = request.form.get("category", "Прочее")
        account = request.form.get("account", "cash")
        note = request.form.get("note", "")

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

    return render_template("add.html")

@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    if request.method == "POST":
        data = load_data()
        # ... (твой код перевода без изменений)
        from_acc = request.form.get("from_account")
        to_acc = request.form.get("to_account")
        amount = float(request.form.get("amount", 0))

        if from_acc != to_acc and amount > 0:
            data["balance"][from_acc] -= amount
            data["balance"][to_acc] += amount
            save_data(data)
        return redirect(url_for("index"))
    
    return render_template("transfer.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)