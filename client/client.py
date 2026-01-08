import socket
import sys
import os
import time

# Thêm thư mục shared vào path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.protocol import Protocol, MessageType
from receive_thread import ReceiveThread
from send_handler import SendHandler
from ui_console import ConsoleUI
import config

class ChatClient:
    def __init__(self):
        self.client_socket = None
        self.username = None
        self.ui = None
        self.receive_thread = None
        self.send_handler = None
        self.connected = False
    
    def start(self):
        """Khởi động client"""
        try:
            # Nhập username
            print("="*70)
            print("CHAT CLIENT")
            print("="*70)
            self.username = input("Nhập username: ").strip()
            
            if not self.username:
                print("Username không được để trống!")
                return
            
            # Kết nối tới server
            print(f"\nĐang kết nối tới {config.HOST}:{config.PORT}...")
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((config.HOST, config.PORT))
            
            # Gửi thông tin join
            join_msg = Protocol.encode_message(
                MessageType.JOIN, self.username, ""
            )
            self.client_socket.send(join_msg)
            
            # Nhận phản hồi từ server
            response = self.client_socket.recv(config.BUFFER_SIZE)
            msg = Protocol.decode_message(response)
            
            if msg["type"] == MessageType.ERROR:
                print(f"\n[ERROR] {msg['content']}")
                self.client_socket.close()
                return
            
            print(f"[SUCCESS] {msg['content']}")
            self.connected = True
            
            # Khởi tạo UI
            self.ui = ConsoleUI(self.username)
            
            # Khởi động thread nhận dữ liệu
            self.receive_thread = ReceiveThread(self.client_socket, self.ui)
            self.receive_thread.start()
            
            # Khởi tạo send handler
            self.send_handler = SendHandler(self.client_socket, self.username)
            
            # Đợi một chút để nhận user list
            time.sleep(0.5)
            
            # Xóa màn hình và hiển thị giao diện
            self.ui.clear_screen()
            self.ui.show_header()
            self.ui.show_help()
            
            # Vòng lặp chính
            self.main_loop()
            
        except ConnectionRefusedError:
            print(f"\n[ERROR] Không thể kết nối tới server {config.HOST}:{config.PORT}")
            print("Hãy chắc chắn server đang chạy!")
        except Exception as e:
            print(f"\n[ERROR] {e}")
        finally:
            self.disconnect()
    
    def main_loop(self):
        """Vòng lặp chính xử lý input"""
        while self.connected:
            try:
                user_input = self.ui.get_input()
                
                if not user_input:
                    continue
                
                # Xử lý lệnh
                if user_input.startswith("/"):
                    self.handle_command(user_input)
                # Tin nhắn riêng
                elif user_input.startswith("@"):
                    self.handle_private_message(user_input)
                # Tin nhắn công khai
                else:
                    if self.send_handler.send_message(user_input):
                        self.ui.show_message("BẠN", user_input)
                    else:
                        self.ui.show_error("Không thể gửi tin nhắn!")
                
            except KeyboardInterrupt:
                print("\n")
                break
    
    def handle_command(self, command):
        """Xử lý các lệnh"""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        
        if cmd in ["/quit", "/exit"]:
            self.connected = False
        
        elif cmd == "/help":
            self.ui.show_help()
        
        elif cmd == "/clear":
            self.ui.clear_screen()
            self.ui.show_header()
        
        elif cmd == "/users":
            self.ui.show_users()
        
        elif cmd == "/file":
            if len(parts) < 2:
                self.ui.show_error("Cú pháp: /file <đường_dẫn_file>")
                return
            
            filepath = parts[1].strip()
            print(f"\nĐang gửi file: {filepath}...")
            success, result = self.send_handler.send_file(filepath)
            
            if success:
                print(f"[SUCCESS] {result}\n")
            else:
                self.ui.show_error(result)
        
        else:
            self.ui.show_error(f"Lệnh không hợp lệ: {cmd}")
            self.ui.show_error("Gõ /help để xem danh sách lệnh")
    
    def handle_private_message(self, message):
        """Xử lý tin nhắn riêng"""
        # Format: @username tin nhắn
        parts = message[1:].split(maxsplit=1)
        
        if len(parts) < 2:
            self.ui.show_error("Cú pháp: @username tin_nhắn")
            return
        
        target_user = parts[0]
        content = parts[1]
        
        if self.send_handler.send_private_message(target_user, content):
            # Tin nhắn sẽ được hiển thị khi nhận response từ server
            pass
        else:
            self.ui.show_error("Không thể gửi tin nhắn riêng!")
    
    def disconnect(self):
        """Ngắt kết nối"""
        if self.connected:
            print("\n[CLIENT] Đang ngắt kết nối...")
            
            # Gửi thông báo leave
            if self.send_handler:
                self.send_handler.send_leave()
            
            # Dừng thread nhận
            if self.receive_thread:
                self.receive_thread.stop()
            
            # Đóng socket
            if self.client_socket:
                self.client_socket.close()
            
            self.connected = False
            print("[CLIENT] Đã ngắt kết nối!")

if __name__ == "__main__":
    client = ChatClient()
    client.start()