"""Quick password reset - sets password to Password123."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from config.database import get_connection
from werkzeug.security import generate_password_hash, check_password_hash

email = "holuwahola3@gmail.com"
new_password = "Password123"

conn = get_connection()
if not conn:
    print("❌ Could not connect to database")
    sys.exit(1)

cursor = conn.cursor(dictionary=True)

# Check current password
cursor.execute("SELECT password_hash FROM users WHERE email = %s", (email,))
current = cursor.fetchone()
if current:
    print(
        f"Before update - Testing '{new_password}': {check_password_hash(current['password_hash'], new_password)}"
    )

# Update password
password_hash = generate_password_hash(new_password)
cursor.execute(
    "UPDATE users SET password_hash = %s WHERE email = %s", (password_hash, email)
)
affected = cursor.rowcount
conn.commit()
print(f"Rows affected: {affected}")

# Verify it worked
cursor.execute("SELECT password_hash FROM users WHERE email = %s", (email,))
verify = cursor.fetchone()
if verify:
    test_result = check_password_hash(verify["password_hash"], new_password)
    print(f"After update - Testing '{new_password}': {test_result}")

    if test_result:
        print(f"\n✅ Password reset successful!")
        print(f"\nLogin credentials:")
        print(f"Email: {email}")
        print(f"Password: {new_password}")
        print(f"\nGo to http://localhost:8000 and log in now!")
    else:
        print("\n❌ ERROR: Password not updated correctly!")
else:
    print("\n❌ ERROR: User not found!")

cursor.close()
conn.close()
