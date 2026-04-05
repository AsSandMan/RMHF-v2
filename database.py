import sqlite3
from datetime import datetime

DB_NAME = 'finance.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Таблица пользователей: раздельные счета
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            cash REAL DEFAULT 0,
            card REAL DEFAULT 0,
            savings REAL DEFAULT 0
        )''')
    # Таблица денежных операций
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            category TEXT,
            account TEXT,
            type TEXT,
            note TEXT,
            date TEXT
        )''')
    # Таблица рабочих смен
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_days (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            earnings REAL
        )''')
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    cursor.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY id DESC LIMIT 10", (user_id,))
    transactions = cursor.fetchall()
    conn.close()
    return user, transactions

def add_transaction(user_id, t_type, amount, category, account, note):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    date_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    final_amount = amount if t_type == 'income' else -amount
    
    cursor.execute("INSERT INTO transactions (user_id, amount, category, account, type, note, date) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                   (user_id, final_amount, category, account, t_type, note, date_str))
    cursor.execute(f"UPDATE users SET {account} = {account} + ? WHERE user_id = ?", (final_amount, user_id))
    conn.commit()
    conn.close()

def make_transfer(user_id, from_acc, to_acc, amount):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE users SET {from_acc} = {from_acc} - ? WHERE user_id = ?", (amount, user_id))
    cursor.execute(f"UPDATE users SET {to_acc} = {to_acc} + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_work_stats(user_id, month_year):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM work_days WHERE user_id = ? AND date LIKE ?", (user_id, f'%.{month_year}'))
    shifts = cursor.fetchall()
    conn.close()
    
    total_days = len(shifts)
    total_earned = sum(s['earnings'] for s in shifts)
    avg = total_earned / total_days if total_days > 0 else 0
    return {'total_days': total_days, 'total_earned': total_earned, 'avg_per_day': avg}