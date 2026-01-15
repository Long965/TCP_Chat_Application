"""
Protocol cho ứng dụng chat - Định nghĩa cấu trúc message
"""

import json
import struct

class MessageType:
    """Các loại message"""
    # Authentication
    LOGIN = "LOGIN"
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    
    # Text messages
    TEXT = "TEXT"
    
    # File transfer
    FILE_UPLOAD = "FILE_UPLOAD"
    FILE_DOWNLOAD = "FILE_DOWNLOAD"
    FILE_INFO = "FILE_INFO"
    FILE_CHUNK = "FILE_CHUNK"
    FILE_COMPLETE = "FILE_COMPLETE"
    FILE_ERROR = "FILE_ERROR"
    
    # User management
    USER_LIST = "USER_LIST"
    USER_ONLINE = "USER_ONLINE"
    USER_OFFLINE = "USER_OFFLINE"
    
    # System
    PING = "PING"
    PONG = "PONG"
    ERROR = "ERROR"

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
            print(f"Error receiving message: {e}")
            return None, None
    
    @staticmethod
    def _recv_exact(sock, n):
        """Nhận chính xác n bytes từ socket"""
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
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