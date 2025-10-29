# Realtime Chat App

## Overview

- Goal: Build a responsive real-time chat web app where users register, log in, create/join rooms, and exchange instant messages.
- Stack: Flask + Flask-SocketIO (Python), MySQL, JWT auth, HTML/CSS/JS frontend.
- This README focuses on Week 1 deliverables (project setup) and how to run the project locally on Windows.

## Monorepo Structure

- backend/ — Flask app, Socket.IO events, routes, models, DB config
- frontend/ — Static HTML/CSS/JS for chat UI

## Prerequisites

- Python 3.10+ installed
- MySQL 8+ running locally (or a remote MySQL instance)
- Git

## Environment Setup (Windows, PowerShell)

1. Clone repo and create a virtual environment

   - git clone REPO_URL
   - cd realtime-chat-app
   - python -m venv .venv
   - .\.venv\Scripts\Activate.ps1

2. Install dependencies

   - pip install -r requirements.txt

3. Configure environment variables

   - Copy backend/.env.example to backend/.env and fill in values
   - Ensure your MySQL server is reachable and the database exists

4. Initialize the database

   - Create a MySQL database (e.g., realtime_chat)
   - Grant a user with proper permissions
   - The app will connect using the values in backend/.env

5. Run the backend (Flask + Socket.IO)

   - From repo root (venv active):
     - python backend/app.py
   - Default: <http://127.0.0.1:5000>

6. Open the frontend
   - Open frontend/chat.html in a browser
   - Or serve it with any static server; ensure it points to the backend URL

## Week 1 Scope (Project Setup)

- Repository initialized with clear folder structure (backend/, frontend/)
- Python environment and dependencies pinned (requirements.txt)
- MySQL configuration in code with environment variables (backend/config/database.py)
- .env.example committed, .env ignored
- Basic README with setup, run, and Week 1 acceptance criteria

## Week 1 Acceptance Criteria

- I can clone the repo, create a venv, and install dependencies without errors
- I can configure MySQL credentials via backend/.env
- Running python backend/app.py starts the server without crashing
- Database connectivity succeeds (e.g., app doesn’t fail on DB import; simple query path available or will be added in Week 2)
- The frontend files are present and can be opened to later wire Socket.IO

## Next Weeks (High level)

- Week 2: Authentication — Registration, Login, JWT integration (endpoints + guards)
- Week 3: Chat backend — WebSocket events, room and message models, persistence
- Week 4: Frontend chat UI and Socket.IO wiring
- Week 5: Enhancements — typing indicator, presence, message history polish
- Week 6: Testing and deployment — QA, bug fixes, deploy (Render/Railway/VPS)

## Week 2: Authentication API

Base URL: <http://127.0.0.1:5000>

### Backend Endpoints

- POST /auth/register

  - Body (JSON): { "first_name": string, "last_name": string, "email": string, "password": string }
  - 201: { message, user: { id, email, first_name, last_name }, access_token }
  - 400: missing/invalid fields; 409: email exists; 500: create failed
  - Password requirements: min 8 chars, uppercase, lowercase, number
  - Name requirements: first_name and last_name are required (max 100 chars each)

- POST /auth/login

  - Body (JSON): { "email": string, "password": string }
  - 200: { message, user: { id, email, first_name, last_name }, access_token }
  - 400: missing fields; 401: invalid credentials

- GET /auth/me
  - Headers: Authorization: Bearer <access_token>
  - 200: { id }

### Frontend Pages

- **frontend/register.html** — Registration form with validation
- **frontend/login.html** — Login form
- **frontend/inbdex.html** — Landing page (redirects if already logged in)

### How to Test Registration

1. Ensure backend is running: `python backend/app.py`
2. Open `frontend/register.html` in your browser or use a simple HTTP server:
   - `python -m http.server 8000` (navigate to <http://localhost:8000/frontend/register.html>)
3. Fill in the form:
   - First Name: required (e.g., John)
   - Last Name: required (e.g., Doe)
   - Email: valid format (e.g., john.doe@example.com)
   - Password: min 8 chars, uppercase, lowercase, number (e.g., TestPass123)
   - Confirm Password: must match password
4. On success: redirects to chat.html with JWT stored in localStorage

### Notes

- JWT secret is configured via `backend/.env` (JWT_SECRET_KEY).
- MySQL connection vars support either MYSQL\_\* (preferred) or DATABASE\_\* naming.
- CORS is enabled for all origins (restrict in production).

## Troubleshooting

- Activation policy: If you can’t run Activate.ps1, set execution policy in an admin PowerShell:
  - Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
- MySQL connection errors: verify host/port/user/password/DB name in backend/.env; ensure MySQL is running
- Port conflicts: change Flask port via environment or app config

## License

- MIT (or your choice)
