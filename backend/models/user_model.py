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


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID.

    Returns: user dict on success, None on failure
    """
    conn = get_connection()
    if not conn:
        return None
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
            return cur.fetchone()
    except Error as e:
        print("Error fetching user by ID:", e)
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

        if getattr(e, "errno", None) == 1062:
            print("Duplicate email attempted:", email)
            return None
        print("Error creating user:", e)
        return None
    finally:
        conn.close()


def update_user_status(user_id: int, status: str) -> bool:
    """Update user online/offline status.

    Args:
        user_id: The user's ID
        status: 'online' or 'offline'

    Returns: True on success, False on failure
    """
    conn = get_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET status=%s WHERE id=%s", (status, user_id))
            conn.commit()
            return True
    except Error as e:
        print(f"Error updating user status: {e}")
        return False
    finally:
        conn.close()


def update_user_avatar(user_id: int, avatar_url: str) -> bool:
    """Update user avatar URL.

    Args:
        user_id: The user's ID
        avatar_url: URL or path to avatar image

    Returns: True on success, False on failure
    """
    conn = get_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET avatar_url=%s WHERE id=%s", (avatar_url, user_id)
            )
            conn.commit()
            return True
    except Error as e:
        print(f"Error updating user avatar: {e}")
        return False
    finally:
        conn.close()


def update_user_profile(
    user_id: int, first_name: str = None, last_name: str = None, avatar_url: str = None
) -> bool:
    """Update user profile information.

    Args:
        user_id: The user's ID
        first_name: New first name (optional)
        last_name: New last name (optional)
        avatar_url: New avatar URL (optional)

    Returns: True on success, False on failure
    """
    conn = get_connection()
    if not conn:
        return False

    try:
        updates = []
        params = []

        if first_name is not None:
            updates.append("first_name=%s")
            params.append(first_name)

        if last_name is not None:
            updates.append("last_name=%s")
            params.append(last_name)

        if avatar_url is not None:
            updates.append("avatar_url=%s")
            params.append(avatar_url)

        if not updates:
            return False

        params.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id=%s"

        with conn.cursor() as cur:
            cur.execute(query, tuple(params))
            conn.commit()
            return True
    except Error as e:
        print(f"Error updating user profile: {e}")
        return False
    finally:
        conn.close()
