from flask import Flask, render_template, request, redirect, url_for, abort
import os
import json
from datetime import datetime

app = Flask(__name__)

# Папка для персональных данных пользователей
DATA_DIR = "user_data"
os.makedirs(DATA_DIR, exist_ok=True)

def get_data_file(user_id: int) -> str:
    return os.path.join(DATA_DIR, f"home_finance_{user_id}.json")

def load_data(user_id: int) -> dict:
    filename = get_data_file(user_id)
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
            # Заполняем недостающие ключи
            for key in ["cash", "card", "other", "savings"]:
                data["balance"].setdefault(key, 0)
            return data
    except Exception as e:
        print(f"Ошибка загрузки данных для {user_id}: {e}")
        return {
            "balance": {"cash": 0, "card": 0, "other": 0, "savings": 0},
            "transactions": []
        }

def save_data(user_id: int, data: dict):
    filename = get_data_file(user_id)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Главная страница — /<user_id>
@app.route("/<int:user_id>")
def index(user_id):
    data = load_data(user_id)
    balance = data["balance"]
    total = sum(balance.values())

    all_tr = data.get("transactions", [])
    last_tr = all_tr[-10:][::-1] if all_tr else []

    return render_template(
        "index.html",
        balance=balance,
        total=total,
        last_tr=last_tr,
        user_id=user_id  # для ссылок в шаблоне
    )

# Добавление операции
@app.route("/<int:user_id>/add", methods=["GET", "POST"])
def add(user_id):
    if request.method == "POST":
        data = load_data(user_id)

        try:
            amount = float(request.form.get("amount", 0))
            tr_type = request.form.get("type", "expense")
            if tr_type == "expense":
                amount = -abs(amount)
            else:
                amount = abs(amount)

            if amount == 0:
                return redirect(url_for("index", user_id=user_id))

            category = request.form.get("category", "Прочее")
            account = request.form.get("account", "cash")
            note = request.form.get("note", "")

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
            save_data(user_id, data)

            return redirect(url_for("index", user_id=user_id))

        except ValueError:
            return render_template("add.html", user_id=user_id, error="Сумма должна быть числом")

    return render_template("add.html", user_id=user_id)

# Перевод между счетами (если нужен)
@app.route("/<int:user_id>/transfer", methods=["GET", "POST"])
def transfer(user_id):
    if request.method == "POST":
        data = load_data(user_id)
        from_acc = request.form.get("from_account")
        to_acc = request.form.get("to_account")
        amount = float(request.form.get("amount", 0))

        if from_acc != to_acc and amount > 0 and from_acc in data["balance"] and to_acc in data["balance"]:
            data["balance"][from_acc] -= amount
            data["balance"][to_acc] += amount
            save_data(user_id, data)

        return redirect(url_for("index", user_id=user_id))

    return render_template("transfer.html", user_id=user_id)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)