from flask import Flask
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os

load_dotenv()  # load .env variables

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_secret')

socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def home():
    return "Realtime Chat App Backend Running!"

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
