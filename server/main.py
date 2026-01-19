import sys
import os
import shutil
from datetime import datetime
from contextlib import asynccontextmanager
import asyncio 

# --- CẤU HÌNH ĐƯỜNG DẪN ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from server.bridge import global_bridge
from server.tcp_server_thread import TCPServer
from common.config import SERVER_STORAGE_DIR

os.makedirs(SERVER_STORAGE_DIR, exist_ok=True)

# --- LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    main_loop = asyncio.get_running_loop()
    tcp_thread = TCPServer(main_loop)
    tcp_thread.daemon = True 
    tcp_thread.start()
    
    print("\n" + "="*40)
    print("✅ FULL-STACK SERVER ĐÃ SẴN SÀNG!")
    print(f"   🌐 Web Client:     http://localhost:8000")
    print(f"   💻 Desktop Client: 127.0.0.1:5555")
    print("="*40 + "\n")
    
    yield 
    print("🛑 Server đang tắt...")

app = FastAPI(lifespan=lifespan)

# --- CẤU HÌNH STATIC FILES ---
static_dir = os.path.join(parent_dir, "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/downloads", StaticFiles(directory=SERVER_STORAGE_DIR), name="downloads")

@app.get("/")
async def get():
    return FileResponse(os.path.join(static_dir, 'index.html'))

# --- API UPLOAD FILE (ĐÃ SỬA LẠI LOGIC) ---
@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...), 
    username: str = Form(...),
    recipient: str = Form(None)  # <--- [FIX 1] Thêm tham số nhận người nhận
):
    try:
        # Xử lý chuỗi "None" hoặc rỗng do Client gửi lên
        if recipient == "None" or recipient == "":
            recipient = None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(SERVER_STORAGE_DIR, safe_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        file_size = os.path.getsize(file_path)
        
        # Tạo tin nhắn thông báo file đầy đủ thông tin
        file_info_msg = {
            "type": "FILE_INFO",
            "sender": username,
            "recipient": recipient, # <--- [FIX 2] Gắn người nhận vào tin nhắn
            "filename": safe_filename,
            "original_filename": file.filename,
            "filesize": file_size,
            "file_type": "image" if file.content_type.startswith("image/") else "file",
            "timestamp": datetime.now().isoformat()
        }
        
        # [FIX 3] Dùng handle_message thay vì broadcast
        # handle_message sẽ tự kiểm tra:
        # - Nếu có recipient -> Gửi riêng (Private Chat)
        # - Nếu recipient là None -> Gửi chung (Group Chat)
        await global_bridge.handle_message(file_info_msg, sender=username)
        
        return {"status": "success", "filename": safe_filename}
        
    except Exception as e:
        print(f"Upload Error: {e}")
        return {"status": "error", "message": str(e)}

# --- WEBSOCKET CHAT ---
@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await global_bridge.add_web(username, websocket)
    try:
        users = list(global_bridge.tcp_clients.keys()) + list(global_bridge.web_clients.keys())
        await global_bridge.broadcast({"type": "SYSTEM", "users": users})

        while True:
            data = await websocket.receive_json()
            if "sender" not in data: data["sender"] = username
            await global_bridge.handle_message(data, sender=username)
            
    except WebSocketDisconnect:
        global_bridge.remove_user(username)
        users = list(global_bridge.tcp_clients.keys()) + list(global_bridge.web_clients.keys())
        await global_bridge.broadcast({"type": "SYSTEM", "users": users})
    except Exception as e:
        print(f"WS Error: {e}")
        global_bridge.remove_user(username)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)