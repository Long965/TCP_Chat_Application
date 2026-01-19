import os
import json
from datetime import datetime
from common.protocol import Protocol, MessageType


class FileHandler:
    def __init__(self, server):
        self.server = server
        self.upload_dir = "uploads"

        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    def handle_file(self, client_socket, data):
        """
        Xử lý file gửi từ client:
        - Lưu file
        - Gửi FILE_INFO cho cả người gửi và người nhận
        """

        try:
            sender = data.get("sender")
            recipient = data.get("recipient")
            filename = data.get("filename")
            filedata = data.get("filedata")  # base64
            filesize = data.get("filesize")

            if not all([sender, recipient, filename, filedata]):
                print("❌ Thiếu dữ liệu file")
                return

            # Tạo tên file an toàn
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{filename}"
            file_path = os.path.join(self.upload_dir, safe_filename)

            # Decode base64 và lưu file
            file_bytes = Protocol.decode_base64(filedata)
            with open(file_path, "wb") as f:
                f.write(file_bytes)

            print(f"📁 File nhận từ {sender}: {filename} ({filesize} bytes)")

            # Gói thông tin file để gửi cho client
            file_info = {
                "sender": sender,
                "recipient": recipient,
                "filename": safe_filename,
                "original_filename": filename,
                "filesize": filesize,
                "timestamp": datetime.now().isoformat()
            }

            # ===============================
            # 1️⃣ GỬI CHO NGƯỜI NHẬN
            # ===============================
            if recipient in self.server.clients:
                Protocol.send_message(
                    self.server.clients[recipient],
                    MessageType.FILE_INFO,
                    file_info
                )
                print(f"📤 Đã gửi FILE_INFO cho {recipient}")

            # ===============================
            # 2️⃣ GỬI LẠI CHO NGƯỜI GỬI (QUAN TRỌNG)
            # ===============================
            Protocol.send_message(
                client_socket,
                MessageType.FILE_INFO,
                file_info
            )
            print(f"📤 Đã gửi FILE_INFO lại cho {sender}")

        except Exception as e:
            print(f"❌ Lỗi xử lý file: {e}")
