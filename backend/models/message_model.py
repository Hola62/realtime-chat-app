import mysql.connector
from config.database import get_connection


def init_messages_table():
    """Create the messages table if it doesn't exist."""
    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                room_id INT NOT NULL,
                user_id INT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_room_id (room_id),
                INDEX idx_user_id (user_id),
                INDEX idx_timestamp (timestamp)
            )
        """
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except mysql.connector.Error as err:
        print(f"Error creating messages table: {err}")
        if conn:
            conn.close()
        return False


def create_message(room_id: int, user_id: int, content: str):
    """Create a new message in a room."""
    conn = get_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "INSERT INTO messages (room_id, user_id, content) VALUES (%s, %s, %s)",
            (room_id, user_id, content),
        )
        conn.commit()
        message_id = cursor.lastrowid

        # Fetch the complete message with user info
        cursor.execute(
            """
            SELECT m.id, m.room_id, m.user_id, m.content, m.timestamp,
                   u.first_name, u.last_name, u.email
            FROM messages m
            JOIN users u ON m.user_id = u.id
            WHERE m.id = %s
            """,
            (message_id,),
        )
        message = cursor.fetchone()
        cursor.close()
        conn.close()
        return message
    except mysql.connector.Error as err:
        print(f"Error creating message: {err}")
        if conn:
            conn.close()
        return None


def get_room_messages(room_id: int, limit: int = 50):
    """Get messages for a specific room."""
    conn = get_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT m.id, m.room_id, m.user_id, m.content, m.timestamp,
                   u.first_name, u.last_name, u.email
            FROM messages m
            JOIN users u ON m.user_id = u.id
            WHERE m.room_id = %s
            ORDER BY m.timestamp DESC
            LIMIT %s
            """,
            (room_id, limit),
        )
        messages = cursor.fetchall()
        cursor.close()
        conn.close()
        # Return in chronological order (oldest first)
        return list(reversed(messages))
    except mysql.connector.Error as err:
        print(f"Error fetching messages: {err}")
        if conn:
            conn.close()
        return []


def delete_message(message_id: int):
    """Delete a message by ID."""
    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE id = %s", (message_id,))
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        return affected > 0
    except mysql.connector.Error as err:
        print(f"Error deleting message: {err}")
        if conn:
            conn.close()
        return False


# Initialize the table on module import
try:
    init_messages_table()
except Exception as e:
    print(f"Warning: Could not initialize messages table: {e}")
