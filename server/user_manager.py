import threading

class UserManager:
    def __init__(self):
        self.users = {}  # {username: socket}
        self.lock = threading.Lock()
    
    def add_user(self, username, client_socket):
        """Thêm user vào danh sách"""
        with self.lock:
            if username in self.users:
                return False
            self.users[username] = client_socket
            return True
    
    def remove_user(self, username):
        """Xóa user khỏi danh sách"""
        with self.lock:
            if username in self.users:
                del self.users[username]
                return True
            return False
    
    def get_user_socket(self, username):
        """Lấy socket của user"""
        with self.lock:
            return self.users.get(username)
    
    def get_all_users(self):
        """Lấy danh sách tất cả user"""
        with self.lock:
            return list(self.users.keys())
    
    def get_username_by_socket(self, client_socket):
        """Tìm username theo socket"""
        with self.lock:
            for username, sock in self.users.items():
                if sock == client_socket:
                    return username
            return None
    
    def broadcast_message(self, message, exclude_socket=None):
        """Gửi message tới tất cả user (trừ exclude_socket)"""
        with self.lock:
            disconnected = []
            for username, sock in self.users.items():
                if sock != exclude_socket:
                    try:
                        sock.send(message)
                    except:
                        disconnected.append(username)
            
            # Xóa các user bị disconnect
            for username in disconnected:
                del self.users[username]