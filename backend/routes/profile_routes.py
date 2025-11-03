"""Profile management routes."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
from pathlib import Path

from models.user_model import (
    get_user_by_id,
    update_user_profile,
    update_user_avatar,
    search_users_by_name,
)

profile_bp = Blueprint("profile", __name__)

# Configuration for file uploads
UPLOAD_FOLDER = Path(__file__).parent.parent.parent / "uploads" / "avatars"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Create upload folder if it doesn't exist
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@profile_bp.route("/me", methods=["GET"])
@jwt_required()
def get_profile():
    """Get current user's profile."""
    user_id = get_jwt_identity()
    user = get_user_by_id(int(user_id))

    if not user:
        return jsonify({"message": "user not found"}), 404

    return (
        jsonify(
            {
                "id": user["id"],
                "email": user["email"],
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name"),
                "avatar_url": user.get("avatar_url"),
                "status": user.get("status"),
                "created_at": (
                    user["created_at"].isoformat() if user.get("created_at") else None
                ),
            }
        ),
        200,
    )


@profile_bp.route("/me", methods=["PUT"])
@jwt_required()
def update_profile():
    """Update current user's profile."""
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    first_name = data.get("first_name", "").strip() if data.get("first_name") else None
    last_name = data.get("last_name", "").strip() if data.get("last_name") else None

    # Validate if provided
    if first_name is not None and (not first_name or len(first_name) > 100):
        return (
            jsonify({"message": "first name must be between 1 and 100 characters"}),
            400,
        )

    if last_name is not None and (not last_name or len(last_name) > 100):
        return (
            jsonify({"message": "last name must be between 1 and 100 characters"}),
            400,
        )

    # Update profile
    success = update_user_profile(
        int(user_id), first_name=first_name, last_name=last_name
    )

    if not success:
        return jsonify({"message": "failed to update profile"}), 500

    # Get updated user data
    user = get_user_by_id(int(user_id))

    return (
        jsonify(
            {
                "message": "profile updated successfully",
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "first_name": user.get("first_name"),
                    "last_name": user.get("last_name"),
                    "avatar_url": user.get("avatar_url"),
                    "status": user.get("status"),
                },
            }
        ),
        200,
    )


@profile_bp.route("/me/avatar", methods=["POST"])
@jwt_required()
def upload_avatar():
    """Upload avatar image."""
    user_id = get_jwt_identity()

    # Check if file is in request
    if "avatar" not in request.files:
        return jsonify({"message": "no file provided"}), 400

    file = request.files["avatar"]

    # Check if file was selected
    if file.filename == "":
        return jsonify({"message": "no file selected"}), 400

    # Check file size (this is a basic check, might not work in all cases)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_FILE_SIZE:
        return jsonify({"message": "file size exceeds 5MB limit"}), 400

    # Check if file type is allowed
    if not allowed_file(file.filename):
        return (
            jsonify(
                {
                    "message": f"file type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
                }
            ),
            400,
        )

    # Create secure filename
    filename = secure_filename(file.filename)
    # Add user ID to filename to avoid conflicts
    name, ext = os.path.splitext(filename)
    filename = f"user_{user_id}_{name}{ext}"

    # Save file
    filepath = UPLOAD_FOLDER / filename
    try:
        file.save(str(filepath))
    except Exception as e:
        print(f"Error saving file: {e}")
        return jsonify({"message": "failed to save file"}), 500

    # Update user avatar URL
    avatar_url = f"/uploads/avatars/{filename}"
    success = update_user_avatar(int(user_id), avatar_url)

    if not success:
        # Delete uploaded file if database update fails
        try:
            filepath.unlink()
        except:
            pass
        return jsonify({"message": "failed to update avatar"}), 500

    return (
        jsonify({"message": "avatar uploaded successfully", "avatar_url": avatar_url}),
        200,
    )


@profile_bp.route("/users/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user_profile(user_id):
    """Get another user's public profile."""
    user = get_user_by_id(user_id)

    if not user:
        return jsonify({"message": "user not found"}), 404

    # Return only public information
    return (
        jsonify(
            {
                "id": user["id"],
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name"),
                "avatar_url": user.get("avatar_url"),
                "status": user.get("status"),
            }
        ),
        200,
    )


@profile_bp.route("/search_users", methods=["GET"])
@jwt_required()
def search_users():
    """Search users by name (for private chat)."""
    user_id = get_jwt_identity()
    name = request.args.get("name", "").strip()
    if not name or len(name) < 2:
        return jsonify({"users": []})

    users = search_users_by_name(name, exclude_user_id=int(user_id))
    return jsonify({"users": users})
