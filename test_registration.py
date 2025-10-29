import requests
import json

BASE_URL = "http://127.0.0.1:5000"

print("=" * 60)
print("Testing Registration Endpoint")
print("=" * 60)

# Test 1: Valid registration
print("\n1. Testing valid registration...")
try:
    r = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": "testuser@example.com",
            "password": "SecurePass123",
        },
    )
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")

# Test 2: Duplicate email
print("\n2. Testing duplicate email...")
try:
    r = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "first_name": "Duplicate",
            "last_name": "User",
            "email": "testuser@example.com",
            "password": "AnotherPass123",
        },
    )
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")

# Test 3: Weak password
print("\n3. Testing weak password...")
try:
    r = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "first_name": "Weak",
            "last_name": "Password",
            "email": "weak@example.com",
            "password": "weak",
        },
    )
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")

# Test 4: Invalid email format
print("\n4. Testing invalid email format...")
try:
    r = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "first_name": "Invalid",
            "last_name": "Email",
            "email": "invalid-email",
            "password": "ValidPass123",
        },
    )
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")

# Test 5: Missing names
print("\n5. Testing missing first/last name...")
try:
    r = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": "noname@example.com", "password": "ValidPass123"},
    )
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")

# Test 6: Missing password
print("\n6. Testing missing password...")
try:
    r = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "first_name": "No",
            "last_name": "Password",
            "email": "nopass@example.com",
        },
    )
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("Registration Tests Complete")
print("=" * 60)
