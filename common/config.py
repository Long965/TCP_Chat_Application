"""
common/config.py - Cấu hình Blue/White Theme (Telegram-like) [FIXED]
"""

# Server settings
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5555
DEFAULT_SERVER = "127.0.0.1:5555"

# Directory settings
CLIENT_DOWNLOAD_DIR = "client_downloads"
SERVER_STORAGE_DIR = "server_files"

# Network settings
CHUNK_SIZE = 8192
SOCKET_TIMEOUT = 5
UPLOAD_TIMEOUT = 10

class Colors:
    # --- BLUE & WHITE PALETTE (Dựa theo ảnh mẫu) ---
    BG_MAIN = "#FFFFFF"         # Nền chính: Trắng
    BG_SIDEBAR = "#FFFFFF"      # Nền danh sách chat: Trắng
    BG_SIDEBAR_HEADER = "#0078D7" # Nền tiêu đề "Chats": Xanh dương đậm
    
    # Màu tin nhắn
    MSG_SENT = "#0078D7"        # Tin gửi đi: Nền xanh (Chữ trắng)
    MSG_RECV = "#F2F2F2"        # Tin nhận: Nền xám nhạt (Chữ đen)

    # Màu chữ
    TEXT_PRIMARY = "#000000"    # Chữ đen
    TEXT_WHITE = "#FFFFFF"      # Chữ trắng (dùng cho header/button)
    TEXT_SECONDARY = "#888888"  # Màu timestamp
    
    # Màu tương tác
    ACCENT = "#0078D7"          # Màu nút Send, Icon
    BG_HOVER = "#E5F3FF"        # Màu khi di chuột vào user (Xanh rất nhạt)
    INPUT_BG = "#FFFFFF"        # Nền ô nhập liệu
    
    # Viền
    BORDER = "#D9D9D9"          # Viền xám nhẹ
    BORDER_LIGHT = "#E0E0E0"    # [FIX] Thêm biến này để LoginUI không bị lỗi

    # --- Backward Compatibility ---
    PRIMARY = ACCENT
    BG_PRIMARY = BG_MAIN
    BG_SECONDARY = BG_SIDEBAR
    TEXT_LIGHT = TEXT_WHITE
    TEXT_DARK = TEXT_PRIMARY
    SUCCESS = "#36A420"
    ERROR = "#FF3B30"
    WARNING = "#FFCC00"

class UISettings:
    WINDOW_WIDTH = 1000
    WINDOW_HEIGHT = 700
    MIN_WIDTH = 800
    MIN_HEIGHT = 600

    # Fonts
    FONT_TITLE = ("Segoe UI", 24, "bold")
    FONT_HEADER = ("Segoe UI", 14, "bold")      
    FONT_CHAT_NAME = ("Segoe UI", 16, "bold")   
    FONT_NORMAL = ("Segoe UI", 11)
    FONT_SMALL = ("Segoe UI", 9)