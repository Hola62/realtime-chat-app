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
            "email": "testuser@example.com",
            "password": "SecurePass123",
            "display_name": "Test User",
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
            "email": "testuser@example.com",
            "password": "AnotherPass123",
            "display_name": "Duplicate User",
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
            "email": "weak@example.com",
            "password": "weak",
            "display_name": "Weak Password User",
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
            "email": "invalid-email",
            "password": "ValidPass123",
            "display_name": "Invalid Email User",
        },
    )
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")

# Test 5: Missing fields
print("\n5. Testing missing required fields...")
try:
    r = requests.post(f"{BASE_URL}/auth/register", json={"email": "nopass@example.com"})
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("Registration Tests Complete")
print("=" * 60)
