import os
import asyncio
from datetime import datetime
from common.protocol import Protocol, MessageType
from common.config import CHUNK_SIZE

class FileHandler:
    def __init__(self, server):
        self.server = server
        # Đảm bảo thư mục lưu trữ file tồn tại
        if not os.path.exists(self.server.storage_dir):
            os.makedirs(self.server.storage_dir)

    def handle_file_upload(self, client_socket, username, data):
        """
        Xử lý upload file theo dạng STREAM (nhận từng chunk).
        Hỗ trợ Client Pause/Resume và hiển thị Progress Bar.
        """
        try:
            # 1. Đọc Metadata từ Header (Client đã gửi JSON trước đó)
            filename = data.get("filename")
            filesize = data.get("filesize")
            file_type = data.get("file_type", "file")
            recipient = data.get("recipient")

            print(f"📤 [Server] Bắt đầu nhận file Stream: {filename} ({filesize} bytes) từ {username}")

            # 2. Tạo đường dẫn lưu file (Thêm timestamp để tránh trùng tên)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{filename}"
            filepath = os.path.join(self.server.storage_dir, safe_filename)

            # 3. Vòng lặp nhận dữ liệu Raw (Binary)
            received = 0
            with open(filepath, 'wb') as f:
                while received < filesize:
                    # Tính toán lượng byte cần đọc còn lại
                    remaining = filesize - received
                    read_size = min(CHUNK_SIZE, remaining)
                    
                    # Đọc từ socket
                    chunk = client_socket.recv(read_size)
                    if not chunk:
                        raise Exception("Client ngắt kết nối đột ngột khi đang gửi file")
                    
                    f.write(chunk)
                    received += len(chunk)

            print(f"✅ [Server] Đã nhận xong file: {safe_filename}")

            # 4. Tạo gói tin thông báo hoàn thành
            file_info_msg = {
                "type": "FILE_INFO",
                "sender": username,
                "recipient": recipient,
                "filename": safe_filename,       # Tên file trên server (để tải về)
                "original_filename": filename,   # Tên gốc (để hiển thị)
                "filesize": filesize,
                "file_type": file_type,
                "timestamp": datetime.now().isoformat()
            }

            # ==================================================================
            # [QUAN TRỌNG] GỬI PHẢN HỒI LẠI CHO NGƯỜI GỬI (SENDER)
            # ==================================================================
            # Giúp Client Sender vẽ bong bóng file vào khung chat của chính mình
            try:
                Protocol.send_message(client_socket, MessageType.FILE_INFO, file_info_msg)
            except Exception as e:
                print(f"⚠️ Lỗi gửi phản hồi cho sender: {e}")

            # ==================================================================
            # 5. CHUYỂN TIẾP CHO NGƯỜI NHẬN (QUA BRIDGE)
            # ==================================================================
            # Sử dụng Bridge để gửi cho cả Web Client và Desktop Client khác
            from server.bridge import global_bridge
            
            # Vì function này chạy trong Thread TCP, cần gọi async thread-safe để tương tác với Event Loop chính
            if self.server.main_loop and self.server.main_loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    global_bridge.handle_message(file_info_msg, sender=username),
                    self.server.main_loop
                )
            else:
                # Fallback: Nếu không chạy mode Hybrid, dùng Broadcast thường
                print("⚠️ Warning: Main loop not running, broadcasting via TCP only")
                self.server.broadcast(MessageType.FILE_INFO, file_info_msg)

        except Exception as e:
            print(f"❌ Lỗi khi nhận file stream: {e}")
            # Gửi thông báo lỗi lại cho client để họ biết
            try:
                Protocol.send_message(client_socket, MessageType.ERROR, {"message": f"Upload thất bại: {str(e)}"})
            except: pass

    def handle_file_download(self, client_socket, data):
        """
        Xử lý yêu cầu tải file.
        Lưu ý: Client Desktop hiện tại tải file qua HTTP (FastAPI Static), 
        nên hàm này chỉ mang tính chất log hoặc mở rộng sau này.
        """
        try:
            filename = data.get("filename")
            print(f"ℹ️ [Server] Client {client_socket.getpeername()} yêu cầu tải file: {filename}")
            
            filepath = os.path.join(self.server.storage_dir, filename)
            if not os.path.exists(filepath):
                 Protocol.send_message(client_socket, MessageType.ERROR, {"message": "File không tồn tại trên server"})
                 return
            
            # Nếu muốn chuyển sang tải qua TCP Socket thay vì HTTP, code sẽ viết ở đây.
            
        except Exception as e:
            print(f"❌ Download error: {e}")