"""
Fix database schema - Add missing 'deleted' column to messages table
"""

import sys

sys.path.insert(0, "backend")

from config.database import get_connection
import mysql.connector


def fix_database():
    """Add the deleted column to messages table if it doesn't exist."""
    conn = get_connection()
    if not conn:
        print("❌ Could not connect to database")
        return False

    try:
        cursor = conn.cursor()

        # Check if column exists
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'messages' 
            AND COLUMN_NAME = 'deleted'
        """
        )

        result = cursor.fetchone()
        column_exists = result[0] > 0

        if column_exists:
            print("✓ Column 'deleted' already exists in messages table")
        else:
            print("Adding 'deleted' column to messages table...")
            cursor.execute(
                """
                ALTER TABLE messages 
                ADD COLUMN deleted BOOLEAN DEFAULT FALSE
            """
            )
            conn.commit()
            print("✓ Column 'deleted' added successfully!")

        # Verify the column
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'messages' 
            AND COLUMN_NAME = 'deleted'
        """
        )

        result = cursor.fetchone()
        if result[0] > 0:
            print("✓ Database schema is now correct!")

            # Show current message count
            cursor.execute("SELECT COUNT(*) FROM messages")
            count = cursor.fetchone()[0]
            print(f"📊 Total messages in database: {count}")

            return True
        else:
            print("❌ Column still missing after fix attempt")
            return False

    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Database Schema Fix")
    print("=" * 50)

    success = fix_database()

    print("=" * 50)
    if success:
        print("✓ Database fix completed successfully!")
        print("\nYou can now:")
        print("1. Restart your servers")
        print("2. Refresh your browser")
        print("3. Messages should now load properly!")
    else:
        print("❌ Database fix failed - check the errors above")
    print("=" * 50)
