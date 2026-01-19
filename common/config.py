"""
common/config.py - Cấu hình Dark Mode & Fix lỗi tương thích
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
    # --- 1. MODERN DARK PALETTE (TELEGRAM STYLE) ---
    BG_MAIN = "#0e1621"        # Nền chính (Chat area)
    BG_SIDEBAR = "#17212b"     # Nền Sidebar, Header, Input
    
    # Màu tin nhắn
    MSG_SENT = "#2b5278"       # Bong bóng gửi đi (Xanh dương tối)
    MSG_RECV = "#182533"       # Bong bóng nhận (Xám tối)
    
    # Màu chữ
    TEXT_PRIMARY = "#f5f5f5"   # Trắng sáng
    TEXT_SECONDARY = "#7f91a4" # Xám xanh (Timestamp, Info)
    
    # Màu tương tác
    ACCENT = "#5288c1"         # Màu xanh Telegram (Icon, Button)
    BG_HOVER = "#202b36"       # Màu khi di chuột
    INPUT_BG = "#17212b"       # Nền ô nhập liệu
    
    # Màu đường viền & Khác
    BORDER = "#101924"         
    
    # --- 2. BACKWARD COMPATIBILITY (TRÁNH LỖI CRASH) ---
    BORDER_LIGHT = "#303841"   # Fix lỗi LoginUI cũ
    
    PRIMARY = ACCENT           
    PRIMARY_HOVER = "#406ba0"  
    
    BG_PRIMARY = BG_MAIN       
    BG_SECONDARY = BG_SIDEBAR  
    
    TEXT_LIGHT = "#FFFFFF"     
    TEXT_DARK = "#000000"
    
    BUTTON_HOVER = PRIMARY_HOVER 
    
    SUCCESS = "#4BB543"
    ERROR = "#FF3B30"
    WARNING = "#FF9500"

class UISettings:
    WINDOW_WIDTH = 1100
    WINDOW_HEIGHT = 750
    MIN_WIDTH = 800
    MIN_HEIGHT = 600
    
    # Fonts
    FONT_TITLE = ("Segoe UI", 24, "bold")
    FONT_HEADER = ("Segoe UI", 14, "bold")
    FONT_NAME = ("Segoe UI", 11, "bold")
    FONT_NORMAL = ("Segoe UI", 10)
    FONT_SMALL = ("Segoe UI", 9)