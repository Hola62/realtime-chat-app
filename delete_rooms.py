"""
Delete specific chat rooms from the database
"""

import sys

sys.path.insert(0, "backend")

from config.database import get_connection
import mysql.connector


def delete_rooms():
    """Delete General chat and admin-related rooms."""
    conn = get_connection()
    if not conn:
        print("❌ Could not connect to database")
        return False

    try:
        cursor = conn.cursor(dictionary=True)

        # First, show all rooms
        cursor.execute("SELECT id, name, created_by FROM rooms")
        rooms = cursor.fetchall()

        print("\n📋 Current Rooms:")
        print("-" * 60)
        for room in rooms:
            print(
                f"ID: {room['id']} | Name: {room['name']} | Created by: {room['created_by']}"
            )
        print("-" * 60)

        if not rooms:
            print("\n✓ No rooms found in database")
            return True

        # Ask which rooms to delete
        print("\n🗑️  Which rooms do you want to delete?")
        print("Enter room IDs separated by commas (e.g., 1,2,3)")
        print("Or type 'all' to delete all rooms")
        print("Or press Enter to cancel")

        choice = input("\nYour choice: ").strip()

        if not choice:
            print("\n❌ Cancelled - no rooms deleted")
            return True

        if choice.lower() == "all":
            room_ids = [room["id"] for room in rooms]
        else:
            try:
                room_ids = [int(id.strip()) for id in choice.split(",")]
            except ValueError:
                print("\n❌ Invalid input - please enter numbers separated by commas")
                return False

        # Delete the rooms
        deleted_count = 0
        for room_id in room_ids:
            # Check if room exists
            cursor.execute("SELECT name FROM rooms WHERE id = %s", (room_id,))
            room = cursor.fetchone()

            if room:
                # Delete messages first (due to foreign key)
                cursor.execute("DELETE FROM messages WHERE room_id = %s", (room_id,))
                messages_deleted = cursor.rowcount

                # Delete the room
                cursor.execute("DELETE FROM rooms WHERE id = %s", (room_id,))

                print(
                    f"✓ Deleted room '{room['name']}' (ID: {room_id}) and {messages_deleted} messages"
                )
                deleted_count += 1
            else:
                print(f"⚠️  Room ID {room_id} not found")

        conn.commit()

        print(f"\n✓ Successfully deleted {deleted_count} room(s)")

        # Show remaining rooms
        cursor.execute("SELECT id, name FROM rooms")
        remaining = cursor.fetchall()

        if remaining:
            print("\n📋 Remaining Rooms:")
            for room in remaining:
                print(f"  - {room['name']} (ID: {room['id']})")
        else:
            print("\n✓ No rooms remaining in database")

        return True

    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Delete Chat Rooms")
    print("=" * 60)

    success = delete_rooms()

    print("=" * 60)
    if success:
        print("✓ Operation completed!")
        print("\nRefresh your browser to see the changes.")
    else:
        print("❌ Operation failed - check the errors above")
    print("=" * 60)
