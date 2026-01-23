"""
client/main.py - Entry Point
"""
import socket
import threading
import sys
import os
from tkinter import Tk, messagebox

# Setup đường dẫn import để chạy từ thư mục gốc
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from common.config import Colors, UISettings
from common.protocol import Protocol, MessageType
from client.ui.login_ui import LoginUI
from client.ui.chat_ui import ChatUI
from client.handlers.message_handler import MessageHandler
from client.handlers.file_handler import FileHandler
from client.handlers.call_handler import CallHandler

class ClientApp:
    def __init__(self):
        # 1. Setup Window
        self.root = Tk()
        self.root.title("TCP Chat Application")
        self.root.geometry(f"{UISettings.WINDOW_WIDTH}x{UISettings.WINDOW_HEIGHT}")
        self.root.minsize(UISettings.MIN_WIDTH, UISettings.MIN_HEIGHT)
        self.root.configure(bg=Colors.BG_MAIN)

        # 2. Data & State
        self.username = None
        self.socket = None
        self.connected = False  # <--- [FIX] Thêm biến trạng thái kết nối
        self.is_running = True
        self.users = []
        self.messages = []
        self.colors = Colors
        self.current_call = None

        # 3. Handlers
        self.message_handler = MessageHandler(self)
        self.file_handler = FileHandler(self)
        self.call_handler = CallHandler(self)

        # 4. UI Managers
        self.login_ui = None
        self.chat_ui = None

        # 5. Start with Login Screen
        self.show_login_screen()

    def show_login_screen(self):
        self.login_ui = LoginUI(self)
        self.login_ui.pack(fill="both", expand=True)

    def connect_to_server(self, username, server_ip):
        try:
            if not username:
                return messagebox.showwarning("Lỗi", "Vui lòng nhập tên!")

            # Parse IP
            if ":" in server_ip:
                host, port = server_ip.split(":")
                port = int(port)
            else:
                host, port = "127.0.0.1", 5555

            # Connect
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            
            # [FIX] Đánh dấu đã kết nối thành công
            self.connected = True 

            # Send Login
            self.username = username
            Protocol.send_message(self.socket, MessageType.LOGIN, {"username": username})

            # Start Listener Thread
            threading.Thread(target=self.receive_messages, daemon=True).start()

        except Exception as e:
            self.connected = False # [FIX] Đánh dấu thất bại
            messagebox.showerror("Lỗi kết nối", f"Không thể kết nối Server:\n{e}")

    def receive_messages(self):
        print("🎧 Client đang lắng nghe...")
        while self.is_running:
            try:
                msg_type, data = Protocol.recv_message(self.socket)
                if not msg_type:
                    print("❌ Mất kết nối Server")
                    self.connected = False # [FIX] Cập nhật trạng thái khi mất kết nối
                    break
                
                # Chuyển cho MessageHandler xử lý
                self.message_handler.handle_message(msg_type, data)
                
            except Exception as e:
                print(f"❌ Error receiving: {e}")
                self.connected = False # [FIX] Cập nhật trạng thái khi lỗi
                break
        
        # Cleanup khi vòng lặp kết thúc
        if self.socket: 
            try: self.socket.close()
            except: pass

    def send_text_message(self, message, recipient=None):
        # Chỉ gửi nếu socket còn kết nối
        if self.socket and self.connected:
            Protocol.send_message(self.socket, MessageType.TEXT, {
                "message": message,
                "sender": self.username,
                "recipient": recipient
            })

    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.is_running = False

if __name__ == "__main__":
    app = ClientApp()
    app.run()