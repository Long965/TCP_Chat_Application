import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.protocol import Protocol, MessageType
import config

class FileHandler:
    @staticmethod
    def receive_file(client_socket, filename, filesize):
        """Nhận file từ client"""
        try:
            # Tạo thư mục nếu chưa có
            os.makedirs(config.SERVER_STORAGE, exist_ok=True)
            
            filepath = os.path.join(config.SERVER_STORAGE, filename)
            received = 0
            
            with open(filepath, 'wb') as f:
                while received < filesize:
                    chunk_size = min(config.FILE_BUFFER, filesize - received)
                    data = client_socket.recv(chunk_size)
                    if not data:
                        break
                    f.write(data)
                    received += len(data)
            
            if received == filesize:
                return True, filepath
            else:
                return False, "File không nhận đủ dữ liệu"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def send_file(client_socket, filepath):
        """Gửi file tới client"""
        try:
            filesize = os.path.getsize(filepath)
            filename = os.path.basename(filepath)
            
            # Gửi thông tin file
            file_info = Protocol.encode_file_info(filename, filesize)
            msg = Protocol.encode_message(MessageType.FILE, "SERVER", file_info)
            client_socket.send(msg)
            
            # Đợi xác nhận
            ack = client_socket.recv(config.BUFFER_SIZE)
            
            # Gửi nội dung file
            with open(filepath, 'rb') as f:
                sent = 0
                while sent < filesize:
                    chunk = f.read(config.FILE_BUFFER)
                    if not chunk:
                        break
                    client_socket.send(chunk)
                    sent += len(chunk)