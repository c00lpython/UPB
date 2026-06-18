# utils/db_handler.py
import sqlite3
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

DB_PATH = Path(__file__).parent.parent / "data" / "users.db"


def get_db():
    """Создаёт соединение с БД и таблицы при первом запуске"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Таблица пользователей
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Таблица сессий
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Таблица результатов пользователей
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            project_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_name TEXT NOT NULL,
            records INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    return conn


def hash_password(password: str) -> str:
    """Хеширует пароль с солью"""
    salt = secrets.token_hex(16)
    return salt + ":" + hashlib.sha256((salt + password).encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Проверяет пароль"""
    salt, hash_val = password_hash.split(":")
    return hash_val == hashlib.sha256((salt + password).encode()).hexdigest()


class UserDB:
    """Работа с пользователями и сессиями"""

    @staticmethod
    def register(username: str, password: str, email: str) -> Dict[str, Any]:
        """Регистрирует нового пользователя"""
        conn = get_db()
        try:
            password_hash = hash_password(password)
            conn.execute(
                "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
                (username, password_hash, email)
            )
            conn.commit()
            return {"success": True, "message": "User registered successfully"}
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                return {"success": False, "error": "Username already exists"}
            if "email" in str(e):
                return {"success": False, "error": "Email already exists"}
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    @staticmethod
    def login(username: str, password: str) -> Dict[str, Any]:
        """Логин пользователя"""
        conn = get_db()
        user = conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        if not user:
            return {"success": False, "error": "User not found"}

        if not verify_password(password, user["password_hash"]):
            return {"success": False, "error": "Invalid password"}

        return {"success": True, "user_id": user["id"], "username": user["username"]}

    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Получает пользователя по email"""
        conn = get_db()
        user = conn.execute(
            "SELECT id, username, email FROM users WHERE email = ?",
            (email,)
        ).fetchone()
        conn.close()
        return dict(user) if user else None

    @staticmethod
    def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
        """Получает пользователя по username"""
        conn = get_db()
        user = conn.execute(
            "SELECT id, username, email FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()
        return dict(user) if user else None

    @staticmethod
    def update_password(username: str, new_password: str) -> Dict[str, Any]:
        """Обновляет пароль пользователя"""
        conn = get_db()
        password_hash = hash_password(new_password)
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (password_hash, username)
        )
        conn.commit()
        conn.close()
        return {"success": True, "message": "Password updated successfully"}

    @staticmethod
    def create_session(user_id: int) -> str:
        """Создаёт сессию для пользователя"""
        conn = get_db()
        token = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(days=7)).isoformat()
        conn.execute(
            "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
            (user_id, token, expires_at)
        )
        conn.commit()
        conn.close()
        return token

    @staticmethod
    def verify_session(token: str) -> Optional[int]:
        """Проверяет сессию и возвращает user_id"""
        conn = get_db()
        session = conn.execute(
            "SELECT user_id FROM sessions WHERE token = ? AND expires_at > datetime('now')",
            (token,)
        ).fetchone()
        conn.close()
        return session["user_id"] if session else None

    # ============ РЕЗУЛЬТАТЫ ============

    @staticmethod
    def add_result(user_id: int, project_name: str, file_path: str, file_name: str, records: int = 0) -> Dict[str, Any]:
        """Сохраняет результат парсинга для пользователя"""
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO user_results (user_id, project_name, file_path, file_name, records) VALUES (?, ?, ?, ?, ?)",
                (user_id, project_name, file_path, file_name, records)
            )
            conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    @staticmethod
    def get_user_results(user_id: int) -> List[Dict[str, Any]]:
        """Получает все результаты пользователя"""
        conn = get_db()
        results = conn.execute(
            "SELECT id, project_name, file_path, file_name, records, created_at FROM user_results WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in results]

    @staticmethod
    def get_result_by_id(result_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает результат по ID (с проверкой владельца)"""
        conn = get_db()
        result = conn.execute(
            "SELECT id, project_name, file_path, file_name, records FROM user_results WHERE id = ? AND user_id = ?",
            (result_id, user_id)
        ).fetchone()
        conn.close()
        return dict(result) if result else None