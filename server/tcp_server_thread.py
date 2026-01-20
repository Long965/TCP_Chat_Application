import threading
import socket
import asyncio
import os
from common.protocol import Protocol, MessageType
from common.config import SERVER_STORAGE_DIR
from server.bridge import global_bridge
from server.handlers.file_handler import FileHandler

class TCPServer(threading.Thread):
    def __init__(self, main_loop): 
        super().__init__()
        self.host = "0.0.0.0"
        self.port = 5555
        self.running = True
        self.server_socket = None
        
        # Lưu event loop của FastAPI để gọi các hàm async
        self.main_loop = main_loop 
        
        # [FIX QUAN TRỌNG] Khai báo đường dẫn lưu file để FileHandler dùng
        self.storage_dir = SERVER_STORAGE_DIR
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Khởi tạo File Handler
        self.file_handler = FileHandler(self)

    def run(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"🚀 TCP Server đang chạy tại port {self.port}")
            
            while self.running:
                try:
                    client_sock, addr = self.server_socket.accept()
                    # Tạo thread riêng cho mỗi client kết nối
                    threading.Thread(target=self.handle_client, args=(client_sock,), daemon=True).start()
                except OSError:
                    break
                    
        except Exception as e:
            print(f"❌ TCP Server Start Error: {e}")

    def handle_client(self, client_socket):
        username = None
        try:
            while True:
                # Nhận tin nhắn từ Client
                msg_type, data = Protocol.recv_message(client_socket)
                
                # Nếu không nhận được gì (client ngắt kết nối) -> Thoát
                if not msg_type: 
                    break 

                # --- 1. XỬ LÝ LOGIN ---
                if msg_type == MessageType.LOGIN:
                    username = data.get("username")
                    
                    # Thêm vào Bridge
                    global_bridge.add_tcp(username, client_socket)
                    
                    # Phản hồi đăng nhập thành công
                    Protocol.send_message(client_socket, MessageType.LOGIN_SUCCESS, {"message": "OK"})
                    
                    # Gửi danh sách user
                    self._update_user_lists()

                # --- 2. XỬ LÝ FILE (Upload/Download) ---
                elif msg_type == MessageType.FILE_UPLOAD:
                    self.file_handler.handle_file_upload(client_socket, username, data)
                
                elif msg_type == MessageType.FILE_DOWNLOAD:
                    self.file_handler.handle_file_download(client_socket, data)

                # --- 3. XỬ LÝ CHUNG (CHAT, VIDEO CALL...) ---
                else:
                    if isinstance(data, dict):
                        data["sender"] = username
                        data["type"] = msg_type
                    
                    # Chuyển qua Bridge (chạy trên Main Thread)
                    self._run_on_main_loop(
                        global_bridge.handle_message(data, sender=username)
                    )

        except (ConnectionResetError, ConnectionAbortedError):
            print(f"🔌 Client {username} ngắt kết nối đột ngột.")
        except Exception as e:
            print(f"❌ Error handling TCP client {username}: {e}")
        finally:
            # Dọn dẹp khi ngắt kết nối
            if username:
                # Kiểm tra socket chính chủ trước khi xóa
                if global_bridge.tcp_clients.get(username) == client_socket:
                    global_bridge.remove_tcp(username)
                    self._update_user_lists()
            
            try: client_socket.close()
            except: pass

    def _update_user_lists(self):
        """Cập nhật danh sách online cho tất cả mọi người"""
        users = list(global_bridge.tcp_clients.keys()) + list(global_bridge.web_clients.keys())
        
        # 1. Gửi cho Web Clients
        self._run_on_main_loop(global_bridge.broadcast({"type": "SYSTEM", "users": users}))
        
        # 2. Gửi cho TCP Clients
        msg_data = {"users": users}
        for sock in global_bridge.tcp_clients.values():
            try: 
                Protocol.send_message(sock, MessageType.LIST_USERS, msg_data)
            except: pass

    def _run_on_main_loop(self, coro):
        """Helper để chạy Coroutine trên Main Thread"""
        if self.main_loop and self.main_loop.is_running():
            asyncio.run_coroutine_threadsafe(coro, self.main_loop)