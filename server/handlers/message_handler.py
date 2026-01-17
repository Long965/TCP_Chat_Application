"""
Xử lý routing và broadcast message - CẬP NHẬT
Server/handlers/message_handler.py
"""

from datetime import datetime
from common.protocol import Protocol, MessageType

class MessageHandler:
    def __init__(self, server):
        self.server = server
    
    def handle_text_message(self, client_socket, username, data):
        """Xử lý tin nhắn text"""
        recipient = data.get("recipient")  # Lấy tên người nhận (nếu có)
        message_content = data.get("message", "")
        
        timestamp = datetime.now().isoformat()
        
        msg_data = {
            "sender": username,
            "recipient": recipient,
            "message": message_content,
            "timestamp": timestamp
        }
        
        if recipient:
            # CHAT RIÊNG
            # 1. Gửi cho người nhận
            if recipient in self.server.clients:
                Protocol.send_message(
                    self.server.clients[recipient],
                    MessageType.TEXT,
                    msg_data
                )
            
            # 2. Gửi lại cho người gửi (để hiện lên màn hình của họ)
            Protocol.send_message(client_socket, MessageType.TEXT, msg_data)
            
            print(f"🔒 [{username} -> {recipient}] {message_content}")
        
        else:
            # CHAT NHÓM (Broadcast)
            print(f"💬 [{username}] {message_content}")
            self.server.broadcast(MessageType.TEXT, msg_data)
    
    def handle_call_request(self, client_socket, username, data):
        """Xử lý yêu cầu gọi"""
        recipient = data.get("recipient")
        call_type = data.get("call_type")
        
        print(f"📞 Call request: {username} -> {recipient} ({call_type})")
        
        if recipient in self.server.clients:
            # Forward yêu cầu đến người nhận
            Protocol.send_message(
                self.server.clients[recipient],
                MessageType.CALL_REQUEST,
                {
                    "caller": username,
                    "call_type": call_type
                }
            )
        else:
            # Người nhận không online
            Protocol.send_message(
                client_socket,
                MessageType.ERROR,
                {"message": "Người dùng không online"}
            )
    
    def handle_call_accept(self, client_socket, username, data):
        """Xử lý chấp nhận cuộc gọi"""
        caller = data.get("caller")
        
        print(f"✅ Call accepted: {username} accepted {caller}")
        
        if caller in self.server.clients:
            Protocol.send_message(
                self.server.clients[caller],
                MessageType.CALL_ACCEPT,
                {
                    "recipient": username
                }
            )
    
    def handle_call_reject(self, client_socket, username, data):
        """Xử lý từ chối cuộc gọi"""
        caller = data.get("caller")
        
        print(f"❌ Call rejected: {username} rejected {caller}")
        
        if caller in self.server.clients:
            Protocol.send_message(
                self.server.clients[caller],
                MessageType.CALL_REJECT,
                {
                    "recipient": username
                }
            )
    
    def handle_call_busy(self, client_socket, username, data):
        """Xử lý khi người nhận đang bận"""
        caller = data.get("caller")
        
        print(f"📵 Call busy: {username} is busy")
        
        if caller in self.server.clients:
            Protocol.send_message(
                self.server.clients[caller],
                MessageType.CALL_BUSY,
                {
                    "recipient": username
                }
            )
    
    def handle_call_end(self, client_socket, username, data):
        """Xử lý kết thúc cuộc gọi"""
        peer = data.get("peer")
        
        print(f"📴 Call ended: {username} <-> {peer}")
        
        if peer in self.server.clients:
            Protocol.send_message(
                self.server.clients[peer],
                MessageType.CALL_END,
                {
                    "peer": username
                }
            )
    
    def handle_webrtc_signal(self, client_socket, username, msg_type, data):
        """Xử lý WebRTC signaling"""
        peer = data.get("peer")
        
        if peer in self.server.clients:
            Protocol.send_message(
                self.server.clients[peer],
                msg_type,
                {
                    "peer": username,
                    "data": data.get("data")
                }
            )