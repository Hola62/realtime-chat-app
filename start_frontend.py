"""Simple HTTP server to serve the frontend files."""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

# Configuration
PORT = 8000
DIRECTORY = Path(__file__).parent / "frontend"


class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

    def end_headers(self):
        # Add CORS headers to allow requests to the backend
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()


def main():
    # Change to frontend directory
    os.chdir(DIRECTORY)

    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print("=" * 60)
        print("Frontend Server Started!")
        print("=" * 60)
        print(f"\n📂 Serving files from: {DIRECTORY}")
        print(f"🌐 Server running at: http://localhost:{PORT}")
        print("\n📄 Available pages:")
        print(f"   • Home: http://localhost:{PORT}/index.html")
        print(f"   • Register: http://localhost:{PORT}/register.html")
        print(f"   • Login: http://localhost:{PORT}/login.html")
        print(f"   • Chat: http://localhost:{PORT}/chat.html")
        print("\n⚠️  Make sure the backend is running on http://localhost:5000")
        print("\n🛑 Press Ctrl+C to stop the server")
        print("=" * 60)

        # Open browser automatically
        try:
            webbrowser.open(f"http://localhost:{PORT}/index.html")
            print("\n✓ Browser opened automatically")
        except:
            print("\n✗ Could not open browser automatically")
            print(f"  Please open http://localhost:{PORT}/index.html manually")

        print("\n")
        httpd.serve_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
