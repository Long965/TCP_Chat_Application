"""
Cấu hình chung cho ứng dụng chat
"""

# Server settings
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5555
DEFAULT_SERVER = "127.0.0.1:5555"

# Directory settings
CLIENT_DOWNLOAD_DIR = "client_downloads"
SERVER_STORAGE_DIR = "server_files"

# Network settings
CHUNK_SIZE = 8192  # 8KB chunks cho file transfer
SOCKET_TIMEOUT = 5  # Timeout cho kết nối ban đầu
UPLOAD_TIMEOUT = 10  # Timeout cho việc đợi server response khi upload

# UI Colors (Zalo-like)
class Colors:
    BG_PRIMARY = "#0068FF"
    BG_SECONDARY = "#F0F2F5"
    BG_WHITE = "#FFFFFF"
    TEXT_PRIMARY = "#000000"
    TEXT_SECONDARY = "#65676B"
    MESSAGE_SENT = "#0084FF"
    MESSAGE_RECEIVED = "#E4E6EB"

# UI Settings
class UISettings:
    WINDOW_WIDTH = 1000
    WINDOW_HEIGHT = 700
    MIN_WIDTH = 800
    MIN_HEIGHT = 600
    SIDEBAR_WIDTH = 280
    CHAT_HEADER_HEIGHT = 60
    INPUT_AREA_HEIGHT = 80
    
    # Fonts
    FONT_TITLE = ("Arial", 32, "bold")
    FONT_HEADER = ("Arial", 18, "bold")
    FONT_NORMAL = ("Arial", 11)
    FONT_MESSAGE = ("Arial", 10)
    FONT_SMALL = ("Arial", 9)
    FONT_TINY = ("Arial", 8)