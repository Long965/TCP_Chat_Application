"""
Entry point cho Client Application
"""
import sys
import os

# Thêm thư mục gốc vào path để import được common
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from client.client_core import ChatClient

def main():
    """Khởi chạy ứng dụng client"""
    try:
        client = ChatClient()
    except KeyboardInterrupt:
        print("\n⏹️  Client stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()