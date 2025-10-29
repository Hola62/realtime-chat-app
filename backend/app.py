import os

from dotenv import load_dotenv
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_cors import CORS

load_dotenv()  # load .env variables

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev_secret")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "change-me")

# Enable CORS for frontend
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize extensions
jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Register blueprints
try:
    from routes.auth_routes import auth_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
except Exception as e:
    # Avoid hard crash on early boot if routes import fails
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

# Register Socket.IO events
try:
    from sockets.chat_events import register_socket_events

    register_socket_events(socketio)
except Exception as e:
    print("Warning: failed to register socket events:", e)


@app.route("/")
def home():
    return "Realtime Chat App Backend Running!"


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
