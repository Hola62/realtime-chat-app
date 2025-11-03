"""Test login exactly as frontend does."""

import requests
import json

url = "http://localhost:5000/auth/login"
payload = {"email": "holuwahola3@gmail.com", "password": "Password123"}

print(f"Sending POST to {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")

response = requests.post(url, json=payload)

print(f"\nResponse status: {response.status_code}")
print(f"Response body: {response.text}")

if response.ok:
    data = response.json()
    print(f"\n✅ Login successful!")
    print(f"Token: {data.get('access_token', 'N/A')[:50]}...")
else:
    print(f"\n❌ Login failed")
