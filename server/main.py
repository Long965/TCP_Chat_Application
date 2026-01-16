"""
Entry point cho Server Application
"""
import sys
import os

# Thêm thư mục gốc vào path để import được common
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.server_core import ChatServer
from common.config import DEFAULT_HOST, DEFAULT_PORT

def main():
    """Khởi chạy server"""
    server = ChatServer(host=DEFAULT_HOST, port=DEFAULT_PORT)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n⏹️  Shutting down server...")
        server.stop()
    except Exception as e:
        print(f"❌ Error: {e}")
        server.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()