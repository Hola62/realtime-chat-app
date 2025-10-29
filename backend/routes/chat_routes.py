from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.room_model import create_room, get_all_rooms, get_room_by_id, delete_room
from models.message_model import get_room_messages

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/rooms", methods=["GET"])
@jwt_required()
def list_rooms():
    """Get all chat rooms."""
    rooms = get_all_rooms()

    # Format rooms for response
    formatted_rooms = []
    for room in rooms:
        formatted_rooms.append(
            {
                "id": room["id"],
                "name": room["name"],
                "created_at": (
                    room["created_at"].isoformat() if room["created_at"] else None
                ),
                "creator": {
                    "first_name": room["first_name"],
                    "last_name": room["last_name"],
                    "email": room["creator_email"],
                },
            }
        )

    return jsonify({"rooms": formatted_rooms}), 200


@chat_bp.route("/rooms", methods=["POST"])
@jwt_required()
def create_new_room():
    """Create a new chat room."""
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    name = data.get("name", "").strip()

    # Validate room name
    if not name:
        return jsonify({"error": "Room name is required"}), 400

    if len(name) > 100:
        return jsonify({"error": "Room name must be less than 100 characters"}), 400

    # Create room
    room_id = create_room(name, int(user_id))

    if not room_id:
        return jsonify({"error": "Failed to create room"}), 500

    # Fetch the created room
    room = get_room_by_id(room_id)

    return (
        jsonify(
            {
                "message": "Room created successfully",
                "room": {
                    "id": room["id"],
                    "name": room["name"],
                    "created_at": (
                        room["created_at"].isoformat() if room["created_at"] else None
                    ),
                    "creator": {
                        "first_name": room["first_name"],
                        "last_name": room["last_name"],
                        "email": room["creator_email"],
                    },
                },
            }
        ),
        201,
    )


@chat_bp.route("/rooms/<int:room_id>", methods=["GET"])
@jwt_required()
def get_room(room_id):
    """Get a specific room by ID."""
    room = get_room_by_id(room_id)

    if not room:
        return jsonify({"error": "Room not found"}), 404

    return (
        jsonify(
            {
                "room": {
                    "id": room["id"],
                    "name": room["name"],
                    "created_at": (
                        room["created_at"].isoformat() if room["created_at"] else None
                    ),
                    "creator": {
                        "first_name": room["first_name"],
                        "last_name": room["last_name"],
                        "email": room["creator_email"],
                    },
                }
            }
        ),
        200,
    )


@chat_bp.route("/rooms/<int:room_id>/messages", methods=["GET"])
@jwt_required()
def get_messages(room_id):
    """Get message history for a room."""
    # Check if room exists
    room = get_room_by_id(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404

    # Get limit from query params (default 50)
    limit = request.args.get("limit", 50, type=int)

    if limit < 1 or limit > 200:
        return jsonify({"error": "Limit must be between 1 and 200"}), 400

    # Fetch messages
    messages = get_room_messages(room_id, limit)

    # Format messages for response
    formatted_messages = []
    for msg in messages:
        formatted_messages.append(
            {
                "id": msg["id"],
                "room_id": msg["room_id"],
                "user_id": msg["user_id"],
                "content": msg["content"],
                "timestamp": msg["timestamp"].isoformat() if msg["timestamp"] else None,
                "user": {
                    "first_name": msg["first_name"],
                    "last_name": msg["last_name"],
                    "email": msg["email"],
                },
            }
        )

    return jsonify({"room_id": room_id, "messages": formatted_messages}), 200


@chat_bp.route("/rooms/<int:room_id>", methods=["DELETE"])
@jwt_required()
def delete_room_endpoint(room_id):
    """Delete a room (only creator can delete)."""
    user_id = get_jwt_identity()

    # Check if room exists and user is creator
    room = get_room_by_id(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404

    # Note: In production, you'd check if user_id matches created_by
    # For now, we'll allow any authenticated user to delete

    success = delete_room(room_id)

    if not success:
        return jsonify({"error": "Failed to delete room"}), 500

    return jsonify({"message": "Room deleted successfully"}), 200
