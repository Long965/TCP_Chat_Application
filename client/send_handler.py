import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.protocol import Protocol, MessageType
from file_handler import FileHandler

class SendHandler:
    def __init__(self, client_socket, username):
        self.client_socket = client_socket
        self.username = username
    
    def send_message(self, message):
        """Gửi tin nhắn thông thường"""
        try:
            msg = Protocol.encode_message(
                MessageType.TEXT, self.username, message
            )
            self.client_socket.send(msg)
            return True
        except Exception as e:
            return False
    
    def send_private_message(self, target_user, message):
        """Gửi tin nhắn riêng"""
        try:
            msg = Protocol.encode_message(
                MessageType.PRIVATE, self.username, message, target_user
            )
            self.client_socket.send(msg)
            return True
        except Exception as e:
            return False
    
    def send_file(self, filepath):
        """Gửi file"""
        success, result = FileHandler.send_file(self.client_socket, filepath)
        return success, result
    
