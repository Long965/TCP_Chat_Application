"""
Core logic cho Chat Server
"""
import socket
import threading
import os

from common.config import SERVER_STORAGE_DIR
from common.protocol import Protocol, MessageType
from server.handlers.client_handler import ClientHandler

class ChatServer:
    def __init__(self, host="0.0.0.0", port=5555):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = {}  # {username: socket}
        self.client_threads = []
        self.running = False
        
        # Tạo thư mục lưu file
        self.storage_dir = SERVER_STORAGE_DIR
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def start(self):
        """Khởi động server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            
            self.running = True
            
            print("=" * 60)
            print(f"🚀 SERVER STARTED")
            print(f"📍 Address: {self.host}:{self.port}")
            print(f"📁 Storage: {self.storage_dir}")
            print("=" * 60)
            
            self.accept_connections()
            
        except Exception as e:
            print(f"❌ Error starting server: {e}")
    
    def accept_connections(self):
        """Chấp nhận kết nối từ client"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"📞 New connection from {address}")
                
                # Tạo handler cho client
                handler = ClientHandler(self, client_socket, address)
                
                # Tạo thread xử lý client
                thread = threading.Thread(
                    target=handler.handle,
                    daemon=True
                )
                thread.start()
                self.client_threads.append(thread)
                
            except KeyboardInterrupt:
                print("\n⏹️  Shutting down server...")
                self.running = False
                break
            except Exception as e:
                if self.running:
                    print(f"❌ Error accepting connection: {e}")
    
    def broadcast(self, msg_type, data, exclude=None):
        """Broadcast message tới tất cả client"""
        disconnected = []
        
        for username, sock in self.clients.items():
            if username == exclude:
                continue
            
            try:
                Protocol.send_message(sock, msg_type, data)
            except:
                disconnected.append(username)
        
        # Xóa client bị disconnect
        for username in disconnected:
            if username in self.clients:
                del self.clients[username]
    
    def send_user_list(self):
        """Gửi danh sách user tới tất cả client"""
        user_list = list(self.clients.keys())
        self.broadcast(
            MessageType.USER_LIST,
            {"users": user_list}
        )
    
    def stop(self):
        """Dừng server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("🛑 Server stopped")