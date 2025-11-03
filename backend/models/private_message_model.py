from typing import List, Dict, Optional

import mysql.connector
from mysql.connector import Error

from config.database import get_connection


def init_private_messages_table() -> bool:
    """Create the private_messages table if it doesn't exist."""
    conn = get_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS private_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                room_key VARCHAR(64) NOT NULL,
                sender_id INT NOT NULL,
                receiver_id INT NOT NULL,
                content TEXT NOT NULL,
                deleted BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_room_key (room_key),
                INDEX idx_sender (sender_id),
                INDEX idx_receiver (receiver_id),
                INDEX idx_pm_timestamp (timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Error as e:
        print("Error creating private_messages table:", e)
        if conn:
            conn.close()
        return False


def create_private_message(
    room_key: str, sender_id: int, receiver_id: int, content: str
) -> Optional[Dict]:
    """Insert a new private message and return the populated record with sender user fields."""
    conn = get_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            INSERT INTO private_messages (room_key, sender_id, receiver_id, content)
            VALUES (%s, %s, %s, %s)
            """,
            (room_key, sender_id, receiver_id, content),
        )
        conn.commit()
        msg_id = cur.lastrowid

        cur.execute(
            """
            SELECT pm.id, pm.room_key, pm.sender_id, pm.receiver_id, pm.content, pm.deleted, pm.timestamp,
                   u.first_name, u.last_name, u.email, u.avatar_url
            FROM private_messages pm
            JOIN users u ON pm.sender_id = u.id
            WHERE pm.id = %s
            """,
            (msg_id,),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row
    except Error as e:
        print("Error creating private message:", e)
        if conn:
            conn.close()
        return None


def get_private_messages(room_key: str, limit: int = 50) -> List[Dict]:
    """Fetch private messages for the room_key ordered by time ascending (oldest first)."""
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT pm.id, pm.room_key, pm.sender_id, pm.receiver_id, pm.content, pm.deleted, pm.timestamp,
                   u.first_name, u.last_name, u.email, u.avatar_url
            FROM private_messages pm
            JOIN users u ON pm.sender_id = u.id
            WHERE pm.room_key = %s
            ORDER BY pm.timestamp DESC
            LIMIT %s
            """,
            (room_key, limit),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        # Return in chronological order (oldest first)
        return list(reversed(rows))
    except Error as e:
        print("Error fetching private messages:", e)
        if conn:
            conn.close()
        return []


try:
    init_private_messages_table()
except Exception as e:
    print(f"Warning: Could not initialize private_messages table: {e}")
