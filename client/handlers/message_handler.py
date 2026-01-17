"""
Xử lý các loại message nhận được từ server - CẬP NHẬT
Client/handlers/message_handler.py
"""

from common.protocol import MessageType
from client.ui.message_ui import MessageUI

class MessageHandler:
    def __init__(self, client):
        self.client = client
    
    def handle_message(self, msg_type, data):
        """Xử lý message dựa vào loại"""
        
        # TEXT MESSAGE (Group chat)
        if msg_type == MessageType.TEXT:
            recipient = data.get("recipient")
            
            # Nếu có recipient -> tin nhắn riêng
            if recipient:
                self._handle_private_message(data)
            else:
                # Tin nhắn nhóm
                self.client.root.after(0, self.display_text_message, data)
        
        # FILE INFO
        elif msg_type == MessageType.FILE_INFO:
            status = data.get("status")
            
            # Server báo "Ready" -> Báo cho thread upload gửi dữ liệu
            if status == "ready":
                self.client.upload_permission = True
                self.client.upload_event.set()
                return
            
            # Server báo "Sending" -> Nhận dữ liệu file
            elif status == "sending":
                filename = data.get("filename")
                filesize = data.get("filesize")
                self.client.file_handler.handle_file_download_data(filename, filesize)
                return
            
            # Hiển thị thông báo có file mới
            else:
                self.client.root.after(0, self.display_file_message, data)
        
        # FILE COMPLETE
        elif msg_type == MessageType.FILE_COMPLETE:
            filename = data.get("filename", "File")
            self.client.root.after(0, self.show_system_message,
                                  f"✅ Đã gửi thành công: {filename}")
        
        # FILE ERROR
        elif msg_type == MessageType.FILE_ERROR:
            err_msg = data.get("message", "Lỗi file không xác định")
            self.client.root.after(0, self.show_system_message,
                                  f"❌ Lỗi file: {err_msg}")
            
            # Mở khóa nếu đang đợi upload
            self.client.upload_permission = False
            self.client.upload_event.set()
        
        # USER MANAGEMENT
        elif msg_type == MessageType.USER_LIST:
            users = data.get("users", [])
            self.client.root.after(0, self._update_user_list, users)
        
        elif msg_type == MessageType.USER_ONLINE:
            username = data.get("username")
            self.client.root.after(0, self.show_system_message,
                                  f"✅ {username} đã online")
        
        elif msg_type == MessageType.USER_OFFLINE:
            username = data.get("username")
            self.client.root.after(0, self.show_system_message,
                                  f"👋 {username} đã offline")
        
        # CALL HANDLING - NEW
        elif msg_type == MessageType.CALL_REQUEST:
            self.client.call_handler.handle_call_request(data)
        
        elif msg_type == MessageType.CALL_ACCEPT:
            self.client.call_handler.handle_call_accept(data)
        
        elif msg_type == MessageType.CALL_REJECT:
            self.client.call_handler.handle_call_reject(data)
        
        elif msg_type == MessageType.CALL_BUSY:
            self.client.call_handler.handle_call_busy(data)
        
        elif msg_type == MessageType.CALL_END:
            self.client.call_handler.handle_call_end(data)
        
        elif msg_type == MessageType.WEBRTC_OFFER:
            self.client.call_handler.handle_webrtc_offer(data)
        
        elif msg_type == MessageType.WEBRTC_ANSWER:
            self.client.call_handler.handle_webrtc_answer(data)
        
        elif msg_type == MessageType.WEBRTC_ICE:
            self.client.call_handler.handle_webrtc_ice(data)
    
    def _handle_private_message(self, data):
        """Xử lý tin nhắn riêng tư"""
        sender = data.get("sender")
        recipient = data.get("recipient")
        
        # Xác định người chat (không phải mình)
        peer = sender if sender != self.client.username else recipient
        
        # Kiểm tra xem có cửa sổ chat với người này chưa
        if peer in self.client.private_chats:
            # Hiển thị trong cửa sổ đã mở
            self.client.root.after(0, 
                self.client.private_chats[peer].display_message, data)
        else:
            # Tạo cửa sổ chat mới và hiển thị
            from client.ui.private_chat_ui import PrivateChatUI
            
            def create_and_show():
                private_chat = PrivateChatUI(self.client, peer)
                self.client.private_chats[peer] = private_chat
                private_chat.display_message(data)
            
            self.client.root.after(0, create_and_show)
    
    def display_text_message(self, data):
        """Hiển thị tin nhắn text trong group chat"""
        if self.client.chat_ui:
            MessageUI.display_text_message(
                self.client.chat_ui.messages_container,
                data,
                self.client.username,
                self.client.colors
            )
    
    def display_file_message(self, data):
        """Hiển thị thông báo file"""
        if self.client.chat_ui:
            MessageUI.display_file_message(
                self.client.chat_ui.messages_container,
                data,
                self.client.file_handler.download_file,
                self.client.colors
            )
    
    def show_system_message(self, message):
        """Hiển thị thông báo hệ thống"""
        if self.client.chat_ui:
            MessageUI.display_system_message(
                self.client.chat_ui.messages_container,
                message,
                self.client.colors
            )
    
    def _update_user_list(self, users):
        """Cập nhật danh sách user"""
        self.client.users = users
        if self.client.chat_ui:
            self.client.chat_ui.update_user_list(users)