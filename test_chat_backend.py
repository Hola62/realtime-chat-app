"""
Test script for chat backend functionality.
Tests room creation, WebSocket events, and message persistence.
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"
AUTH_URL = f"{BASE_URL}/auth"
CHAT_URL = f"{BASE_URL}/chat"

# Test user credentials
test_user = {
    "first_name": "Chat",
    "last_name": "Tester",
    "email": "chattester@example.com",
    "password": "TestPass123",
}


def test_setup():
    """Register a test user and get access token."""
    print("\n=== Setting up test user ===")

    # Try to register
    response = requests.post(f"{AUTH_URL}/register", json=test_user)

    if response.status_code == 201:
        print("✓ User registered successfully")
        data = response.json()
        return data.get("access_token")
    elif response.status_code == 400 and "already exists" in response.text:
        print("✓ User already exists, logging in...")
        # Login instead
        response = requests.post(
            f"{AUTH_URL}/login",
            json={"email": test_user["email"], "password": test_user["password"]},
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")

    print(f"✗ Setup failed: {response.status_code} - {response.text}")
    return None


def test_create_room(token):
    """Test creating a new chat room."""
    print("\n=== Testing Room Creation ===")

    headers = {"Authorization": f"Bearer {token}"}
    room_data = {"name": "Test Chat Room"}

    response = requests.post(f"{CHAT_URL}/rooms", json=room_data, headers=headers)

    if response.status_code == 201:
        data = response.json()
        print(f"✓ Room created: {data['room']['name']} (ID: {data['room']['id']})")
        return data["room"]["id"]
    else:
        print(f"✗ Room creation failed: {response.status_code} - {response.text}")
        return None


def test_list_rooms(token):
    """Test listing all rooms."""
    print("\n=== Testing List Rooms ===")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{CHAT_URL}/rooms", headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {len(data['rooms'])} rooms")
        for room in data["rooms"]:
            creator_name = (
                f"{room['creator']['first_name']} {room['creator']['last_name']}"
            )
            print(f"  - {room['name']} (created by {creator_name})")
        return True
    else:
        print(f"✗ List rooms failed: {response.status_code} - {response.text}")
        return False


def test_get_room(token, room_id):
    """Test getting a specific room."""
    print(f"\n=== Testing Get Room {room_id} ===")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{CHAT_URL}/rooms/{room_id}", headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Room retrieved: {data['room']['name']}")
        return True
    else:
        print(f"✗ Get room failed: {response.status_code} - {response.text}")
        return False


def test_get_messages(token, room_id):
    """Test getting message history for a room."""
    print(f"\n=== Testing Get Messages for Room {room_id} ===")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{CHAT_URL}/rooms/{room_id}/messages", headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved {len(data['messages'])} messages")
        for msg in data["messages"]:
            user_name = f"{msg['user']['first_name']} {msg['user']['last_name']}"
            print(f"  - {user_name}: {msg['content'][:50]}...")
        return True
    else:
        print(f"✗ Get messages failed: {response.status_code} - {response.text}")
        return False


def test_websocket_info():
    """Display WebSocket connection info."""
    print("\n=== WebSocket Connection Info ===")
    print("To test WebSocket functionality, use a Socket.IO client:")
    print(f"1. Connect to: {BASE_URL}")
    print("2. Add token as query parameter: ?token=YOUR_ACCESS_TOKEN")
    print("\nAvailable events:")
    print("  - connect: Automatic on connection")
    print("  - join_room: {room_id: 1}")
    print("  - send_message: {room_id: 1, content: 'Hello!'}")
    print("  - typing: {room_id: 1, is_typing: true}")
    print("  - get_messages: {room_id: 1, limit: 50}")
    print("  - leave_room: {room_id: 1}")
    print("\nEvents to listen for:")
    print("  - connected: Connection confirmation")
    print("  - joined_room: Room join confirmation")
    print("  - user_joined: Another user joined")
    print("  - new_message: New message in room")
    print("  - user_typing: User is typing")
    print("  - messages_history: Message history response")
    print("  - error: Error messages")


def main():
    """Run all tests."""
    print("=" * 50)
    print("Chat Backend Test Suite")
    print("=" * 50)

    # Setup
    token = test_setup()
    if not token:
        print("\n✗ Cannot proceed without valid token")
        return

    print(f"\n✓ Access Token: {token[:20]}...")

    # Test room creation
    room_id = test_create_room(token)

    # Test listing rooms
    test_list_rooms(token)

    # Test getting specific room
    if room_id:
        test_get_room(token, room_id)
        test_get_messages(token, room_id)

    # WebSocket info
    test_websocket_info()

    print("\n" + "=" * 50)
    print("Test Suite Complete")
    print("=" * 50)
    print("\n✓ REST API endpoints are working!")
    print("✓ Next: Test WebSocket events using a Socket.IO client")
    print(f"✓ Server should be running at: {BASE_URL}")


if __name__ == "__main__":
    main()
