"""
Xử lý file transfer (upload/download)
"""
import os
from datetime import datetime

from common.protocol import Protocol, MessageType
from common.config import CHUNK_SIZE

class FileHandler:
    def __init__(self, server):
        self.server = server
    
    def handle_file_upload(self, client_socket, username, data):
        """Xử lý upload file từ client"""
        try:
            filename = data.get("filename")
            filesize = data.get("filesize")
            file_type = data.get("file_type", "file")
            
            print(f"📤 Receiving {file_type}: {filename} ({filesize} bytes) from {username}")
            
            # Tạo đường dẫn lưu file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{filename}"
            filepath = os.path.join(self.server.storage_dir, safe_filename)
            
            # Gửi xác nhận sẵn sàng nhận
            Protocol.send_message(
                client_socket,
                MessageType.FILE_INFO,
                {"status": "ready"}
            )
            
            # Nhận file data
            received = 0
            with open(filepath, 'wb') as f:
                while received < filesize:
                    chunk_size = min(CHUNK_SIZE, filesize - received)
                    chunk = client_socket.recv(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)
            
            if received == filesize:
                print(f"✅ File received: {safe_filename}")
                
                # Gửi thông báo hoàn thành
                Protocol.send_message(
                    client_socket,
                    MessageType.FILE_COMPLETE,
                    {
                        "filename": safe_filename,
                        "original_filename": filename,
                        "filesize": filesize
                    }
                )
                
                # Broadcast thông báo file mới
                self.server.broadcast(
                    MessageType.FILE_INFO,
                    {
                        "sender": username,
                        "filename": safe_filename,
                        "original_filename": filename,
                        "filesize": filesize,
                        "file_type": file_type,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            else:
                Protocol.send_message(
                    client_socket,
                    MessageType.FILE_ERROR,
                    {"message": "File không nhận đủ dữ liệu"}
                )
        
        except Exception as e:
            print(f"❌ Error uploading file: {e}")
            Protocol.send_message(
                client_socket,
                MessageType.FILE_ERROR,
                {"message": str(e)}
            )
    
    def handle_file_download(self, client_socket, data):
        """Xử lý download file cho client"""
        try:
            filename = data.get("filename")
            filepath = os.path.join(self.server.storage_dir, filename)
            
            if not os.path.exists(filepath):
                Protocol.send_message(
                    client_socket,
                    MessageType.FILE_ERROR,
                    {"message": "File không tồn tại"}
                )
                return
            
            filesize = os.path.getsize(filepath)
            
            # Gửi thông tin file
            Protocol.send_message(
                client_socket,
                MessageType.FILE_INFO,
                {
                    "filename": filename,
                    "filesize": filesize,
                    "status": "sending"
                }
            )
            
            # Gửi file data
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    client_socket.sendall(chunk)
            
            print(f"📥 Sent file: {filename}")
        
        except Exception as e:
            print(f"❌ Error downloading file: {e}")
            Protocol.send_message(
                client_socket,
                MessageType.FILE_ERROR,
                {"message": str(e)}
            )