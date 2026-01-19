"""
server/bridge.py - Fix lỗi lặp tin nhắn trên Web
"""
from fastapi import WebSocket
from common.protocol import Protocol, MessageType
import asyncio
import json

class BridgeManager:
    def __init__(self):
        self.tcp_clients = {}  # {username: socket}
        self.web_clients = {}  # {username: websocket}

    def add_tcp(self, username, socket):
        # --- LOGIC MỚI: KICK USER CŨ ---
        if username in self.tcp_clients:
            print(f"🔄 [Bridge] Phát hiện kết nối cũ của '{username}'. Đang đóng để thay thế...")
            try:
                old_socket = self.tcp_clients[username]
                old_socket.close() # Đóng socket cũ
            except Exception as e:
                print(f"⚠️ Lỗi đóng socket cũ: {e}")
        # -------------------------------
        
        self.tcp_clients[username] = socket
        print(f"✅ [Bridge] TCP User added: {username}")

    async def add_web(self, username, websocket: WebSocket):
        await websocket.accept()
        # Logic Kick cho Web
        if username in self.web_clients:
             try: await self.web_clients[username].close()
             except: pass
             
        self.web_clients[username] = websocket
        print(f"✅ [Bridge] Web User added: {username}")

    def remove_user(self, username):
        # Chỉ xóa nếu user tồn tại
        if username in self.tcp_clients:
            del self.tcp_clients[username]
        if username in self.web_clients:
            del self.web_clients[username]
        print(f"👋 [Bridge] User removed: {username}")

    async def handle_message(self, message_dict, sender=None):
        """Xử lý định tuyến tin nhắn (Riêng/Chung)"""
        # 1. Chuẩn hóa dữ liệu đầu vào
        msg_type = message_dict.get("type", "TEXT")
        recipient = message_dict.get("recipient")
        
        # 2. Tạo Payload chuẩn (Chứa đầy đủ thông tin cho cả Web và Desktop)
        # Web dùng 'message', Desktop dùng 'content' -> Gán cả 2 để tương thích
        text_content = message_dict.get("message") or message_dict.get("content")
        
        payload = {
            "type": msg_type,
            "sender": sender,
            "recipient": recipient,
            "message": text_content, 
            "content": text_content, 
            "timestamp": message_dict.get("timestamp"),
            # File Info
            "filename": message_dict.get("filename"),
            "original_filename": message_dict.get("original_filename"),
            "filesize": message_dict.get("filesize"),
            "file_type": message_dict.get("file_type"),
            # Call Info
            "call_type": message_dict.get("call_type"),
            "data": message_dict.get("data"), # Dành cho Video/Audio frames
            # System Info
            "users": message_dict.get("users")
        }

        # 3. Gửi tin (Routing)
        if recipient:
            # --- CHAT RIÊNG ---
            # Gửi sang Web (Người nhận)
            if recipient in self.web_clients:
                try: await self.web_clients[recipient].send_json(payload)
                except: pass
            
            # Gửi sang Desktop (Người nhận)
            if recipient in self.tcp_clients:
                self._send_tcp_safe(recipient, msg_type, payload)
                
            # [QUAN TRỌNG] Đã XÓA đoạn gửi lại cho Sender để tránh lặp tin nhắn
        else:
            # --- CHAT NHÓM / BROADCAST ---
            await self.broadcast(payload, sender=sender)

    async def broadcast(self, payload, sender=None):
        """Gửi tin nhắn cho toàn bộ user online"""
        msg_type = payload.get("type")

        # 1. Gửi cho Web Clients (JSON)
        for user, ws in self.web_clients.items():
            if user == sender: continue
            try: await ws.send_json(payload)
            except: pass
            
        # 2. Gửi cho TCP Clients (Protocol Binary)
        # [QUAN TRỌNG] Xử lý chuyển đổi tin nhắn SYSTEM -> LIST_USERS
        tcp_msg_type = msg_type
        tcp_data = payload

        if msg_type == "SYSTEM":
            # Nếu Web gửi danh sách user, Desktop cần nhận loại LIST_USERS
            tcp_msg_type = MessageType.LIST_USERS
            tcp_data = {"users": payload.get("users", [])}
        elif msg_type == "VIDEO_FRAME":
            tcp_msg_type = MessageType.VIDEO_DATA

        for user, sock in self.tcp_clients.items():
            if user == sender: continue
            self._send_tcp_safe(user, tcp_msg_type, tcp_data)

    def _send_tcp_safe(self, username, msg_type, data):
        """Hàm phụ trợ để gửi TCP an toàn"""
        if username in self.tcp_clients:
            try:
                Protocol.send_message(self.tcp_clients[username], msg_type, data)
            except Exception as e:
                print(f"❌ Lỗi gửi TCP tới {username}: {e}")

global_bridge = BridgeManager()