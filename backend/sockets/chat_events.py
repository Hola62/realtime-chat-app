from flask_socketio import emit, join_room, leave_room, disconnect
from flask import request
from functools import wraps
import jwt
import os
from models.message_model import create_message, get_room_messages, delete_message
from models.room_model import get_room_by_id
from models.user_model import update_user_status, get_user_by_id


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
