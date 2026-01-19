"""
Protocol cho ứng dụng chat - Định nghĩa cấu trúc message (FULL)
"""

import json
import struct

class MessageType:
    """Các loại message"""
    # Authentication
    LOGIN = "LOGIN"
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    
    # Text messages
    TEXT = "TEXT"
    PRIVATE_TEXT = "PRIVATE_TEXT"
    
    # File transfer (Đã bổ sung đầy đủ)
    FILE_UPLOAD = "FILE_UPLOAD"
    FILE_DOWNLOAD = "FILE_DOWNLOAD"
    FILE_INFO = "FILE_INFO"
    FILE_DATA = "FILE_DATA"
    FILE_CHUNK = "FILE_CHUNK"      
    FILE_COMPLETE = "FILE_COMPLETE" # <--- Đã thêm biến này để sửa lỗi
    FILE_ERROR = "FILE_ERROR"       # <--- Thêm luôn biến này cho chắc
    
    # User management
    LIST_USERS = "LIST_USERS"
    USER_INFO = "USER_INFO"
    
    # Video/Audio Call
    CALL_REQUEST = "CALL_REQUEST"
    CALL_ACCEPT = "CALL_ACCEPT"
    CALL_REJECT = "CALL_REJECT"
    CALL_END = "CALL_END"
    CALL_BUSY = "CALL_BUSY"
    
    # Media Data
    VIDEO_DATA = "VIDEO_DATA"
    AUDIO_DATA = "AUDIO_DATA"
    
    # System
    ERROR = "ERROR"
    PING = "PING"
    PONG = "PONG"

class Protocol:
    """Xử lý encode/decode message"""
    
    HEADER_SIZE = 4  # 4 bytes cho message length
    ENCODING = "utf-8"
    
    @staticmethod
    def encode_message(msg_type, data):
        """
        Encode message thành bytes
        Format: [4 bytes length][JSON data]
        """
        message = {
            "type": msg_type,
            "data": data
        }
        
        # ensure_ascii=False để hỗ trợ tiếng Việt
        json_str = json.dumps(message, ensure_ascii=False)
        json_bytes = json_str.encode(Protocol.ENCODING)
        
        # Thêm header chứa độ dài message
        length = len(json_bytes)
        header = struct.pack(">I", length)  # Big-endian unsigned int
        
        return header + json_bytes
    
    @staticmethod
    def decode_message(data):
        """
        Decode message từ bytes
        Returns: (msg_type, data)
        """
        try:
            json_str = data.decode(Protocol.ENCODING)
            message = json.loads(json_str)
            return message["type"], message["data"]
        except Exception as e:
            return MessageType.ERROR, str(e)
    
    @staticmethod
    def recv_message(sock):
        """
        Nhận message hoàn chỉnh từ socket
        Returns: (msg_type, data) hoặc (None, None) nếu disconnect
        """
        try:
            # Đọc header (4 bytes)
            header = Protocol._recv_exact(sock, Protocol.HEADER_SIZE)
            if not header:
                return None, None
            
            # Giải mã độ dài message
            msg_length = struct.unpack(">I", header)[0]
            
            # Đọc message data
            msg_data = Protocol._recv_exact(sock, msg_length)
            if not msg_data:
                return None, None
            
            # Decode message
            return Protocol.decode_message(msg_data)
            
        except Exception as e:
            return None, None
    
    @staticmethod
    def _recv_exact(sock, n):
        """Nhận chính xác n bytes từ socket"""
        data = bytearray()
        while len(data) < n:
            try:
                packet = sock.recv(n - len(data))
                if not packet:
                    return None
                data.extend(packet)
            except:
                return None
        return bytes(data)
    
    @staticmethod
    def send_message(sock, msg_type, data):
        """Gửi message qua socket"""
        try:
            message = Protocol.encode_message(msg_type, data)
            sock.sendall(message)
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            return False