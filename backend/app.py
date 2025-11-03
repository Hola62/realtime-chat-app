import os

from dotenv import load_dotenv
from flask import Flask, send_from_directory
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_cors import CORS
from pathlib import Path

# Load .env from project root (parent directory)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev_secret")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "change-me")

# Upload folder configuration
UPLOAD_FOLDER = Path(__file__).parent.parent / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)


CORS(app, resources={r"/*": {"origins": "*"}})


jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*")


try:
    from routes.auth_routes import auth_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
except Exception as e:

    print("Warning: failed to register auth blueprint:", e)

try:
    from routes.health_routes import health_bp

    app.register_blueprint(health_bp)
except Exception as e:
    print("Warning: failed to register health blueprint:", e)

try:
    from routes.chat_routes import chat_bp

    app.register_blueprint(chat_bp, url_prefix="/chat")
except Exception as e:
    print("Warning: failed to register chat blueprint:", e)

try:
    from routes.profile_routes import profile_bp

    app.register_blueprint(profile_bp, url_prefix="/profile")
except Exception as e:
    print("Warning: failed to register profile blueprint:", e)


try:
    from sockets.chat_events import register_socket_events

    register_socket_events(socketio)
except Exception as e:
    print("Warning: failed to register socket events:", e)

# (AI events removed)


@app.route("/")
def home():
    return "Realtime Chat App Backend Running!"


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    """Serve uploaded files (avatars, etc.)."""
    return send_from_directory(str(UPLOAD_FOLDER), filename)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
