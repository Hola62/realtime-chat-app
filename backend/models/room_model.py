import mysql.connector
from config.database import get_connection


def init_rooms_table():
    """Create the rooms table if it doesn't exist."""
    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rooms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                created_by INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_created_by (created_by)
            )
        """
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except mysql.connector.Error as err:
        print(f"Error creating rooms table: {err}")
        if conn:
            conn.close()
        return False


def create_room(name: str, created_by: int):
    """Create a new chat room."""
    conn = get_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO rooms (name, created_by) VALUES (%s, %s)", (name, created_by)
        )
        conn.commit()
        room_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return room_id
    except mysql.connector.Error as err:
        print(f"Error creating room: {err}")
        if conn:
            conn.close()
        return None


def get_room_by_id(room_id: int):
    """Get a room by ID."""
    conn = get_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT r.id, r.name, r.created_at, 
                   u.first_name, u.last_name, u.email as creator_email
            FROM rooms r
            JOIN users u ON r.created_by = u.id
            WHERE r.id = %s
            """,
            (room_id,),
        )
        room = cursor.fetchone()
        cursor.close()
        conn.close()
        return room
    except mysql.connector.Error as err:
        print(f"Error fetching room: {err}")
        if conn:
            conn.close()
        return None


def get_all_rooms():
    """Get all chat rooms."""
    conn = get_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT r.id, r.name, r.created_at, 
                   u.first_name, u.last_name, u.email as creator_email
            FROM rooms r
            JOIN users u ON r.created_by = u.id
            ORDER BY r.created_at DESC
            """
        )
        rooms = cursor.fetchall()
        cursor.close()
        conn.close()
        return rooms
    except mysql.connector.Error as err:
        print(f"Error fetching rooms: {err}")
        if conn:
            conn.close()
        return []


def delete_room(room_id: int):
    """Delete a room by ID."""
    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM rooms WHERE id = %s", (room_id,))
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        return affected > 0
    except mysql.connector.Error as err:
        print(f"Error deleting room: {err}")
        if conn:
            conn.close()
        return False



try:
    init_rooms_table()
except Exception as e:
    print(f"Warning: Could not initialize rooms table: {e}")
