"""
Core logic cho Chat Client
"""
import socket
import threading
import os
from tkinter import Tk

from common.protocol import Protocol, MessageType
from common.config import CLIENT_DOWNLOAD_DIR, SOCKET_TIMEOUT, Colors
from client.ui.login_ui import LoginUI
from client.ui.chat_ui import ChatUI
from client.handlers.message_handler import MessageHandler
from client.handlers.file_handler import FileHandler

class ChatClient:
    def __init__(self):
        # Tkinter root
        self.root = Tk()
        self.root.title("Zalo Chat")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
       
        # Socket và connection
        self.socket = None
        self.username = None
        self.connected = False
        self.receive_thread = None
       
        # Event và flags cho file upload/download
        self.upload_event = threading.Event()
        self.upload_permission = False
        self.current_download_ui = None
       
        # Data
        self.users = []
        self.messages = []
       
        # Thư mục lưu file
        self.download_dir = CLIENT_DOWNLOAD_DIR
        os.makedirs(self.download_dir, exist_ok=True)
       
        # Colors
        self.colors = Colors
       
        # UI Components (sẽ được khởi tạo sau)
        self.login_ui = None
        self.chat_ui = None
       
        # Handlers
        self.message_handler = MessageHandler(self)
        self.file_handler = FileHandler(self)
       
        # Setup initial UI
        self.setup_login_ui()
       
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start main loop
        self.root.mainloop()
   
    def setup_login_ui(self):
        """Thiết lập giao diện đăng nhập"""
        self.login_ui = LoginUI(self)
   
    def setup_chat_ui(self):
        """Thiết lập giao diện chat"""
        if self.login_ui:
            self.login_ui.destroy()
        self.chat_ui = ChatUI(self)
   
    def login(self, username, server_info):
        """
        Đăng nhập vào server
        Returns: (success, message)
        """
        try:
            # Parse server info
            if ":" in server_info:
                host, port = server_info.split(":")
                port = int(port)
            else:
                host = server_info
                port = 5555
           
            # Kết nối
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(SOCKET_TIMEOUT)
            self.socket.connect((host, port))
            self.socket.settimeout(None)
           
            # Gửi LOGIN
            Protocol.send_message(
                self.socket,
                MessageType.LOGIN,
                {"username": username}
            )
           
            # Nhận response
            msg_type, data = Protocol.recv_message(self.socket)
           
            if msg_type == MessageType.LOGIN_FAILED:
                self.socket.close()
                return False, data.get("message", "Đăng nhập thất bại!")
           
            elif msg_type == MessageType.LOGIN_SUCCESS:
                self.username = username
                self.connected = True
               
                # Khởi động receive thread
                self.receive_thread = threading.Thread(
                    target=self.receive_messages,
                    daemon=True
                )
                self.receive_thread.start()
               
                return True, "Đăng nhập thành công!"
       
        except socket.timeout:
            return False, "Timeout! Server không phản hồi."
        except ConnectionRefusedError:
            return False, "Không thể kết nối tới server!"
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
   
    def receive_messages(self):
        """Thread nhận messages từ server"""
        while self.connected:
            try:
                msg_type, data = Protocol.recv_message(self.socket)
               
                if msg_type is None:
                    self.connected = False
                    self.root.after(0, self.message_handler.show_system_message, 
                                   "❌ Mất kết nối với server!")
                    break
               
                # Delegate cho message handler
                self.message_handler.handle_message(msg_type, data)
               
            except Exception as e:
                if self.connected:
                    print(f"Error receiving: {e}")
                    self.connected = False
                    self.root.after(0, self.message_handler.show_system_message, 
                                   "❌ Lỗi luồng nhận dữ liệu.")
                    break
   
    def send_text_message(self, message):
        """Gửi tin nhắn text"""
        try:
            Protocol.send_message(
                self.socket,
                MessageType.TEXT,
                {"message": message}
            )
            return True
        except Exception as e:
            self.message_handler.show_system_message(f"❌ Lỗi gửi tin nhắn: {e}")
            return False
   
    def on_closing(self):
        """Xử lý khi đóng app"""
        if self.connected:
            try:
                self.socket.close()
            except:
                pass
        self.root.destroy()