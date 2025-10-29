"""
Database setup script - Creates the database if it doesn't exist.
Run this before starting the Flask application for the first time.
"""

import mysql.connector
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
backend_dir = Path(__file__).parent / "backend"
env_path = backend_dir / ".env"
load_dotenv(dotenv_path=env_path)


def setup_database():
    """Create the database if it doesn't exist."""

    # Get database credentials from environment
    host = os.getenv("DATABASE_HOST") or os.getenv("MYSQL_HOST", "127.0.0.1")
    port = int(os.getenv("DATABASE_PORT") or os.getenv("MYSQL_PORT", "3306"))
    user = os.getenv("DATABASE_USER") or os.getenv("MYSQL_USER", "root")
    password = os.getenv("DATABASE_PASSWORD") or os.getenv("MYSQL_PASSWORD", "")
    database_name = os.getenv("DATABASE_NAME") or os.getenv("MYSQL_DB", "realtime_chat")

    print(f"Connecting to MySQL server at {host}:{port} as user '{user}'...")

    try:
        # Connect to MySQL server (without specifying database)
        conn = mysql.connector.connect(
            host=host, port=port, user=user, password=password
        )

        cursor = conn.cursor()

        # Create database if it doesn't exist
        print(f"Creating database '{database_name}' if it doesn't exist...")
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )

        print(f"✓ Database '{database_name}' is ready!")

        cursor.close()
        conn.close()

        print("\nDatabase setup complete!")
        print(f"You can now start the Flask server: python backend/app.py")

    except mysql.connector.Error as err:
        print(f"\n✗ Error setting up database: {err}")
        print("\nPlease check:")
        print(f"  1. MySQL server is running")
        print(f"  2. User '{user}' has permission to create databases")
        print(f"  3. Password in backend/.env is correct")
        print(f"  4. MySQL is accessible at {host}:{port}")
        return False

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Realtime Chat App - Database Setup")
    print("=" * 60)
    print()

    success = setup_database()

    if success:
        print("\n✓ All done! Start your server with:")
        print("  .venv\\Scripts\\python.exe backend\\app.py")
    else:
        print("\n✗ Setup failed. Please fix the errors above and try again.")
