from flask_socketio import emit, join_room, leave_room, disconnect
from flask import request
from functools import wraps
import jwt
import os
from models.message_model import create_message, get_room_messages
from models.room_model import get_room_by_id


def token_required(f):
    """Decorator to require JWT token for Socket.IO events."""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get token from Socket.IO auth or query params
        if hasattr(request, "args") and "token" in request.args:
            token = request.args.get("token")

        if not token:
            emit("error", {"message": "Authentication token is missing"})
            disconnect()
            return None

        try:
            # Decode JWT token
            secret_key = os.getenv("JWT_SECRET_KEY", "change-me")
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            user_id = payload.get("sub")  # Flask-JWT-Extended uses 'sub' for identity

            if not user_id:
                emit("error", {"message": "Invalid token payload"})
                disconnect()
                return None

            # Pass user_id to the decorated function
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

    @socketio.on("join_room")
    @token_required
    def handle_join_room(user_id, data):
        """Handle user joining a room."""
        room_id = data.get("room_id")

        if not room_id:
            emit("error", {"message": "room_id is required"})
            return

        # Verify room exists
        room = get_room_by_id(room_id)
        if not room:
            emit("error", {"message": "Room not found"})
            return

        # Join the room
        join_room(str(room_id))

        # Notify user
        emit(
            "joined_room",
            {
                "room_id": room_id,
                "room_name": room["name"],
                "message": f'You joined {room["name"]}',
            },
        )

        # Notify others in the room
        emit(
            "user_joined",
            {
                "user_id": user_id,
                "room_id": room_id,
                "message": f"User {user_id} joined the room",
            },
            room=str(room_id),
            skip_sid=request.sid,
        )

        print(f"User {user_id} joined room {room_id}")

    @socketio.on("leave_room")
    @token_required
    def handle_leave_room(user_id, data):
        """Handle user leaving a room."""
        room_id = data.get("room_id")

        if not room_id:
            emit("error", {"message": "room_id is required"})
            return

        # Leave the room
        leave_room(str(room_id))

        # Notify user
        emit("left_room", {"room_id": room_id, "message": f"You left room {room_id}"})

        # Notify others in the room
        emit(
            "user_left",
            {
                "user_id": user_id,
                "room_id": room_id,
                "message": f"User {user_id} left the room",
            },
            room=str(room_id),
        )

        print(f"User {user_id} left room {room_id}")

    @socketio.on("send_message")
    @token_required
    def handle_send_message(user_id, data):
        """Handle sending a message to a room."""
        room_id = data.get("room_id")
        content = data.get("content")

        if not room_id or not content:
            emit("error", {"message": "room_id and content are required"})
            return

        # Validate content length
        content = content.strip()
        if not content or len(content) > 5000:
            emit(
                "error",
                {"message": "Message content must be between 1 and 5000 characters"},
            )
            return

        # Save message to database
        message = create_message(room_id, int(user_id), content)

        if not message:
            emit("error", {"message": "Failed to save message"})
            return

        # Prepare message data for broadcasting
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
            },
        }

        # Broadcast to all users in the room (including sender)
        emit("new_message", message_data, room=str(room_id))

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

        # Broadcast typing status to others in the room
        emit(
            "user_typing",
            {"user_id": user_id, "room_id": room_id, "is_typing": is_typing},
            room=str(room_id),
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

        # Fetch messages from database
        messages = get_room_messages(room_id, limit)

        # Format messages for client
        formatted_messages = []
        for msg in messages:
            formatted_messages.append(
                {
                    "id": msg["id"],
                    "room_id": msg["room_id"],
                    "user_id": msg["user_id"],
                    "content": msg["content"],
                    "timestamp": (
                        msg["timestamp"].isoformat() if msg["timestamp"] else None
                    ),
                    "user": {
                        "first_name": msg["first_name"],
                        "last_name": msg["last_name"],
                        "email": msg["email"],
                    },
                }
            )

        emit("messages_history", {"room_id": room_id, "messages": formatted_messages})
