# Quick Start Guide

## Running the Application

### Option 1: Start Both Servers Together (Recommended)

```powershell
.\.venv\Scripts\Activate.ps1
python start_servers.py
```

This will start both the backend (port 5000) and frontend (port 8000) in separate windows.

### Option 2: Start Servers Separately

**Terminal 1 - Backend:**

```powershell
.\.venv\Scripts\Activate.ps1
python backend/app.py
```

**Terminal 2 - Frontend:**

```powershell
.\.venv\Scripts\Activate.ps1
python start_frontend.py
```

## Accessing the Application

Once both servers are running:

- **Frontend**: http://localhost:8000
- **Backend API**: http://localhost:5000

### Available Pages:

- Home: http://localhost:8000/index.html
- Register: http://localhost:8000/register.html
- Login: http://localhost:8000/login.html
- Chat: http://localhost:8000/chat.html

## Troubleshooting

### Browser Console

Press `F12` to open Developer Tools and check the Console tab for any errors.

### Clear Browser Storage

If you're having authentication issues:

1. Press `F12`
2. Go to **Application** tab
3. Click **Local Storage** → `http://localhost:8000`
4. Click **Clear All**

### Port Already in Use

If you see "Address already in use" error:

- **Backend (port 5000)**: Kill any Python processes or change the port in `backend/app.py`
- **Frontend (port 8000)**: Change PORT in `start_frontend.py`

## Testing Authentication Flow

1. Open http://localhost:8000/register.html
2. Create an account with:
   - First Name
   - Last Name
   - Email
   - Password (min 8 chars, must have uppercase, lowercase, and number)
3. After successful registration, you'll be redirected to the chat page
4. Your name and email should appear in the sidebar

## Database Setup

If database is not set up:

```powershell
.\.venv\Scripts\Activate.ps1
python setup_database.py
```
