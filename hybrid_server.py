from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from server.bridge import global_bridge
from server.tcp_server_thread import TCPServer

app = FastAPI()

# Mount thư mục static (chứa file HTML/CSS/JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup_event():
    """Chạy khi Server bắt đầu khởi động"""
    # 1. Khởi động TCP Server (Port 5555) ở thread riêng
    tcp_thread = TCPServer()
    tcp_thread.daemon = True # Tự tắt khi chương trình chính tắt
    tcp_thread.start()
    print("✅ Hybrid Server Started: Web (Port 8000) + TCP (Port 5555)")

@app.get("/")
async def get():
    """Trả về file HTML chính"""
    from fastapi.responses import FileResponse
    return FileResponse('static/index.html')

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    """Xử lý kết nối từ Web Client"""
    # 1. Đăng ký user vào Bridge
    await global_bridge.add_web(username, websocket)
    
    try:
        while True:
            # 2. Nhận tin nhắn từ Web
            data = await websocket.receive_json()
            
            # Gán thêm người gửi nếu thiếu
            if "sender" not in data:
                data["sender"] = username
            
            # 3. Broadcast qua Bridge (nó sẽ tự bắn sang cả TCP và Web khác)
            await global_bridge.broadcast(data, sender=username)
            
    except WebSocketDisconnect:
        global_bridge.remove_user(username)