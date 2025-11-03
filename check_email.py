"""Check exact email format in database."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from config.database import get_connection

conn = get_connection()
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT id, email, CHAR_LENGTH(email) as len FROM users WHERE id = 3")
user = cursor.fetchone()

if user:
    print(f"Email from DB: '{user['email']}'")
    print(f"Length: {user['len']} characters")
    print(f"Bytes: {user['email'].encode('utf-8')}")

    # Check for hidden characters
    for i, char in enumerate(user["email"]):
        print(f"  [{i}] = '{char}' (ASCII {ord(char)})")
else:
    print("User not found")

cursor.close()
conn.close()
