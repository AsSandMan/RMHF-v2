import sqlite3

DB_NAME = 'finance.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Создаем таблицу пользователей, если её нет
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            wallet REAL DEFAULT 1000.0,
            piggy_bank REAL DEFAULT 0.0
        )
    ''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_user(user_id, username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def update_balance(user_id, amount):
    """Логика перемещения: из wallet в piggy_bank"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Проверяем баланс перед списанием
    cursor.execute("SELECT wallet FROM users WHERE user_id = ?", (user_id,))
    current_wallet = cursor.fetchone()[0]
    
    if current_wallet >= amount:
        cursor.execute("""
            UPDATE users 
            SET wallet = wallet - ?, piggy_bank = piggy_bank + ? 
            WHERE user_id = ?""", (amount, amount, user_id))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False