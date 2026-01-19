"""
client/handlers/message_handler.py
"""
import traceback
from common.protocol import MessageType
from client.ui.chat_ui import ChatUI

class MessageHandler:
    def __init__(self, client):
        self.client = client

    def handle_message(self, msg_type, data):
        if msg_type == MessageType.LOGIN_SUCCESS:
            self.client.root.after(0, self._switch_to_chat)
        elif msg_type == MessageType.LOGIN_FAILURE:
            self.client.root.after(0, lambda: self.client.login_ui.show_error(data.get("message")))
        elif msg_type == MessageType.LIST_USERS:
            self.client.users = data.get("users", [])
            if self.client.chat_ui:
                self.client.root.after(0, lambda: self.client.chat_ui.update_user_list(self.client.users))
        elif msg_type in [MessageType.TEXT, MessageType.FILE_INFO]:
            data["type"] = "FILE_INFO" if msg_type == MessageType.FILE_INFO else "TEXT"
            self.client.messages.append(data)
            if self.client.chat_ui:
                self.client.root.after(0, lambda: self.client.chat_ui.display_new_message(data))
        elif msg_type == MessageType.CALL_REQUEST:
            if self.client.call_handler: # Xử lý cuộc gọi
                self.client.root.after(0, lambda: self.client.call_handler.handle_call_request(data))

    def _switch_to_chat(self):
        if self.client.login_ui:
            self.client.login_ui.destroy()
            self.client.login_ui = None
        self.client.chat_ui = ChatUI(self.client)
        self.client.chat_ui.pack(fill="both", expand=True)