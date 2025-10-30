"""Test the /auth/me endpoint to verify it returns correct user data."""

import requests
import json

API_URL = "http://localhost:5000"


def test_auth_me():
    print("Testing /auth/me endpoint...")
    print("-" * 50)

    # First, let's login to get a token
    print("\n1. Logging in...")
    login_data = {
        "email": input("Enter your email: ").strip().lower(),
        "password": input("Enter your password: "),
    }

    try:
        response = requests.post(f"{API_URL}/auth/login", json=login_data)
        print(f"Login status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✓ Login successful!")
            print(f"Token received: {token[:20]}...")
            print(f"User data: {json.dumps(data.get('user'), indent=2)}")

            # Now test /auth/me endpoint
            print("\n2. Testing /auth/me endpoint...")
            me_response = requests.get(
                f"{API_URL}/auth/me", headers={"Authorization": f"Bearer {token}"}
            )

            print(f"/auth/me status: {me_response.status_code}")

            if me_response.status_code == 200:
                me_data = me_response.json()
                print(f"✓ /auth/me successful!")
                print(f"User data from /auth/me:")
                print(json.dumps(me_data, indent=2))

                # Verify required fields
                required_fields = ["id", "email", "first_name", "last_name"]
                missing_fields = [f for f in required_fields if f not in me_data]

                if missing_fields:
                    print(f"\n⚠ WARNING: Missing fields: {missing_fields}")
                    print("This will cause the frontend to fail!")
                else:
                    print(f"\n✓ All required fields present!")
                    print("The authentication should work correctly.")
            else:
                print(f"✗ /auth/me failed!")
                print(f"Response: {me_response.text}")
        else:
            print(f"✗ Login failed!")
            print(f"Response: {response.text}")

    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Cannot connect to server!")
        print("Make sure the Flask server is running on http://localhost:5000")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")


if __name__ == "__main__":
    test_auth_me()
