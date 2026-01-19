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
        self.storage_dir = SERVER_STORAGE_DIR
        os.makedirs(self.storage_dir, exist_ok=True)
        self.main_loop = main_loop 

    def run(self):
        HOST = "0.0.0.0"
        PORT = 5555
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((HOST, PORT))
            sock.listen(5)
            print(f"🚀 TCP Server đang chạy tại port {PORT}")
            
            while True:
                client, addr = sock.accept()
                threading.Thread(target=self.handle_client, args=(client,), daemon=True).start()
        except Exception as e:
            print(f"❌ TCP Server Error: {e}")

    def handle_client(self, client):
        username = None
        file_handler = FileHandler(self)

        try:
            while True:
                msg_type, data = Protocol.recv_message(client)
                if not msg_type: break 

                # --- 1. LOGIN ---
                if msg_type == MessageType.LOGIN:
                    username = data.get("username")
                    
                    # === SỬA ĐOẠN NÀY: KHÔNG CHẶN NỮA MÀ CHO PHÉP GHI ĐÈ ===
                    # Bridge sẽ tự động đóng socket cũ nếu trùng tên
                    global_bridge.add_tcp(username, client)
                    
                    # Phản hồi thành công
                    Protocol.send_message(client, MessageType.LOGIN_SUCCESS, {"message": "OK"})
                    self._update_user_lists()

                # --- 2. TEXT CHAT ---
                elif msg_type == MessageType.TEXT:
                    msg = {
                        "type": "TEXT",
                        "content": data.get("message"),
                        "sender": username,
                        "recipient": data.get("recipient"),
                        "timestamp": data.get("timestamp")
                    }
                    self._run_on_main_loop(global_bridge.handle_message(msg, sender=username))
                
                # --- 3. FILE & CALL (Giữ nguyên) ---
                elif msg_type == MessageType.FILE_UPLOAD:
                    file_handler.handle_file_upload(client, username, data)
                elif msg_type == MessageType.FILE_DOWNLOAD:
                    file_handler.handle_file_download(client, data)
                elif msg_type == MessageType.CALL_REQUEST:
                    recipient = data.get("recipient")
                    if recipient in global_bridge.tcp_clients:
                         Protocol.send_message(global_bridge.tcp_clients[recipient], MessageType.CALL_REQUEST, data)
                elif msg_type == MessageType.CALL_ACCEPT:
                     target = data.get("recipient")
                     if target in global_bridge.tcp_clients:
                         Protocol.send_message(global_bridge.tcp_clients[target], MessageType.CALL_ACCEPT, data)
                elif msg_type == MessageType.VIDEO_DATA or msg_type == MessageType.AUDIO_DATA:
                    recipient = data.get("recipient")
                    if recipient and recipient in global_bridge.tcp_clients:
                        Protocol.send_message(global_bridge.tcp_clients[recipient], msg_type, data)

        except Exception as e:
            # Lỗi này thường xảy ra khi socket cũ bị close() do user mới đăng nhập
            # Đây là điều bình thường, không cần in ra nếu không muốn spam log
            pass 
        finally:
            # Chỉ remove nếu socket hiện tại vẫn đang là socket chính chủ của user đó
            # (Tránh trường hợp user mới vừa vào, thread cũ này chạy finally và xóa luôn user mới)
            if username and global_bridge.tcp_clients.get(username) == client:
                global_bridge.remove_user(username)
                self._update_user_lists()
            
            try: client.close()
            except: pass

    def _update_user_lists(self):
        users = list(global_bridge.tcp_clients.keys()) + list(global_bridge.web_clients.keys())
        msg_data = {"users": users}
        for sock in global_bridge.tcp_clients.values():
            try: Protocol.send_message(sock, MessageType.LIST_USERS, msg_data)
            except: pass
        self._run_on_main_loop(global_bridge.broadcast({"type": "SYSTEM", "users": users}))

    def broadcast(self, msg_type, data, exclude=None):
        for user, sock in global_bridge.tcp_clients.items():
            if user == exclude: continue
            try: Protocol.send_message(sock, msg_type, data)
            except: pass
        
        if msg_type == MessageType.FILE_INFO:
            web_msg = {
                "type": "FILE_INFO", "sender": data.get("sender"),
                "filename": data.get("filename"), "original_filename": data.get("original_filename"),
                "filesize": data.get("filesize"), "file_type": data.get("file_type")
            }
            self._run_on_main_loop(global_bridge.broadcast(web_msg, sender=exclude))

    def _run_on_main_loop(self, coro):
        if self.main_loop and self.main_loop.is_running():
            asyncio.run_coroutine_threadsafe(coro, self.main_loop)