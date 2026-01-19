from tkinter import messagebox
from common.protocol import MessageType
from client.ui.message_ui import MessageUI
from client.ui.chat_ui import ChatUI # Import ChatUI để chuyển màn hình

class MessageHandler:
    def __init__(self, client):
        self.client = client

    def handle_message(self, msg_type, data):
        """Router xử lý tin nhắn từ Server"""
        # Debug: In ra để biết client nhận được gì
        print(f"📩 Client received: {msg_type}") 

        # --- 1. XỬ LÝ ĐĂNG NHẬP ---
        if msg_type == MessageType.LOGIN_SUCCESS:
            print("✅ Login Success -> Switching UI")
            # Chuyển UI phải chạy trên Main Thread
            self.client.root.after(0, self._switch_to_chat)
            
        elif msg_type == MessageType.LOGIN_FAILURE:
            error_msg = data.get("message", "Đăng nhập thất bại")
            self.client.root.after(0, lambda: messagebox.showerror("Lỗi", error_msg))

        # --- 2. XỬ LÝ DANH SÁCH USER ---
        elif msg_type == MessageType.LIST_USERS:
            self._handle_user_list(data)

        # --- 3. XỬ LÝ TIN NHẮN CHAT & FILE ---
        elif msg_type == MessageType.TEXT:
            # Gán loại tin nhắn để lưu lịch sử cho đúng
            data["type"] = "TEXT" 
            self._handle_text_message(data)
        
        elif msg_type == MessageType.FILE_INFO:
            # Gán loại tin nhắn để lưu lịch sử cho đúng
            data["type"] = "FILE_INFO"
            self._handle_file_message(data)
            
        elif msg_type == MessageType.ERROR:
            self.client.root.after(0, lambda: messagebox.showerror("Lỗi Server", data.get("message")))
            
        # --- 4. XỬ LÝ CUỘC GỌI ---
        elif msg_type in [MessageType.CALL_REQUEST, MessageType.CALL_ACCEPT, MessageType.CALL_REJECT, MessageType.CALL_END, MessageType.CALL_BUSY, MessageType.CALL_ICE_CANDIDATE]:
            self._handle_call_message(msg_type, data)

    def _switch_to_chat(self):
        """Chuyển từ màn hình Login sang Chat"""
        if self.client.login_ui:
            self.client.login_ui.destroy()
            self.client.login_ui = None
        
        # Tạo giao diện Chat
        self.client.chat_ui = ChatUI(self.client)
        self.client.chat_ui.pack(fill="both", expand=True)
        
        # [FIX QUAN TRỌNG] Cập nhật ngay danh sách user nếu đã có dữ liệu
        # (Khắc phục lỗi 2 người online nhưng danh sách trống)
        if self.client.users:
            print(f"🔄 Updating user list immediately: {len(self.client.users)} users")
            self.client.chat_ui.update_user_list(self.client.users)

    def _handle_user_list(self, data):
        """Cập nhật danh sách người dùng online"""
        self.client.users = data.get("users", [])
        print(f"👥 Users updated: {self.client.users}")
        
        # Nếu giao diện Chat đã mở thì update ngay
        if self.client.chat_ui:
            self.client.root.after(0, lambda: self.client.chat_ui.update_user_list(self.client.users))

    def _handle_text_message(self, data):
        """Xử lý hiển thị tin nhắn Text"""
        sender = data.get("sender")
        msg_recipient = data.get("recipient")
        is_sender = (sender == self.client.username)
        
        # Thêm vào lịch sử tin nhắn của Client
        self.client.messages.append(data)

        # Logic hiển thị UI
        current_chat = self.client.chat_ui.current_chat if self.client.chat_ui else None
        should_display = False
        
        if not msg_recipient: # Chat nhóm
            if not current_chat: should_display = True
        else: # Chat riêng
            if is_sender:
                if current_chat == msg_recipient: should_display = True
            else:
                if current_chat == sender: should_display = True

        if should_display and self.client.chat_ui:
            self.client.root.after(0, lambda: self._draw_text(data, is_sender))

    def _draw_text(self, data, is_sender):
        MessageUI.display_text_message(
            self.client.chat_ui.messages_container,
            data,
            is_sender,
            self.client.colors
        )
        self.client.chat_ui.canvas.yview_moveto(1)

    def _handle_file_message(self, data):
        """Xử lý hiển thị tin nhắn File"""
        sender = data.get("sender")
        msg_recipient = data.get("recipient")
        is_sender = (sender == self.client.username)
        
        # Thêm vào lịch sử
        self.client.messages.append(data)

        current_chat = self.client.chat_ui.current_chat if self.client.chat_ui else None
        should_display = False

        if not msg_recipient:
            if not current_chat: should_display = True
        else:
            if is_sender and current_chat == msg_recipient: should_display = True
            elif not is_sender and current_chat == sender: should_display = True

        if should_display and self.client.chat_ui:
            self.client.root.after(0, lambda: self._draw_file(data, is_sender))

    def _draw_file(self, data, is_sender):
        MessageUI.display_file_message(
            self.client.chat_ui.messages_container,
            data,
            is_sender,
            self.client.colors,
            download_callback=self.client.file_handler.request_download
        )
        self.client.chat_ui.canvas.yview_moveto(1)

    def _handle_call_message(self, msg_type, data):
        """Chuyển tiếp tin nhắn gọi video"""
        if self.client.call_handler:
            if msg_type == MessageType.CALL_REQUEST:
                self.client.root.after(0, lambda: self.client.call_handler.handle_call_request(data))
            elif msg_type == MessageType.CALL_ACCEPT:
                self.client.root.after(0, lambda: self.client.call_handler.handle_call_accept(data))
            elif msg_type == MessageType.CALL_REJECT:
                self.client.root.after(0, lambda: self.client.call_handler.handle_call_reject(data))
            elif msg_type == MessageType.CALL_END:
                self.client.root.after(0, lambda: self.client.call_handler.handle_call_end(data))
            elif msg_type == MessageType.CALL_ICE_CANDIDATE:
                # [FIX] Đưa vào root.after để tránh xung đột luồng khi xử lý tín hiệu
                self.client.root.after(0, lambda: self.client.call_handler.handle_ice_candidate(data))