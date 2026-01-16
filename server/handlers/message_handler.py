"""
Xử lý routing và broadcast message
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