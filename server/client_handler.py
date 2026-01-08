import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
from shared.protocol import Protocol, MessageType
from file_handler import FileHandler
import config

class ClientHandler(threading.Thread):
    def __init__(self, client_socket, address, user_manager):
        super().__init__()
        self.client_socket = client_socket
        self.address = address
        self.user_manager = user_manager
        self.username = None
        self.running = True
    
    def run(self):
        """Chạy thread xử lý client"""
        print(f"[NEW CONNECTION] {self.address} connected.")
        
        try:
            # Nhận username từ client
            data = self.client_socket.recv(config.BUFFER_SIZE)
            msg = Protocol.decode_message(data)
            
            if msg["type"] == MessageType.JOIN:
                self.username = msg["sender"]
                
                # Kiểm tra username đã tồn tại
                if not self.user_manager.add_user(self.username, self.client_socket):
                    error_msg = Protocol.encode_message(
                        MessageType.ERROR, "SERVER", 
                        "Username đã tồn tại!"
                    )
                    self.client_socket.send(error_msg)
                    self.client_socket.close()
                    return
                
                # Gửi thông báo thành công
                success_msg = Protocol.encode_message(
                    MessageType.SUCCESS, "SERVER", 
                    f"Chào mừng {self.username}!"
                )
                self.client_socket.send(success_msg)
                
                # Gửi danh sách user
                users = ",".join(self.user_manager.get_all_users())
                user_list_msg = Protocol.encode_message(
                    MessageType.USER_LIST, "SERVER", users
                )
                self.client_socket.send(user_list_msg)
                
                # Thông báo cho tất cả user khác
                join_msg = Protocol.encode_message(
                    MessageType.JOIN, "SERVER", 
                    f"{self.username} đã tham gia!"
                )
                self.user_manager.broadcast_message(join_msg, self.client_socket)
                
                print(f"[USER JOINED] {self.username}")
                
                # Xử lý messages
                self.handle_messages()
            
        except Exception as e:
            print(f"[ERROR] {self.address}: {e}")
        finally:
            self.disconnect()
    
    def handle_messages(self):
        """Xử lý các message từ client"""
        while self.running:
            try:
                data = self.client_socket.recv(config.BUFFER_SIZE)
                if not data:
                    break
                
                msg = Protocol.decode_message(data)
                
                if msg["type"] == MessageType.TEXT:
                    # Broadcast tin nhắn
                    broadcast_msg = Protocol.encode_message(
                        MessageType.TEXT, self.username, msg["content"]
                    )
                    self.user_manager.broadcast_message(broadcast_msg)
                    print(f"[{self.username}] {msg['content']}")
                
                elif msg["type"] == MessageType.PRIVATE:
                    # Gửi tin nhắn riêng
                    target_user = msg["extra"]
                    target_socket = self.user_manager.get_user_socket(target_user)
                    
                    if target_socket:
                        private_msg = Protocol.encode_message(
                            MessageType.PRIVATE, self.username, 
                            msg["content"], f"(riêng)"
                        )
                        target_socket.send(private_msg)
                        
                        # Gửi xác nhận cho người gửi
                        confirm_msg = Protocol.encode_message(
                            MessageType.PRIVATE, "BẠN", 
                            msg["content"], f"→ {target_user}"
                        )
                        self.client_socket.send(confirm_msg)
                    else:
                        error_msg = Protocol.encode_message(
                            MessageType.ERROR, "SERVER", 
                            f"User {target_user} không tồn tại!"
                        )
                        self.client_socket.send(error_msg)
                
                elif msg["type"] == MessageType.FILE:
                    # Nhận file
                    file_info = Protocol.decode_file_info(msg["content"])
                    filename = file_info["filename"]
                    filesize = file_info["filesize"]
                    
                    print(f"[FILE] {self.username} đang gửi: {filename} ({filesize} bytes)")
                    
                    # Gửi ACK
                    ack = Protocol.encode_message(MessageType.SUCCESS, "SERVER", "OK")
                    self.client_socket.send(ack)
                    
                    # Nhận file
                    success, result = FileHandler.receive_file(
                        self.client_socket, filename, filesize
                    )
                    
                    if success:
                        print(f"[FILE] Đã nhận file: {filename}")
                        # Thông báo cho tất cả
                        file_msg = Protocol.encode_message(
                            MessageType.FILE, self.username, 
                            f"đã gửi file: {filename}"
                        )
                        self.user_manager.broadcast_message(file_msg)
                    else:
                        error_msg = Protocol.encode_message(
                            MessageType.ERROR, "SERVER", 
                            f"Lỗi nhận file: {result}"
                        )
                        self.client_socket.send(error_msg)
                
                elif msg["type"] == MessageType.LEAVE:
                    break
                    
            except Exception as e:
                print(f"[ERROR] Xử lý message: {e}")
                break
    
    def disconnect(self):
        """Ngắt kết nối client"""
        if self.username:
            self.user_manager.remove_user(self.username)
            
            # Thông báo cho tất cả
            leave_msg = Protocol.encode_message(
                MessageType.LEAVE, "SERVER", 
                f"{self.username} đã rời khỏi!"
            )
            self.user_manager.broadcast_message(leave_msg)
            
            print(f"[USER LEFT] {self.username}")
        
        self.client_socket.close()
        self.running = False