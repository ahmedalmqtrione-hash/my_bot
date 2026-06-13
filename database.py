import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path="./moallem.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER UNIQUE, username TEXT, first_name TEXT, last_name TEXT, department TEXT DEFAULT 'general', points INTEGER DEFAULT 0, level INTEGER DEFAULT 1, streak INTEGER DEFAULT 0, last_active DATE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS conversations (id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER, message TEXT, response TEXT, agent_type TEXT, department TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS banned_users (telegram_id INTEGER PRIMARY KEY, reason TEXT, banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER, username TEXT, message TEXT, rating INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS quiz_scores (id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER, department TEXT, score INTEGER, total INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS channel_files (id INTEGER PRIMARY KEY AUTOINCREMENT, file_id TEXT UNIQUE, file_unique_id TEXT, file_name TEXT, file_type TEXT, category TEXT, department TEXT, caption TEXT, file_size INTEGER, uploaded_by INTEGER, message_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        conn.commit()
        conn.close()

    def add_user(self, telegram_id, username, first_name, last_name):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute("INSERT OR IGNORE INTO users (telegram_id, username, first_name, last_name, last_active) VALUES (?, ?, ?, ?, ?)", (telegram_id, username, first_name, last_name, datetime.now().date()))
            conn.commit()
        except: pass
        finally: conn.close()

    def update_user(self, telegram_id, **kwargs):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            for key, value in kwargs.items():
                c.execute(f"UPDATE users SET {key} = ? WHERE telegram_id = ?", (value, telegram_id))
            c.execute("UPDATE users SET last_active = ? WHERE telegram_id = ?", (datetime.now().date(), telegram_id))
            conn.commit()
        except: pass
        finally: conn.close()

    def get_user(self, telegram_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        result = c.fetchone()
        conn.close()
        return result

    def add_points(self, telegram_id, points):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute("UPDATE users SET points = points + ? WHERE telegram_id = ?", (points, telegram_id))
            c.execute("""UPDATE users SET level = CASE
                WHEN points >= 1000 THEN 10 WHEN points >= 800 THEN 9
                WHEN points >= 600 THEN 8 WHEN points >= 500 THEN 7
                WHEN points >= 400 THEN 6 WHEN points >= 300 THEN 5
                WHEN points >= 200 THEN 4 WHEN points >= 100 THEN 3
                WHEN points >= 50 THEN 2 ELSE 1 END WHERE telegram_id = ?""", (telegram_id,))
            conn.commit()
        except: pass
        finally: conn.close()

    def save_conversation(self, telegram_id, message, response, agent_type, department):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO conversations (telegram_id, message, response, agent_type, department) VALUES (?, ?, ?, ?, ?)", (telegram_id, message, response, agent_type, department))
            conn.commit()
        except: pass
        finally: conn.close()

    def save_quiz_score(self, telegram_id, department, score, total):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO quiz_scores (telegram_id, department, score, total) VALUES (?, ?, ?, ?)", (telegram_id, department, score, total))
            conn.commit()
            self.add_points(telegram_id, score)
        except: pass
        finally: conn.close()

    def save_feedback(self, telegram_id, username, message, rating=0):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO feedback (telegram_id, username, message, rating) VALUES (?, ?, ?, ?)", (telegram_id, username, message, rating))
            conn.commit()
        except: pass
        finally: conn.close()

    def save_channel_file(self, file_id, file_unique_id, file_name, file_type, category, department, caption, file_size, uploaded_by, message_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute("INSERT OR IGNORE INTO channel_files (file_id, file_unique_id, file_name, file_type, category, department, caption, file_size, uploaded_by, message_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (file_id, file_unique_id, file_name, file_type, category, department, caption, file_size, uploaded_by, message_id))
            conn.commit()
            return True
        except: return False
        finally: conn.close()

    def search_files(self, query, category=None, department=None):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            if category and department:
                c.execute("SELECT file_id, file_name, file_type, category, caption, created_at FROM channel_files WHERE (file_name LIKE ? OR caption LIKE ?) AND category = ? AND department = ? ORDER BY created_at DESC LIMIT 50", (f"%{query}%", f"%{query}%", category, department))
            elif category:
                c.execute("SELECT file_id, file_name, file_type, category, caption, created_at FROM channel_files WHERE (file_name LIKE ? OR caption LIKE ?) AND category = ? ORDER BY created_at DESC LIMIT 50", (f"%{query}%", f"%{query}%", category))
            elif department:
                c.execute("SELECT file_id, file_name, file_type, category, caption, created_at FROM channel_files WHERE (file_name LIKE ? OR caption LIKE ?) AND department = ? ORDER BY created_at DESC LIMIT 50", (f"%{query}%", f"%{query}%", department))
            else:
                c.execute("SELECT file_id, file_name, file_type, category, caption, created_at FROM channel_files WHERE file_name LIKE ? OR caption LIKE ? ORDER BY created_at DESC LIMIT 50", (f"%{query}%", f"%{query}%"))
            return c.fetchall()
        except: return []
        finally: conn.close()

    def get_files_by_category(self, category, department=None, limit=20):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            if department:
                c.execute("SELECT file_id, file_name, file_type, caption, created_at FROM channel_files WHERE category = ? AND department = ? ORDER BY created_at DESC LIMIT ?", (category, department, limit))
            else:
                c.execute("SELECT file_id, file_name, file_type, caption, created_at FROM channel_files WHERE category = ? ORDER BY created_at DESC LIMIT ?", (category, limit))
            return c.fetchall()
        except: return []
        finally: conn.close()

    def is_banned(self, telegram_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT 1 FROM banned_users WHERE telegram_id = ?", (telegram_id,))
        result = c.fetchone()
        conn.close()
        return result is not None

    def ban_user(self, telegram_id, reason=""):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute("INSERT OR REPLACE INTO banned_users (telegram_id, reason) VALUES (?, ?)", (telegram_id, reason))
            conn.commit()
        except: pass
        finally: conn.close()

    def unban_user(self, telegram_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute("DELETE FROM banned_users WHERE telegram_id = ?", (telegram_id,))
            conn.commit()
        except: pass
        finally: conn.close()

    def get_all_users(self, limit=100):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT telegram_id, username, first_name, last_name, department, points, level, created_at FROM users ORDER BY created_at DESC LIMIT ?", (limit,))
        users = c.fetchall()
        conn.close()
        return users

    def get_leaderboard(self, limit=10):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT first_name, last_name, username, points, level FROM users ORDER BY points DESC LIMIT ?", (limit,))
        result = c.fetchall()
        conn.close()
        return result

    def get_statistics(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute("SELECT COUNT(*) FROM users")
            total_users = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM conversations")
            total_messages = c.fetchone()[0]
            c.execute("SELECT COUNT(DISTINCT telegram_id) FROM conversations WHERE created_at >= date('now', 'start of day')")
            active_today = c.fetchone()[0]
            c.execute("SELECT department, COUNT(*) as count FROM conversations GROUP BY department ORDER BY count DESC LIMIT 1")
            result = c.fetchone()
            top_department = result[0] if result else "عام"
            c.execute("SELECT COUNT(*) FROM users WHERE created_at >= date('now', '-1 day')")
            new_today = c.fetchone()[0]
            c.execute("SELECT SUM(points) FROM users")
            total_points = c.fetchone()[0] or 0
            c.execute("SELECT COUNT(*) FROM channel_files")
            total_files = c.fetchone()[0]
            return {"total_users": total_users, "total_messages": total_messages, "active_today": active_today, "top_department": top_department, "new_today": new_today, "total_points": total_points, "total_files": total_files}
        except:
            return {"total_users": 0, "total_messages": 0, "active_today": 0, "top_department": "عام", "new_today": 0, "total_points": 0, "total_files": 0}
        finally:
            conn.close()

db = Database()
