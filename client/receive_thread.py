import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
from shared.protocol import Protocol, MessageType
from file_handler import FileHandler
import config

class ReceiveThread(threading.Thread):
    def __init__(self, client_socket, ui):
        super().__init__()
        self.client_socket = client_socket
        self.ui = ui  # Có thể là ConsoleUI hoặc ChatClientGUI
        self.running = True
        self.daemon = True
    
    def run(self):
        """Nhận và xử lý dữ liệu từ server"""
        while self.running:
            try:
                data = self.client_socket.recv(config.BUFFER_SIZE)
                if not data:
                    self.ui.show_message("SERVER", "Mất kết nối với server!")
                    self.running = False
                    break
                
                msg = Protocol.decode_message(data)
                self.handle_message(msg)
                
            except Exception as e:
                if self.running:
                    self.ui.show_message("ERROR", f"Lỗi nhận dữ liệu: {e}")
                break
    
    def handle_message(self, msg):
        """Xử lý message dựa vào type"""
        msg_type = msg["type"]
        
        if msg_type == MessageType.TEXT:
            # Tin nhắn thông thường
            self.ui.show_message(msg["sender"], msg["content"])
        
        elif msg_type == MessageType.PRIVATE:
            # Tin nhắn riêng
            extra = msg.get("extra", "")
            self.ui.show_message(msg["sender"], msg["content"], extra)
        
        elif msg_type == MessageType.FILE:
            # Thông báo về file
            self.ui.show_message(msg["sender"], msg["content"])
        
        elif msg_type == MessageType.JOIN:
            # User tham gia
            self.ui.show_message("SERVER", msg["content"])
        
        elif msg_type == MessageType.LEAVE:
            # User rời đi
            self.ui.show_message("SERVER", msg["content"])
        
        elif msg_type == MessageType.USER_LIST:
            # Danh sách user
            users = msg["content"].split(",") if msg["content"] else []
            self.ui.update_user_list(users)
        
        elif msg_type == MessageType.SUCCESS:
            # Thông báo thành công
            self.ui.show_message("SERVER", msg["content"])
        
    
    def stop(self):
        """Dừng thread"""
        self.running = False