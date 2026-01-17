"""
Xử lý các loại message nhận được từ server
Client/handlers/message_handler.py
"""

from common.protocol import MessageType
from client.ui.message_ui import MessageUI

class MessageHandler:
    def __init__(self, client):
        self.client = client
    
    def handle_message(self, msg_type, data):
        """Xử lý message dựa vào loại"""
        
        # TEXT MESSAGE
        if msg_type == MessageType.TEXT:
            # Lưu vào history
            self.client.add_message(data)
            
            # Hiển thị nếu đang ở view tương ứng
            self.client.root.after(0, self.display_message_in_current_view, data)
        
        # FILE INFO
        elif msg_type == MessageType.FILE_INFO:
            status = data.get("status")
            
            if status == "ready":
                self.client.upload_permission = True
                self.client.upload_event.set()
                return
            
            elif status == "sending":
                filename = data.get("filename")
                filesize = data.get("filesize")
                self.client.file_handler.handle_file_download_data(filename, filesize)
                return
            
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
        
        # CALL HANDLING
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
    
    def display_message_in_current_view(self, data):
        """Hiển thị message nếu phù hợp với view hiện tại"""
        if not self.client.chat_ui:
            return
        
        sender = data.get("sender")
        recipient = data.get("recipient")
        current_chat = self.client.chat_ui.current_chat
        
        # Nếu đang ở group chat
        if current_chat is None:
            # Chỉ hiển thị tin nhắn không có recipient (group messages)
            if not recipient:
                MessageUI.display_text_message(
                    self.client.chat_ui.messages_container,
                    data,
                    self.client.username,
                    self.client.colors
                )
        
        # Nếu đang ở private chat
        else:
            # Hiển thị nếu tin nhắn liên quan đến conversation này
            if (sender == current_chat and recipient == self.client.username) or \
               (sender == self.client.username and recipient == current_chat):
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