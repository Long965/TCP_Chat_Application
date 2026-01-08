import json

class MessageType:
    TEXT = "TEXT"
    FILE = "FILE"
    FILE_CHUNK = "FILE_CHUNK"
    JOIN = "JOIN"
    LEAVE = "LEAVE"
    USER_LIST = "USER_LIST"
    PRIVATE = "PRIVATE"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"

class Protocol:
    SEPARATOR = "|"
    ENCODING = "utf-8"
    BUFFER_SIZE = 4096
    FILE_BUFFER = 8192
    
    @staticmethod
    def encode_message(msg_type, sender, content, extra=""):
        """Mã hóa message thành chuỗi theo protocol"""
        msg = f"{msg_type}{Protocol.SEPARATOR}{sender}{Protocol.SEPARATOR}{content}"
        if extra:
            msg += f"{Protocol.SEPARATOR}{extra}"
        return msg.encode(Protocol.ENCODING)
    
    @staticmethod
    def decode_message(data):
        """Giải mã message từ bytes"""
        try:
            msg = data.decode(Protocol.ENCODING)
            parts = msg.split(Protocol.SEPARATOR)
            
            result = {
                "type": parts[0] if len(parts) > 0 else "",
                "sender": parts[1] if len(parts) > 1 else "",
                "content": parts[2] if len(parts) > 2 else "",
                "extra": parts[3] if len(parts) > 3 else ""
            }
            return result
        except Exception as e:
            return {"type": MessageType.ERROR, "content": str(e)}
    
    @staticmethod
    def encode_file_info(filename, filesize):
        """Mã hóa thông tin file"""
        return json.dumps({"filename": filename, "filesize": filesize})
    
    @staticmethod
    def decode_file_info(data):
        """Giải mã thông tin file"""
        return json.loads(data)