"""
Xử lý gửi và nhận file trên client
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.protocol import Protocol, MessageType
import config

class FileHandler:
    @staticmethod
    def send_file(client_socket, filepath, progress_callback=None):
        """Gửi file tới server với progress callback"""
        try:
            if not os.path.exists(filepath):
                return False, "File không tồn tại!"
            
            filesize = os.path.getsize(filepath)
            filename = os.path.basename(filepath)
            
            # Kiểm tra kích thước file
            if filesize > config.MAX_FILE_SIZE:
                return False, f"File quá lớn! (Max: {config.MAX_FILE_SIZE/1024/1024}MB)"
            
            # Gửi thông tin file
            file_info = Protocol.encode_file_info(filename, filesize)
            msg = Protocol.encode_message(MessageType.FILE, "", file_info)
            client_socket.send(msg)
            
            # Đợi ACK từ server
            ack = client_socket.recv(config.BUFFER_SIZE)
            ack_msg = Protocol.decode_message(ack)
            
            if ack_msg["type"] != MessageType.SUCCESS:
                return False, "Server không chấp nhận file"
            
            # Gửi nội dung file
            with open(filepath, 'rb') as f:
                sent = 0
                while sent < filesize:
                    chunk = f.read(config.FILE_BUFFER)
                    if not chunk:
                        break
                    client_socket.sendall(chunk)  # Dùng sendall thay vì send
                    sent += len(chunk)
                    
                    # Callback progress
                    if progress_callback:
                        progress = (sent / filesize) * 100
                        progress_callback(progress)
                    else:
                        # Hiển thị tiến trình trong console
                        progress = (sent / filesize) * 100
                        print(f"\rĐang gửi: {progress:.1f}%", end="", flush=True)
            
            if not progress_callback:
                print()  # Xuống dòng
            
            return True, f"Đã gửi {filename} ({sent} bytes)"
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def receive_file(client_socket, filename, filesize):
        """Nhận file từ server"""
        try:
            # Tạo thư mục nếu chưa có
            os.makedirs(config.CLIENT_DOWNLOADS, exist_ok=True)
            
            filepath = os.path.join(config.CLIENT_DOWNLOADS, filename)
            received = 0
            
            with open(filepath, 'wb') as f:
                while received < filesize:
                    chunk_size = min(config.FILE_BUFFER, filesize - received)
                    data = client_socket.recv(chunk_size)
                    if not data:
                        break
                    f.write(data)
                    received += len(data)
                    
                    # Hiển thị tiến trình
                    progress = (received / filesize) * 100
                    print(f"\rĐang nhận: {progress:.1f}%", end="", flush=True)
            
            print()  # Xuống dòng
            
            if received == filesize:
                return True, filepath
            else:
                return False, "File không nhận đủ dữ liệu"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def is_image(filename):
        """Kiểm tra file có phải ảnh không"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        ext = os.path.splitext(filename)[1].lower()
        return ext in image_extensions
    
    @staticmethod
    def is_video(filename):
        """Kiểm tra file có phải video không"""
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
        ext = os.path.splitext(filename)[1].lower()
        return ext in video_extensions