import re
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from models.user_model import init_user_table, get_user_by_email, create_user


auth_bp = Blueprint("auth", __name__)


try:
    init_user_table()
except Exception as e:
    print(f"Warning: Could not initialize users table on import: {e}")


def validate_email(email: str) -> bool:
    """Basic email format validation."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength.

    Returns: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return False, "password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return False, "password must contain at least one number"
    return True, ""


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()

    if not email or not password:
        return jsonify({"message": "email and password are required"}), 400

    if not first_name or not last_name:
        return jsonify({"message": "first name and last name are required"}), 400

    if not validate_email(email):
        return jsonify({"message": "invalid email format"}), 400

    is_valid, error_msg = validate_password(password)
    if not is_valid:
        return jsonify({"message": error_msg}), 400

    if len(first_name) > 100:
        return jsonify({"message": "first name too long (max 100 characters)"}), 400

    if len(last_name) > 100:
        return jsonify({"message": "last name too long (max 100 characters)"}), 400

    if get_user_by_email(email):
        return jsonify({"message": "email already registered"}), 409

    password_hash = generate_password_hash(password)
    user_id = create_user(email, password_hash, first_name, last_name)
    if not user_id:
        return jsonify({"message": "could not create user"}), 500

    token = create_access_token(identity=str(user_id))
    return (
        jsonify(
            {
                "message": "registered successfully",
                "user": {
                    "id": user_id,
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                },
                "access_token": token,
            }
        ),
        201,
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"message": "email and password are required"}), 400

    user = get_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"message": "invalid email or password"}), 401

    token = create_access_token(identity=str(user["id"]))
    profile = {
        "id": user["id"],
        "email": user["email"],
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
    }
    return (
        jsonify({"message": "logged_in", "user": profile, "access_token": token}),
        200,
    )


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    # Get full user info from database
    from models.user_model import get_user_by_id

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
            }
        ),
        200,
    )
