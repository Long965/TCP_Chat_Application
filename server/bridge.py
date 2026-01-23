"""
server/bridge.py - Bridge quản lý kết nối Hybrid + Hỗ trợ Upload & Download Stream
(Phiên bản Fix lỗi 404 & Thêm Rate Limiting)
"""
from fastapi import WebSocket, WebSocketDisconnect
from common.protocol import Protocol, MessageType
from common.config import SERVER_STORAGE_DIR
import asyncio
import json
import os
import time  # [ADDED]
from datetime import datetime

# [ADDED] Cấu hình giới hạn tốc độ (50KB/s để test)
DOWNLOAD_SPEED_LIMIT = 50 * 1024  
DOWNLOAD_CHUNK_SIZE = 8192 * 4 

class BridgeManager:
    def __init__(self):
        self.tcp_clients = {}    # {username: socket}
        self.web_clients = {}    # {username: websocket} (User Chat Chính)
        self.upload_clients = {} # {username: websocket} (User Upload/Download Ẩn)
        
        self.active_uploads = {} # {username: {file_handle, filename, ...}}

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
        
        # [UPDATED] Hỗ trợ cả _upload_ và _download_
        if "_upload_" in username or "_download_" in username:
            self.upload_clients[username] = websocket
            # print(f"🔌 [Bridge] Ghost connection added: {username}")
            return 

        if username in self.web_clients:
            print(f"🔄 [Bridge] Kick old Web: {username}")
            try: await self.web_clients[username].close()
            except: pass
        self.web_clients[username] = websocket
        print(f"✅ [Bridge] Web User added: {username}")

    async def remove_web(self, username):
        # [UPDATED] Kiểm tra cả upload và download
        if "_upload_" in username or "_download_" in username:
            if username in self.upload_clients:
                del self.upload_clients[username]
        elif username in self.web_clients:
            del self.web_clients[username]
            print(f"👋 [Bridge] Web User removed: {username}")

        if username in self.active_uploads:
            try: self.active_uploads[username]["file_handle"].close()
            except: pass
            del self.active_uploads[username]

    def remove_tcp(self, username):
        if username in self.tcp_clients:
            del self.tcp_clients[username]
        print(f"👋 [Bridge] TCP User removed: {username}")

    # --- MAIN LOOP CHO WEB CLIENT ---
    async def listen_to_web_user(self, username):
        websocket = self.web_clients.get(username) or self.upload_clients.get(username)
        
        if not websocket:
            print(f"⚠️ [Bridge] Listen failed: No socket for {username}")
            return

        try:
            while True:
                message = await websocket.receive()

                # 1. TEXT (JSON)
                if "text" in message and message["text"]:
                    try:
                        data = json.loads(message["text"])
                        msg_type = data.get("type")

                        if msg_type == "FILE_UPLOAD_START":
                            meta = data.get("data")
                            
                            # [FIX 404] Tin tưởng tên file từ Client
                            safe_filename = meta["filename"] 
                            original_filename = meta.get("original_filename", safe_filename)

                            filepath = os.path.join(SERVER_STORAGE_DIR, safe_filename)
                            
                            self.active_uploads[username] = {
                                "file_handle": open(filepath, "wb"),
                                "total": meta["filesize"],
                                "received": 0,
                                "filename": safe_filename,
                                "original_filename": original_filename,
                                "recipient": meta["recipient"]
                            }
                            print(f"🌍 Web Upload Start: {safe_filename}")

                        elif msg_type == "FILE_UPLOAD_CANCEL":
                            if username in self.active_uploads:
                                self.active_uploads[username]["file_handle"].close()
                                del self.active_uploads[username]
                                print(f"❌ Web Upload Cancelled: {username}")

                        # [ADDED] DOWNLOAD VỚI RATE LIMIT
                        elif msg_type == "FILE_DOWNLOAD_REQUEST":
                            meta = data.get("data")
                            filename = meta["filename"]
                            offset = meta.get("offset", 0)
                            filepath = os.path.join(SERVER_STORAGE_DIR, filename)

                            if os.path.exists(filepath):
                                print(f"⬇️ Download Start: {filename} (Offset: {offset})")
                                
                                with open(filepath, "rb") as f:
                                    f.seek(offset)
                                    while True:
                                        start_time = time.time() # Bấm giờ

                                        chunk = f.read(DOWNLOAD_CHUNK_SIZE) 
                                        if not chunk: break 
                                        
                                        await websocket.send_bytes(chunk)
                                        
                                        # Rate Limiting Logic
                                        elapsed = time.time() - start_time
                                        expected = len(chunk) / DOWNLOAD_SPEED_LIMIT
                                        if elapsed < expected:
                                            await asyncio.sleep(expected - elapsed)
                                        else:
                                            await asyncio.sleep(0)
                                    
                                    await websocket.send_json({"type": "DOWNLOAD_COMPLETE", "filename": filename})
                            else:
                                await websocket.send_json({"type": "ERROR", "message": "File not found"})

                        else:
                            await self.handle_message(data, sender=username)

                    except json.JSONDecodeError:
                        print(f"⚠️ JSON Error from {username}: {message['text']}")
                    except Exception as e:
                        print(f"❌ Error handling TEXT from {username}: {e}")

                # 2. BYTES (Upload Incoming)
                elif "bytes" in message and message["bytes"]:
                    if username in self.active_uploads:
                        chunk = message["bytes"]
                        upload = self.active_uploads[username]
                        upload["file_handle"].write(chunk)
                        upload["received"] += len(chunk)

                        if upload["received"] >= upload["total"]:
                            upload["file_handle"].close()
                            print(f"✅ Web Upload Complete: {upload['filename']}")
                            del self.active_uploads[username]

        except WebSocketDisconnect:
            await self.remove_web(username)
        except Exception as e:
            # print(f"🔥 Critical Web Error {username}: {e}")
            await self.remove_web(username)

    # Trong server/bridge.py

    async def handle_message(self, message_dict, sender=None):
        try:
            raw_type = message_dict.get("type")
            recipient = message_dict.get("recipient")
            
            # Chuẩn hóa msg_type
            str_type = str(raw_type).upper()
            if "FILE" in str_type: msg_type = "FILE_INFO"
            elif "CALL" in str_type: msg_type = raw_type
            elif "SYSTEM" in str_type: msg_type = "SYSTEM"
            else: msg_type = "TEXT"

            # Xử lý trường hợp recipient rỗng
            if recipient == "": recipient = None

            # Tạo payload chuẩn để gửi đi
            payload = {
                "type": msg_type,
                "sender": sender,
                "recipient": recipient,
                "message": message_dict.get("message") or message_dict.get("content"),
                "content": message_dict.get("message") or message_dict.get("content"),
                "timestamp": message_dict.get("timestamp") or datetime.now().isoformat(),
                "filename": message_dict.get("filename"),
                "original_filename": message_dict.get("original_filename"),
                "filesize": message_dict.get("filesize"),
                "file_type": message_dict.get("file_type"),
                "users": message_dict.get("users")
            }

            # --- LOGIC XỬ LÝ ĐỊNH TUYẾN ---
            if recipient:
                print(f"🔒 [Bridge] Private Chat: {sender} -> {recipient}")
                
                received = False
                
                # 1. Gửi cho người nhận là Web Client
                if recipient in self.web_clients:
                    try: 
                        await self.web_clients[recipient].send_json(payload)
                        received = True
                    except: pass
                
                # 2. Gửi cho người nhận là Desktop (TCP) Client
                if recipient in self.tcp_clients:
                    self._send_tcp_safe(recipient, raw_type, payload)
                    received = True

                if not received:
                    print(f"⚠️ Không tìm thấy người nhận: {recipient}")

                # [QUAN TRỌNG - SỬA LỖI TRÙNG LẶP]
                # Đã vô hiệu hóa phần gửi ngược lại cho Sender để tránh hiện 2 lần ở Client.
                # (Vì Client Desktop đã tự hiển thị tin nhắn ngay khi bấm gửi)
                
                # if sender in self.tcp_clients:
                #    self._send_tcp_safe(sender, raw_type, payload)

            else:
                # Chat nhóm (Broadcast) - Gửi cho tất cả trừ người gửi
                await self.broadcast(payload, sender=sender, original_type=raw_type)

        except Exception as e:
            print(f"❌ Handle Message Error: {e}")

    async def broadcast(self, payload, sender=None, original_type=None):
        # ... (Giữ nguyên logic cũ của bạn) ...
        for user, ws in self.web_clients.items():
            if user == sender: continue
            try: await ws.send_json(payload)
            except: pass
        tcp_msg_type = original_type if original_type else payload.get("type")
        if payload.get("type") == "SYSTEM": tcp_msg_type = MessageType.LIST_USERS
        for user, sock in self.tcp_clients.items():
            if user == sender: continue
            self._send_tcp_safe(user, tcp_msg_type, payload)

    def _send_tcp_safe(self, username, msg_type, data):
        # ... (Giữ nguyên logic cũ của bạn) ...
        if username in self.tcp_clients:
            try: Protocol.send_message(self.tcp_clients[username], msg_type, data)
            except: pass

global_bridge = BridgeManager()