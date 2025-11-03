"""Quick diagnostic script to check database and user accounts."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

try:
    from config.database import get_connection

    print("✓ Database module loaded")

    conn = get_connection()
    if not conn:
        print("❌ Could not connect to MySQL")
        print("\nCheck your .env file has correct MySQL credentials:")
        print("  MYSQL_HOST=localhost")
        print("  MYSQL_PORT=3306")
        print("  MYSQL_USER=root")
        print("  MYSQL_PASSWORD=<your-mysql-password>")
        print("  MYSQL_DB=realtime_chat")
        sys.exit(1)

    print("✓ Connected to MySQL database")

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as count FROM users")
    result = cursor.fetchone()
    user_count = result["count"]
    print(f"✓ Found {user_count} users in database")

    if user_count > 0:
        cursor.execute("SELECT id, email, first_name, last_name FROM users LIMIT 5")
        users = cursor.fetchall()
        print("\nRegistered users:")
        for u in users:
            print(
                f"  - {u['email']} ({u['first_name']} {u['last_name']}) [ID: {u['id']}]"
            )
    else:
        print("\n⚠ No users found - you need to register an account first")

    cursor.close()
    conn.close()
    print("\n✓ Database connection is working!")

    if user_count > 0:
        print("\n📝 Login troubleshooting:")
        print("1. Make sure you're typing the EXACT email from the list above")
        print("2. Email is converted to lowercase during login")
        print("3. Check caps lock is OFF when typing password")
        print("4. Password must match exactly what you set during registration")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nPossible issues:")
    print("1. MySQL server is not running - start XAMPP/WAMP")
    print("2. Database 'realtime_chat' does not exist - run setup_database.py")
    print("3. Wrong MySQL password in .env file")
