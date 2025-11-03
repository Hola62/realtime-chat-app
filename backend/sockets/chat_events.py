from flask_socketio import emit, join_room, leave_room, disconnect
from flask import request
from functools import wraps
import jwt
import os
from models.message_model import create_message, get_room_messages, delete_message
from models.room_model import get_room_by_id
from models.user_model import update_user_status, get_user_by_id
from models.private_message_model import (
    create_private_message,
    get_private_messages,
)


def token_required(f):
    """Decorator to require JWT token for Socket.IO events."""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if hasattr(request, "args") and "token" in request.args:
            token = request.args.get("token")

        if not token:
            emit("error", {"message": "Authentication token is missing"})
            disconnect()
            return None

        try:

            secret_key = os.getenv("JWT_SECRET_KEY", "change-me")
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            user_id = payload.get("sub")

            if not user_id:
                emit("error", {"message": "Invalid token payload"})
                disconnect()
                return None

            return f(user_id, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            emit("error", {"message": "Token has expired"})
            disconnect()
            return None
        except jwt.InvalidTokenError:
            emit("error", {"message": "Invalid token"})
            disconnect()
            return None

    return decorated


def register_socket_events(socketio):
    """Register all Socket.IO event handlers."""

    # Store user sessions (sid -> user_id mapping)
    connected_users = {}

    # Store room members (room_id -> set of user_ids)
    room_members = {}

    @socketio.on("connect")
    def handle_connect():
        """Handle client connection."""
        print(f"Client connected: {request.sid}")
        emit(
            "connected",
            {"message": "Successfully connected to chat server", "sid": request.sid},
        )

    @socketio.on("disconnect")
    def handle_disconnect():
        """Handle client disconnection."""
        print(f"Client disconnected: {request.sid}")

        # Update user status to offline if they were logged in
        if request.sid in connected_users:
            user_id = connected_users[request.sid]
            update_user_status(user_id, "offline")
            del connected_users[request.sid]

            # Notify all clients about user going offline
            emit(
                "user_status_changed",
                {"user_id": user_id, "status": "offline"},
                broadcast=True,
            )
            # Also emit specific event for private chats
            emit(
                "user_status_update",
                {"user_id": user_id, "status": "offline"},
                broadcast=True,
            )

    @socketio.on("user_online")
    @token_required
    def handle_user_online(user_id):
        """Handle user coming online after authentication."""
        # Store the session
        connected_users[request.sid] = int(user_id)

        # Update user status to online
        update_user_status(int(user_id), "online")

        # Get user info
        user = get_user_by_id(int(user_id))

        # Notify all clients about user coming online
        emit(
            "user_status_changed",
            {
                "user_id": int(user_id),
                "status": "online",
                "user": (
                    {
                        "id": user["id"],
                        "first_name": user.get("first_name"),
                        "last_name": user.get("last_name"),
                        "avatar_url": user.get("avatar_url"),
                    }
                    if user
                    else None
                ),
            },
            broadcast=True,
        )
        # Also emit specific event for private chats
        emit(
            "user_status_update",
            {"user_id": int(user_id), "status": "online"},
            broadcast=True,
        )

        print(f"User {user_id} is now online")

    @socketio.on("join_room")
    @token_required
    def handle_join_room(user_id, data):
        """Handle user joining a room."""
        room_id = data.get("room_id")

        if not room_id:
            emit("error", {"message": "room_id is required"})
            return

        room = get_room_by_id(room_id)
        if not room:
            emit("error", {"message": "Room not found"})
            return

        print(f"=== User {user_id} joining room {room_id} (SID: {request.sid}) ===")
        join_room(str(room_id))
        print(f"Socket {request.sid} added to room {room_id}")

        # Track member in room
        if room_id not in room_members:
            room_members[room_id] = set()
        room_members[room_id].add(int(user_id))

        # Get member count
        member_count = len(room_members[room_id])

        emit(
            "joined_room",
            {
                "room_id": room_id,
                "room_name": room["name"],
                "message": f'You joined {room["name"]}',
                "member_count": member_count,
            },
        )

        # Notify others in the room about new member and updated count
        emit(
            "user_joined",
            {
                "user_id": user_id,
                "room_id": room_id,
                "message": f"User {user_id} joined the room",
                "member_count": member_count,
            },
            to=str(room_id),
            skip_sid=request.sid,
        )

        print(f"User {user_id} joined room {room_id} (Total members: {member_count})")

    @socketio.on("leave_room")
    @token_required
    def handle_leave_room(user_id, data):
        """Handle user leaving a room."""
        room_id = data.get("room_id")

        if not room_id:
            emit("error", {"message": "room_id is required"})
            return

        print(f"=== User {user_id} leaving room {room_id} (SID: {request.sid}) ===")
        leave_room(str(room_id))
        print(f"Socket {request.sid} removed from room {room_id}")

        # Remove member from room
        if room_id in room_members and int(user_id) in room_members[room_id]:
            room_members[room_id].discard(int(user_id))
            member_count = len(room_members[room_id])
        else:
            member_count = 0

        emit("left_room", {"room_id": room_id, "message": f"You left room {room_id}"})

        # Notify others in the room about member leaving and updated count
        emit(
            "user_left",
            {
                "user_id": user_id,
                "room_id": room_id,
                "message": f"User {user_id} left the room",
                "member_count": member_count,
            },
            to=str(room_id),
        )

        print(f"User {user_id} left room {room_id} (Remaining members: {member_count})")

    @socketio.on("send_message")
    @token_required
    def handle_send_message(user_id, data):
        """Handle sending a message to a room."""
        room_id = data.get("room_id")
        content = data.get("content")

        if not room_id or not content:
            emit("error", {"message": "room_id and content are required"})
            return

        content = content.strip()
        if not content or len(content) > 5000:
            emit(
                "error",
                {"message": "Message content must be between 1 and 5000 characters"},
            )
            return

        print(f"=== User {user_id} sending message to room {room_id} ===")
        message = create_message(room_id, int(user_id), content)

        if not message:
            emit("error", {"message": "Failed to save message"})
            return

        message_data = {
            "id": message["id"],
            "room_id": message["room_id"],
            "user_id": message["user_id"],
            "content": message["content"],
            "timestamp": (
                message["timestamp"].isoformat() if message["timestamp"] else None
            ),
            "user": {
                "first_name": message["first_name"],
                "last_name": message["last_name"],
                "email": message["email"],
                "avatar_url": message.get("avatar_url"),
            },
        }

        # Broadcast to all users in the room (including sender)
        print(f"Broadcasting message {message['id']} to room {room_id}")
        emit("new_message", message_data, to=str(room_id), include_self=True)

        print(f"User {user_id} sent message to room {room_id}")

    @socketio.on("typing")
    @token_required
    def handle_typing(user_id, data):
        """Handle typing indicator."""
        room_id = data.get("room_id")
        is_typing = data.get("is_typing", True)

        if not room_id:
            emit("error", {"message": "room_id is required"})
            return

        emit(
            "user_typing",
            {"user_id": user_id, "room_id": room_id, "is_typing": is_typing},
            to=str(room_id),
            skip_sid=request.sid,
        )

    @socketio.on("get_messages")
    @token_required
    def handle_get_messages(user_id, data):
        """Handle request for message history."""
        room_id = data.get("room_id")
        limit = data.get("limit", 50)

        if not room_id:
            emit("error", {"message": "room_id is required"})
            return

        messages = get_room_messages(room_id, limit)

        formatted_messages = []
        for msg in messages:
            formatted_messages.append(
                {
                    "id": msg["id"],
                    "room_id": msg["room_id"],
                    "user_id": msg["user_id"],
                    "content": msg["content"],
                    "deleted": msg.get("deleted", False),
                    "timestamp": (
                        msg["timestamp"].isoformat() if msg["timestamp"] else None
                    ),
                    "user": {
                        "first_name": msg["first_name"],
                        "last_name": msg["last_name"],
                        "email": msg["email"],
                        "avatar_url": msg.get("avatar_url"),
                    },
                }
            )

        emit("messages_history", {"room_id": room_id, "messages": formatted_messages})

    @socketio.on("delete_message")
    @token_required
    def handle_delete_message(user_id, data):
        """Handle message deletion."""
        message_id = data.get("message_id")
        room_id = data.get("room_id")

        if not message_id or not room_id:
            emit("error", {"message": "message_id and room_id are required"})
            return

        # Delete the message (marks as deleted in database)
        success = delete_message(message_id)

        if success:
            # Notify all users in the room
            emit(
                "message_deleted",
                {"message_id": message_id, "room_id": room_id},
                to=str(room_id),
            )
            print(f"Message {message_id} deleted by user {user_id}")
        else:
            emit("error", {"message": "Failed to delete message"})

    # ===== PRIVATE CHAT HANDLERS =====
    @socketio.on("join_private_chat")
    @token_required
    def handle_join_private_chat(user_id, data):
        """Join a private chat room between two users."""
        room_id = data.get("room_id")  # e.g., "private_1_2"
        other_user_id = data.get("other_user_id")

        if not room_id:
            emit("error", {"message": "room_id is required"})
            return

        print(
            f"=== User {user_id} joining private chat {room_id} (SID: {request.sid}) ==="
        )

        # Join the Socket.IO room
        join_room(room_id)

        # Track this user in the private room
        if room_id not in room_members:
            room_members[room_id] = set()
        room_members[room_id].add(user_id)

        # Confirm to the user
        emit(
            "joined_private_chat", {"room_id": room_id, "other_user_id": other_user_id}
        )

        print(f"User {user_id} joined private chat {room_id}")

    @socketio.on("leave_private_chat")
    @token_required
    def handle_leave_private_chat(user_id, data):
        """Leave a private chat room."""
        room_id = data.get("room_id")

        if not room_id:
            return

        print(f"User {user_id} leaving private chat {room_id}")

        # Leave the Socket.IO room
        leave_room(room_id)

        # Remove from room members
        if room_id in room_members and user_id in room_members[room_id]:
            room_members[room_id].remove(user_id)

    @socketio.on("send_private_message")
    @token_required
    def handle_send_private_message(user_id, data):
        """Send a private message to another user."""
        room_id = data.get("room_id")  # e.g., "private_1_2"
        other_user_id = data.get("other_user_id")
        content = data.get("content")

        if not room_id or not content:
            emit("error", {"message": "room_id and content are required"})
            return

        print(f"Private message from user {user_id} in room {room_id}")

        # Persist the message
        saved = create_private_message(
            room_id, int(user_id), int(other_user_id), content.strip()
        )
        if not saved:
            emit("error", {"message": "Failed to save private message"})
            return

        # Build payload matching frontend expectations
        message_data = {
            "id": saved["id"],
            "room_id": saved["room_key"],
            "user_id": saved["sender_id"],
            "content": saved["content"],
            "deleted": saved.get("deleted", False),
            "timestamp": (
                saved["timestamp"].isoformat() if saved.get("timestamp") else None
            ),
            "user": {
                "first_name": saved.get("first_name", ""),
                "last_name": saved.get("last_name", ""),
                "email": saved.get("email", ""),
                "avatar_url": saved.get("avatar_url"),
            },
        }

        # Broadcast to both users in the private room (including sender)
        emit("private_message", message_data, to=room_id, include_self=True)

        print(f"Private message saved and sent in room {room_id}")

    @socketio.on("get_private_messages")
    @token_required
    def handle_get_private_messages(user_id, data):
        """Get private message history for the given private room."""
        room_id = data.get("room_id")

        if not room_id:
            emit("error", {"message": "room_id is required"})
            return

        msgs = get_private_messages(room_id, data.get("limit", 50))

        formatted = []
        for m in msgs:
            formatted.append(
                {
                    "id": m["id"],
                    "room_id": m["room_key"],
                    "user_id": m["sender_id"],
                    "content": m["content"],
                    "deleted": m.get("deleted", False),
                    "timestamp": (
                        m["timestamp"].isoformat() if m.get("timestamp") else None
                    ),
                    "user": {
                        "first_name": m.get("first_name", ""),
                        "last_name": m.get("last_name", ""),
                        "email": m.get("email", ""),
                        "avatar_url": m.get("avatar_url"),
                    },
                }
            )

        emit("private_messages_history", {"room_id": room_id, "messages": formatted})

    @socketio.on("private_typing")
    @token_required
    def handle_private_typing(user_id, data):
        """Handle typing indicator in private chat."""
        room_id = data.get("room_id")
        other_user_id = data.get("other_user_id")
        is_typing = data.get("is_typing", False)

        if not room_id:
            return

        print(f"Private typing from user {user_id} in room {room_id}: {is_typing}")

        # Broadcast typing status to the other user only
        emit(
            "private_user_typing",
            {"user_id": user_id, "is_typing": is_typing},
            to=room_id,
            skip_sid=request.sid,
        )

    @socketio.on("check_user_status")
    @token_required
    def handle_check_user_status(user_id, data):
        """Check if a user is online or offline."""
        target_user_id = data.get("user_id")

        if not target_user_id:
            emit("error", {"message": "user_id is required"})
            return

        # Check if user is in connected_users
        is_online = any(uid == target_user_id for uid in connected_users.values())

        # Get user from database to check stored status
        target_user = get_user_by_id(target_user_id)
        status = (
            "online"
            if is_online
            else (target_user.get("status", "offline") if target_user else "offline")
        )

        emit("user_status_response", {"user_id": target_user_id, "status": status})

        print(f"User {user_id} checked status of user {target_user_id}: {status}")
