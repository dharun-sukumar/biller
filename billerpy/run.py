import uvicorn
import webview
import threading
import multiprocessing
import sys
import socket
import os
from app.main import app
from app.utils import get_data_path

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def start_server(port):
    """Start uvicorn server in a separate thread."""
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    # Identify database path for debugging
    db_path = get_data_path("billerpy.db")
    print(f"\n--- DATABASE PATH: {db_path} ---\n")
    
    # Try default port 8000, then find a free one
    port = 8000
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", port))
        sock.close()
    except Exception:
        port = get_free_port()
        print(f"--- Port 8000 busy, using port: {port} ---")

    # Start server in a separate thread
    server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
    server_thread.start()
    
    # Create a GUI window pointing to the server
    webview.create_window("BluBiller", f"http://127.0.0.1:{port}", width=1200, height=800, resizable=True)
    
    # Start the GUI loop
    webview.start()
    sys.exit()
