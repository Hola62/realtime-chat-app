from typing import Optional, Dict, Any

from mysql.connector import Error

from config.database import get_connection


def init_user_table() -> None:
    """Create users table if it doesn't exist."""
    sql = """
		CREATE TABLE IF NOT EXISTS users (
			id INT AUTO_INCREMENT PRIMARY KEY,
			email VARCHAR(255) NOT NULL UNIQUE,
			password_hash VARCHAR(255) NOT NULL,
			first_name VARCHAR(100) NOT NULL,
			last_name VARCHAR(100) NOT NULL,
			avatar_url TEXT NULL,
			status VARCHAR(32) DEFAULT 'offline',
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
		"""
    conn = get_connection()
    if not conn:
        print("DB not connected; users table creation skipped.")
        return
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    except Error as e:
        print("Error creating users table:", e)
    finally:
        conn.close()


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    if not conn:
        return None
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT * FROM users WHERE email=%s", (email,))
            return cur.fetchone()
    except Error as e:
        print("Error fetching user by email:", e)
        return None
    finally:
        conn.close()


def create_user(
    email: str, password_hash: str, first_name: str, last_name: str
) -> Optional[int]:
    """Create a new user with email, password, first name, and last name.

    Returns: user_id on success, None on failure
    """
    conn = get_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (email, password_hash, first_name, last_name) VALUES (%s, %s, %s, %s)",
                (email, password_hash, first_name, last_name),
            )
            conn.commit()
            return cur.lastrowid
    except Error as e:
        # Duplicate email error code in MySQL is 1062
        if getattr(e, "errno", None) == 1062:
            print("Duplicate email attempted:", email)
            return None
        print("Error creating user:", e)
        return None
    finally:
        conn.close()
