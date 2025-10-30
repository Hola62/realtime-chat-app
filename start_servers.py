"""Start both backend and frontend servers."""

import subprocess
import sys
import time
import os
from pathlib import Path


def main():
    print("=" * 60)
    print("Starting Realtime Chat Application")
    print("=" * 60)

    # Get the project root directory
    project_root = Path(__file__).parent

    # Check if virtual environment exists
    venv_python = project_root / ".venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        print("\n✗ Virtual environment not found!")
        print("  Please create it first by running:")
        print("  python -m venv .venv")
        print("  .venv\\Scripts\\Activate.ps1")
        print("  pip install -r requirements.txt")
        sys.exit(1)

    print("\n✓ Virtual environment found")

    # Start backend server
    print("\n🚀 Starting backend server on http://localhost:5000...")
    backend_process = subprocess.Popen(
        [str(venv_python), "backend/app.py"],
        cwd=str(project_root),
        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
    )

    # Wait a bit for backend to start
    time.sleep(2)

    # Start frontend server
    print("🚀 Starting frontend server on http://localhost:8000...")
    frontend_process = subprocess.Popen(
        [str(venv_python), "start_frontend.py"],
        cwd=str(project_root),
        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
    )

    print("\n" + "=" * 60)
    print("✓ Both servers started successfully!")
    print("=" * 60)
    print("\n📡 Backend API: http://localhost:5000")
    print("🌐 Frontend UI: http://localhost:8000")
    print("\n📝 Note: Both servers are running in separate windows")
    print("🛑 Close those windows to stop the servers")
    print("=" * 60)

    try:
        # Keep this script running
        print("\nPress Ctrl+C to stop all servers...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping all servers...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✓ All servers stopped")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
