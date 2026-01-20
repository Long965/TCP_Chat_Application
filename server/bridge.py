"""
server/bridge.py - Bridge quản lý kết nối Hybrid + Hỗ trợ Upload Stream
"""
from fastapi import WebSocket, WebSocketDisconnect
from common.protocol import Protocol, MessageType
from common.config import SERVER_STORAGE_DIR
import asyncio
import json
import os
from datetime import datetime

class BridgeManager:
    def __init__(self):
        self.tcp_clients = {}  # {username: socket}
        self.web_clients = {}  # {username: websocket}
        
        # Lưu trạng thái upload của từng user
        self.active_uploads = {} # {username: {file_handle, filename, total, received, recipient}}

        if not os.path.exists(SERVER_STORAGE_DIR):
            os.makedirs(SERVER_STORAGE_DIR)

    def add_tcp(self, username, socket):
        if username in self.tcp_clients:
            print(f"🔄 [Bridge] Kick old TCP: {username}")
            try: self.tcp_clients[username].close()
            except: pass
        self.tcp_clients[username] = socket
        print(f"✅ [Bridge] TCP User added: {username}")

    async def add_web(self, username, websocket: WebSocket):
        await websocket.accept()
        if username in self.web_clients:
            print(f"🔄 [Bridge] Kick old Web: {username}")
            try: await self.web_clients[username].close()
            except: pass
        self.web_clients[username] = websocket
        print(f"✅ [Bridge] Web User added: {username}")

    async def remove_web(self, username):
        if username in self.web_clients:
            del self.web_clients[username]
        # Xóa file rác nếu đang upload dở
        if username in self.active_uploads:
            try:
                self.active_uploads[username]["file_handle"].close()
            except: pass
            del self.active_uploads[username]
        print(f"👋 [Bridge] Web User removed: {username}")

    def remove_tcp(self, username):
        if username in self.tcp_clients:
            del self.tcp_clients[username]
        print(f"👋 [Bridge] TCP User removed: {username}")

    # --- MAIN LOOP CHO WEB CLIENT (Xử lý Text & Bytes) ---
    async def listen_to_web_user(self, username):
        websocket = self.web_clients.get(username)
        if not websocket: return

        try:
            while True:
                # [QUAN TRỌNG] Nhận raw message (có thể là text hoặc bytes)
                message = await websocket.receive()

                # 1. Xử lý TEXT (JSON Commands)
                if "text" in message and message["text"]:
                    try:
                        data = json.loads(message["text"])
                        msg_type = data.get("type")

                        if msg_type == "FILE_UPLOAD_START":
                            # Bắt đầu phiên upload mới
                            meta = data.get("data")
                            filename = meta["filename"]
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            safe_filename = f"{timestamp}_{filename}"
                            filepath = os.path.join(SERVER_STORAGE_DIR, safe_filename)
                            
                            self.active_uploads[username] = {
                                "file_handle": open(filepath, "wb"),
                                "total": meta["filesize"],
                                "received": 0,
                                "filename": safe_filename,
                                "original_filename": filename,
                                "recipient": meta["recipient"]
                            }
                            print(f"🌍 Web Upload Start: {filename} from {username}")

                        elif msg_type == "FILE_UPLOAD_CANCEL":
                            if username in self.active_uploads:
                                self.active_uploads[username]["file_handle"].close()
                                del self.active_uploads[username]
                                print(f"🌍 Web Upload Cancelled: {username}")

                        else:
                            # Tin nhắn chat thường -> Router
                            await self.handle_message(data, sender=username)

                    except json.JSONDecodeError:
                        pass

                # 2. Xử lý BYTES (File Chunk)
                elif "bytes" in message and message["bytes"]:
                    chunk = message["bytes"]
                    if username in self.active_uploads:
                        upload = self.active_uploads[username]
                        upload["file_handle"].write(chunk)
                        upload["received"] += len(chunk)

                        # Kiểm tra hoàn thành
                        if upload["received"] >= upload["total"]:
                            upload["file_handle"].close()
                            print(f"✅ Web Upload Complete: {upload['filename']}")
                            
                            # Tạo tin nhắn FILE_INFO để broadcast
                            file_info = {
                                "type": "FILE_INFO",
                                "sender": username,
                                "recipient": upload["recipient"],
                                "filename": upload["filename"],
                                "original_filename": upload["original_filename"],
                                "filesize": upload["total"],
                                "file_type": "file",
                                "timestamp": datetime.now().isoformat()
                            }
                            
                            # Clean up
                            del self.active_uploads[username]

                            # Gửi lại cho chính mình (để hiện bong bóng)
                            await self.send_to_user_web(username, file_info)
                            # Gửi cho người nhận
                            await self.handle_message(file_info, sender=username)

        except WebSocketDisconnect:
            await self.remove_web(username)
        except Exception as e:
            # print(f"❌ Web Error {username}: {e}")
            await self.remove_web(username)

    async def send_to_user_web(self, username, payload):
        if username in self.web_clients:
            try: await self.web_clients[username].send_json(payload)
            except: pass

    async def handle_message(self, message_dict, sender=None):
        """Định tuyến tin nhắn"""
        msg_type = message_dict.get("type", "TEXT")
        recipient = message_dict.get("recipient")
        
        # Payload chuẩn
        payload = {
            "type": msg_type,
            "sender": sender,
            "recipient": recipient,
            "message": message_dict.get("message") or message_dict.get("content"),
            "content": message_dict.get("message") or message_dict.get("content"),
            "timestamp": message_dict.get("timestamp"),
            "filename": message_dict.get("filename"),
            "original_filename": message_dict.get("original_filename"),
            "filesize": message_dict.get("filesize"),
            "file_type": message_dict.get("file_type"),
            "users": message_dict.get("users")
        }

        # 1. Chat Riêng
        if recipient:
            if recipient in self.web_clients:
                try: await self.web_clients[recipient].send_json(payload)
                except: pass
            
            if recipient in self.tcp_clients:
                self._send_tcp_safe(recipient, msg_type, payload)

        # 2. Broadcast
        else:
            await self.broadcast(payload, sender=sender)

    async def broadcast(self, payload, sender=None):
        msg_type = payload.get("type")

        # Gửi Web
        for user, ws in self.web_clients.items():
            if user == sender: continue
            try: await ws.send_json(payload)
            except: pass
            
        # Gửi TCP
        tcp_msg_type = msg_type
        if msg_type == "SYSTEM": tcp_msg_type = MessageType.LIST_USERS
        
        for user, sock in self.tcp_clients.items():
            if user == sender: continue
            self._send_tcp_safe(user, tcp_msg_type, payload)

    def _send_tcp_safe(self, username, msg_type, data):
        if username in self.tcp_clients:
            try: Protocol.send_message(self.tcp_clients[username], msg_type, data)
            except: pass

global_bridge = BridgeManager()