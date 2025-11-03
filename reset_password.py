"""Reset password for a user account."""

import sys
import os
from getpass import getpass

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from config.database import get_connection
from werkzeug.security import generate_password_hash


def reset_password(email, new_password):
    """Reset password for a user."""
    conn = get_connection()
    if not conn:
        print("❌ Could not connect to database")
        return False

    try:
        cursor = conn.cursor(dictionary=True)

        # Check if user exists
        cursor.execute(
            "SELECT id, email, first_name, last_name FROM users WHERE email = %s",
            (email,),
        )
        user = cursor.fetchone()

        if not user:
            print(f"❌ No user found with email: {email}")
            cursor.close()
            conn.close()
            return False

        print(
            f"✓ Found user: {user['first_name']} {user['last_name']} ({user['email']})"
        )

        # Hash the new password
        password_hash = generate_password_hash(new_password)

        # Update password
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (password_hash, user["id"]),
        )
        conn.commit()

        print(f"✓ Password updated successfully!")
        print(f"\nYou can now log in with:")
        print(f"  Email: {email}")
        print(f"  Password: {new_password}")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        return False


if __name__ == "__main__":
    print("=== Password Reset Tool ===\n")

    # Show available users
    conn = get_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT email, first_name, last_name FROM users")
        users = cursor.fetchall()
        print("Available users:")
        for u in users:
            print(f"  - {u['email']} ({u['first_name']} {u['last_name']})")
        cursor.close()
        conn.close()
        print()

    # Get user input
    email = input("Enter email to reset: ").strip().lower()
    new_password = getpass("Enter NEW password: ")
    confirm = getpass("Confirm NEW password: ")

    if new_password != confirm:
        print("❌ Passwords don't match!")
        sys.exit(1)

    if len(new_password) < 8:
        print("❌ Password must be at least 8 characters")
        sys.exit(1)

    # Reset password
    if reset_password(email, new_password):
        print("\n✓ Done! Try logging in now.")
    else:
        sys.exit(1)
