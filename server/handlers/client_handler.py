"""
Xử lý connection từng client - CẬP NHẬT
Server/handlers/client_handler.py
"""

from datetime import datetime
from common.protocol import Protocol, MessageType
from server.handlers.message_handler import MessageHandler
from server.handlers.file_handler import FileHandler

class ClientHandler:
    def __init__(self, server, client_socket, address):
        self.server = server
        self.client_socket = client_socket
        self.address = address
        self.username = None
        
        # Handlers
        self.message_handler = MessageHandler(server)
        self.file_handler = FileHandler(server)
    
    def handle(self):
        """Xử lý client connection"""
        try:
            while self.server.running:
                # Nhận message
                msg_type, data = Protocol.recv_message(self.client_socket)
                
                if msg_type is None:
                    break
                
                # Xử lý LOGIN
                if msg_type == MessageType.LOGIN:
                    if not self._handle_login(data):
                        return
                
                # Xử lý TEXT message
                elif msg_type == MessageType.TEXT:
                    self.message_handler.handle_text_message(
                        self.client_socket,
                        self.username,
                        data
                    )
                
                # Xử lý FILE UPLOAD
                elif msg_type == MessageType.FILE_UPLOAD:
                    self.file_handler.handle_file_upload(
                        self.client_socket,
                        self.username,
                        data
                    )
                
                # Xử lý FILE DOWNLOAD
                elif msg_type == MessageType.FILE_DOWNLOAD:
                    self.file_handler.handle_file_download(
                        self.client_socket,
                        data
                    )
                
                # Xử lý CALL - NEW
                elif msg_type == MessageType.CALL_REQUEST:
                    self.message_handler.handle_call_request(
                        self.client_socket,
                        self.username,
                        data
                    )
                
                elif msg_type == MessageType.CALL_ACCEPT:
                    self.message_handler.handle_call_accept(
                        self.client_socket,
                        self.username,
                        data
                    )
                
                elif msg_type == MessageType.CALL_REJECT:
                    self.message_handler.handle_call_reject(
                        self.client_socket,
                        self.username,
                        data
                    )
                
                elif msg_type == MessageType.CALL_BUSY:
                    self.message_handler.handle_call_busy(
                        self.client_socket,
                        self.username,
                        data
                    )
                
                elif msg_type == MessageType.CALL_END:
                    self.message_handler.handle_call_end(
                        self.client_socket,
                        self.username,
                        data
                    )
                
                # Xử lý WebRTC signaling - NEW
                elif msg_type == MessageType.WEBRTC_OFFER:
                    self.message_handler.handle_webrtc_signal(
                        self.client_socket,
                        self.username,
                        MessageType.WEBRTC_OFFER,
                        data
                    )
                
                elif msg_type == MessageType.WEBRTC_ANSWER:
                    self.message_handler.handle_webrtc_signal(
                        self.client_socket,
                        self.username,
                        MessageType.WEBRTC_ANSWER,
                        data
                    )
                
                elif msg_type == MessageType.WEBRTC_ICE:
                    self.message_handler.handle_webrtc_signal(
                        self.client_socket,
                        self.username,
                        MessageType.WEBRTC_ICE,
                        data
                    )
                # Thêm xử lý cho VIDEO_DATA và AUDIO_DATA
                elif msg_type in [MessageType.VIDEO_DATA, MessageType.AUDIO_DATA]:
                    self.message_handler.handle_media_data(
                        self.client_socket,
                        self.username,
                        msg_type,
                        data
                    )

                # Xử lý PING
                elif msg_type == MessageType.PING:
                    Protocol.send_message(self.client_socket, MessageType.PONG, {})
        
        except Exception as e:
            print(f"❌ Error handling {self.username or self.address}: {e}")
        
        finally:
            self._cleanup()
    
    def _handle_login(self, data):
        """
        Xử lý đăng nhập
        Returns: True nếu thành công, False nếu thất bại
        """
        username = data.get("username", "")
        
        if username in self.server.clients:
            Protocol.send_message(
                self.client_socket,
                MessageType.LOGIN_FAILED,
                {"message": "Username đã tồn tại!"}
            )
            self.client_socket.close()
            return False
        
        # Thêm client vào danh sách
        self.username = username
        self.server.clients[username] = self.client_socket
        
        # Gửi thông báo thành công
        Protocol.send_message(
            self.client_socket,
            MessageType.LOGIN_SUCCESS,
            {
                "username": username,
                "message": "Đăng nhập thành công!"
            }
        )
        
        # Gửi danh sách user
        self.server.send_user_list()
        
        # Thông báo user online
        self.server.broadcast(
            MessageType.USER_ONLINE,
            {
                "username": username,
                "timestamp": datetime.now().isoformat()
            },
            exclude=username
        )
        
        print(f"✅ {username} logged in")
        return True
    
    def _cleanup(self):
        """Cleanup khi client disconnect"""
        if self.username and self.username in self.server.clients:
            del self.server.clients[self.username]
            
            # Thông báo user offline
            self.server.broadcast(
                MessageType.USER_OFFLINE,
                {
                    "username": self.username,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Cập nhật user list
            self.server.send_user_list()
            
            print(f"👋 {self.username} disconnected")
        
        try:
            self.client_socket.close()
        except:
            pass