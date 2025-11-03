"""Debug login issue - check password hash."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from config.database import get_connection
from werkzeug.security import check_password_hash

email = "holuwahola3@gmail.com"

conn = get_connection()
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT email, password_hash FROM users WHERE email = %s", (email,))
user = cursor.fetchone()

if user:
    print(f"Found user: {user['email']}")
    print(f"Password hash: {user['password_hash'][:50]}...")

    # Test multiple passwords
    test_passwords = ["Password123", "password123", "PASSWORD123"]

    for pwd in test_passwords:
        result = check_password_hash(user["password_hash"], pwd)
        print(f"Testing '{pwd}': {'✅ MATCH' if result else '❌ NO MATCH'}")
else:
    print(f"❌ User not found: {email}")

cursor.close()
conn.close()
