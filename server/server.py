import socket
import sys
import os

# Thêm thư mục shared vào path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client_handler import ClientHandler
from user_manager import UserManager
import config

class ChatServer:
    def __init__(self):
        self.server_socket = None
        self.user_manager = UserManager()
        self.running = True
    
    def start(self):
        """Khởi động server"""
        try:
            # Tạo socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind và listen
            self.server_socket.bind((config.HOST, config.PORT))
            self.server_socket.listen(config.MAX_CLIENTS)
            
            print("="*60)
            print(f"[SERVER STARTED] Listening on {config.HOST}:{config.PORT}")
            print(f"[MAX CLIENTS] {config.MAX_CLIENTS}")
            print(f"[FILE STORAGE] {config.SERVER_STORAGE}")
            print("="*60)
            
            # Tạo thư mục lưu file
            os.makedirs(config.SERVER_STORAGE, exist_ok=True)
            
            # Chấp nhận kết nối
            self.accept_connections()
            
        except Exception as e:
            print(f"[ERROR] Không thể khởi động server: {e}")
        finally:
            self.stop()
    
    def accept_connections(self):
        """Chấp nhận kết nối từ client"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                
                # Tạo thread xử lý client
                handler = ClientHandler(client_socket, address, self.user_manager)
                handler.daemon = True
                handler.start()
                
            except KeyboardInterrupt:
                print("\n[SERVER] Đang tắt server...")
                self.running = False
            except Exception as e:
                if self.running:
                    print(f"[ERROR] Accept connection: {e}")
    
    def stop(self):
        """Dừng server"""
        print("[SERVER] Đang đóng kết nối...")
        if self.server_socket:
            self.server_socket.close()
        print("[SERVER] Đã tắt!")

if __name__ == "__main__":
    server = ChatServer()
    server.start()