from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from server.bridge import global_bridge
from server.tcp_server_thread import TCPServer
import os
from common.config import SERVER_STORAGE_DIR
from datetime import datetime
import shutil

app = FastAPI()

# Mount thư mục static (chứa file HTML/CSS/JS)
app.mount("/static", StaticFiles(directory="static"), name="static")
# Mount thư mục downloads để Client có thể tải file về
app.mount("/downloads", StaticFiles(directory=SERVER_STORAGE_DIR), name="downloads")

@app.on_event("startup")
async def startup_event():
    """Chạy khi Server bắt đầu khởi động"""
    import asyncio
    # Lấy main loop hiện tại để truyền cho TCP Server (dùng cho async tasks)
    main_loop = asyncio.get_running_loop()
    
    # 1. Khởi động TCP Server (Port 5555) ở thread riêng
    tcp_thread = TCPServer(main_loop)
    tcp_thread.daemon = True # Tự tắt khi chương trình chính tắt
    tcp_thread.start()
    print("✅ Hybrid Server Started: Web (Port 8000) + TCP (Port 5555)")

@app.get("/")
async def get():
    """Trả về file HTML chính"""
    return FileResponse('static/index.html')

# --- API UPLOAD FILE (GIỮ LẠI CHO DESKTOP CLIENT CŨ NẾU CẦN) ---
@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    username: str = Form(...),
    recipient: str = Form(None)
):
    try:
        if recipient == "None" or recipient == "": recipient = None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(SERVER_STORAGE_DIR, safe_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        file_size = os.path.getsize(file_path)
        
        file_info_msg = {
            "type": "FILE_INFO",
            "sender": username,
            "recipient": recipient,
            "filename": safe_filename,
            "original_filename": file.filename,
            "filesize": file_size,
            "file_type": "image" if file.content_type.startswith("image/") else "file",
            "timestamp": datetime.now().isoformat()
        }
        
        # Gửi thông báo
        await global_bridge.handle_message(file_info_msg, sender=username)
        
        return {"status": "success", "filename": safe_filename}
    except Exception as e:
        print(f"Upload Error: {e}")
        return {"status": "error", "message": str(e)}

# --- WEBSOCKET CHAT (ĐÃ SỬA LỖI MẤT KẾT NỐI) ---
@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    """Xử lý kết nối từ Web Client"""
    
    # 1. Đăng ký user vào Bridge
    await global_bridge.add_web(username, websocket)
    
    # 2. Gửi danh sách user hiện tại cho người mới vào
    try:
        users = list(global_bridge.tcp_clients.keys()) + list(global_bridge.web_clients.keys())
        await websocket.send_json({"type": "SYSTEM", "users": users})
        
        # Thông báo cho mọi người có user mới online
        await global_bridge.broadcast({"type": "SYSTEM", "users": users})
    except: pass

    # 3. [FIX QUAN TRỌNG] Chuyển giao việc lắng nghe cho Bridge
    # Hàm này sẽ xử lý cả JSON (Chat) và Bytes (File Upload) mà không bị lỗi
    await global_bridge.listen_to_web_user(username)