import os
from datetime import datetime

class ConsoleUI:
    def __init__(self, username):
        self.username = username
        self.users = []
    
    def clear_screen(self):
        """Xóa màn hình"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_header(self):
        """Hiển thị header"""
        print("="*70)
        print(f"CHAT CLIENT - Đăng nhập: {self.username}")
        print("="*70)
        self.show_users()
        print("="*70)
    
    def show_users(self):
        """Hiển thị danh sách user online"""
        if self.users:
            print(f"Online ({len(self.users)}): {', '.join(self.users)}")
        else:
            print("Online: Đang tải...")
    
    def update_user_list(self, users):
        """Cập nhật danh sách user"""
        self.users = users
    
    def show_message(self, sender, content, extra=""):
        """Hiển thị tin nhắn"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if sender == "SERVER" or sender == "ERROR":
            print(f"[{timestamp}] *** {content} ***")
        elif sender == "BẠN":
            if extra:
                print(f"[{timestamp}] {sender} {extra}: {content}")
            else:
                print(f"[{timestamp}] {sender}: {content}")
        else:
            if extra:
                print(f"[{timestamp}] {sender} {extra}: {content}")
            else:
                print(f"[{timestamp}] {sender}: {content}")
    
    def show_help(self):
        """Hiển thị hướng dẫn"""
        print("\n" + "="*70)
        print("HƯỚNG DẪN SỬ DỤNG:")
        print("-"*70)
        print("  Nhập tin nhắn và Enter             -> Gửi tin nhắn công khai")
        print("  @username tin nhắn                 -> Gửi tin nhắn riêng")
        print("  /file đường_dẫn_file               -> Gửi file")
        print("  /users                             -> Hiển thị danh sách user")
        print("  /help                              -> Hiển thị hướng dẫn")
        print("  /clear                             -> Xóa màn hình")
        print("  /quit hoặc /exit                   -> Thoát")
        print("="*70 + "\n")
    
    def get_input(self):
        """Nhận input từ user"""
        try:
            return input(">>> ")
        except EOFError:
            return "/quit"
        except KeyboardInterrupt:
            return "/quit"
    
    def show_error(self, message):
        """Hiển thị lỗi"""
        print(f"\n[ERROR] {message}\n")