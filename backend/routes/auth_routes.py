from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from models.user_model import init_user_table, get_user_by_email, create_user


auth_bp = Blueprint("auth", __name__)


@auth_bp.before_app_first_request
def _ensure_tables():
    # Create users table on first request to avoid failing imports when DB is not available
    init_user_table()


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    display_name = data.get("display_name") or None

    if not email or not password:
        return jsonify({"message": "email and password are required"}), 400

    if get_user_by_email(email):
        return jsonify({"message": "email already registered"}), 409

    password_hash = generate_password_hash(password)
    user_id = create_user(email, password_hash, display_name)
    if not user_id:
        return jsonify({"message": "could not create user"}), 500

    token = create_access_token(identity=str(user_id))
    return (
        jsonify(
            {
                "message": "registered",
                "user": {"id": user_id, "email": email, "display_name": display_name},
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
        "display_name": user.get("display_name"),
    }
    return (
        jsonify({"message": "logged_in", "user": profile, "access_token": token}),
        200,
    )


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    return jsonify({"id": user_id}), 200
