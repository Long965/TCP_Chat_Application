"""
client/handlers/call_handler.py
"""
from tkinter import messagebox
from common.protocol import Protocol, MessageType
from client.ui.call_ui import CallUI

class CallHandler:
    def __init__(self, client):
        self.client = client
        if not hasattr(self.client, 'current_call'):
            self.client.current_call = None

    def start_call(self, recipient, call_type="video"):
        """Gửi yêu cầu gọi"""
        Protocol.send_message(
            self.client.socket,
            MessageType.CALL_REQUEST,
            {"recipient": recipient, "sender": self.client.username, "call_type": call_type}
        )
        # Mở UI ở chế độ chờ (Caller)
        self.client.current_call = CallUI(self.client, recipient, call_type, is_caller=True)

    def handle_call_request(self, data):
        """Xử lý khi có người gọi đến"""
        caller = data.get("caller") or data.get("sender")
        call_type = data.get("call_type", "video")
        
        if self.client.current_call:
            Protocol.send_message(self.client.socket, MessageType.CALL_BUSY, {"recipient": caller, "sender": self.client.username})
            return

        # Mở UI ở chế độ nhận (Receiver)
        self.client.current_call = CallUI(self.client, caller, call_type, is_caller=False)