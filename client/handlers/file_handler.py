import os
import threading
import time
import requests # Cần cài đặt: pip install requests
from tkinter import filedialog, messagebox
from collections import deque
from common.config import CLIENT_DOWNLOAD_DIR
from common.protocol import Protocol, MessageType
from client.ui.message_ui import MessageUI

# Kích thước gói tin chia nhỏ
CHUNK_SIZE = 8192 

# [CẤU HÌNH] Giới hạn tốc độ Upload
UPLOAD_SPEED_LIMIT = 512 * 1024  # 512 KB/s

# ============================================================================
# CLASS: UPLOAD SESSION (Quản lý gửi file)
# ============================================================================
class UploadSession:
    def __init__(self, client, file_path, recipient, update_ui_callback, on_complete_callback=None):
        self.client = client
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
        self.filesize = os.path.getsize(file_path)
        self.recipient = recipient
        self.update_ui = update_ui_callback
        self.on_complete = on_complete_callback # Callback khi xong để chạy file tiếp theo
        
        self.paused = False
        self.cancelled = False
        self.sent_bytes = 0
        self.is_running = False

    def is_connected(self):
        return getattr(self.client, 'connected', False) and self.client.socket

    def start(self):
        if not self.is_running:
            self.is_running = True
            threading.Thread(target=self._run, daemon=True).start()

    def pause(self): 
        self.paused = True
    
    def resume(self): 
        self.paused = False
    
    def cancel(self): 
        self.cancelled = True
        self.is_running = False

    def _run(self):
        try:
            if not self.is_connected(): return 

            # 1. Gửi Header
            try:
                Protocol.send_message(
                    self.client.socket,
                    MessageType.FILE_UPLOAD,
                    {
                        "filename": self.filename,
                        "filesize": self.filesize,
                        "recipient": self.recipient,
                        "sender": self.client.username
                    }
                )
            except Exception:
                return

            time.sleep(0.5) # Đợi server xử lý header

            # 2. Gửi Data
            with open(self.file_path, "rb") as f:
                # Nếu đã gửi được 1 phần (logic resume nâng cao sau này), seek tới đó
                if self.sent_bytes > 0:
                    f.seek(self.sent_bytes)

                while self.sent_bytes < self.filesize:
                    # Check Cancel
                    if self.cancelled: 
                        print(f"❌ Upload cancelled: {self.filename}")
                        return 

                    if not self.is_connected(): return
                    
                    # Check Pause
                    while self.paused:
                        if self.cancelled: return
                        time.sleep(0.1)

                    start_time = time.time()

                    chunk = f.read(CHUNK_SIZE)
                    if not chunk: break
                    
                    try:
                        self.client.socket.sendall(chunk)
                    except OSError as e:
                        if e.winerror in [10038, 10054, 10053] or e.errno == 9: 
                            return
                        raise e 

                    self.sent_bytes += len(chunk)
                    
                    # Cập nhật UI
                    if self.update_ui:
                        self.client.root.after(0, lambda: self.update_ui(self.sent_bytes))

                    # Logic giới hạn tốc độ
                    if UPLOAD_SPEED_LIMIT and UPLOAD_SPEED_LIMIT > 0:
                        elapsed = time.time() - start_time
                        expected_duration = len(chunk) / UPLOAD_SPEED_LIMIT
                        if elapsed < expected_duration:
                            time.sleep(expected_duration - elapsed)

            print(f"✅ Upload xong: {self.filename}")
            
            # Gọi callback để báo cho FileHandler biết đã xong file này
            if self.on_complete:
                self.client.root.after(0, self.on_complete)

        except Exception as e:
            err_str = str(e)
            if "10038" in err_str or "10054" in err_str:
                return
            if not self.cancelled:
                self.client.root.after(0, lambda: messagebox.showerror("Lỗi Upload", err_str))

# ============================================================================
# CLASS: DOWNLOAD SESSION (Quản lý tải file HTTP)
# ============================================================================
class DownloadSession:
    def __init__(self, client, url, save_path, filesize, update_ui_callback):
        self.client = client
        self.url = url
        self.save_path = save_path
        self.filesize = filesize
        self.update_ui = update_ui_callback
        
        self.paused = False
        self.cancelled = False
        self.received_bytes = 0
        self.is_running = False

    def start(self):
        if not self.is_running:
            self.is_running = True
            threading.Thread(target=self._run, daemon=True).start()

    def pause(self): self.paused = True
    def resume(self): self.paused = False
    def cancel(self): self.cancelled = True

    def _run(self):
        try:
            # Chế độ ghi: 'wb' (ghi mới) hoặc 'ab' (ghi tiếp - resume)
            mode = 'wb'
            headers = {}
            
            # Kiểm tra nếu file đã tồn tại để Resume (Tải tiếp)
            if os.path.exists(self.save_path):
                self.received_bytes = os.path.getsize(self.save_path)
                if self.received_bytes < self.filesize:
                    # Gửi Header Range để yêu cầu server gửi từ byte tiếp theo
                    headers['Range'] = f'bytes={self.received_bytes}-'
                    mode = 'ab'
                else:
                    # File đã tải xong rồi
                    self.received_bytes = 0 # Tải lại từ đầu nếu muốn ghi đè
            
            # Gửi Request HTTP
            r = requests.get(self.url, headers=headers, stream=True)
            
            if r.status_code not in [200, 206]: # 200: OK, 206: Partial Content (Resume)
                raise Exception(f"Server returned status: {r.status_code}")

            with open(self.save_path, mode) as f:
                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                    # Check Cancel
                    if self.cancelled:
                        print(f"❌ Download cancelled: {self.save_path}")
                        r.close()
                        return

                    # Check Pause
                    while self.paused:
                        if self.cancelled: return
                        time.sleep(0.1)

                    if chunk:
                        f.write(chunk)
                        self.received_bytes += len(chunk)
                        
                        # Cập nhật UI
                        if self.update_ui:
                            self.client.root.after(0, lambda: self.update_ui(self.received_bytes))
            
            print(f"✅ Download xong: {self.save_path}")
            self.client.root.after(0, lambda: messagebox.showinfo("Thành công", f"Đã tải xong:\n{os.path.basename(self.save_path)}"))

        except Exception as e:
            if not self.cancelled:
                self.client.root.after(0, lambda: messagebox.showerror("Lỗi Download", str(e)))

# ============================================================================
# CLASS: FILE HANDLER (Quản lý chung)
# ============================================================================
class FileHandler:
    def __init__(self, client):
        self.client = client
        if not os.path.exists(CLIENT_DOWNLOAD_DIR):
            os.makedirs(CLIENT_DOWNLOAD_DIR)
            
        # Hàng đợi Upload (Multi-file)
        self.upload_queue = deque()
        self.current_upload_session = None
        
        # Container chứa các session download đang chạy (để Pause/Cancel)
        self.download_sessions = {} 

    # ------------------------------------------------------------------------
    # UPLOAD LOGIC
    # ------------------------------------------------------------------------
    def send_file(self):
        """Chọn nhiều file và thêm vào hàng đợi upload"""
        # [FIX] Dùng askopenfilenames (có 's') để chọn nhiều file
        file_paths = filedialog.askopenfilenames()
        if not file_paths: return

        recipient = None
        if self.client.chat_ui and self.client.chat_ui.current_chat:
            recipient = self.client.chat_ui.current_chat

        # Thêm tất cả file vào hàng đợi
        for path in file_paths:
            self.upload_queue.append((path, recipient))
        
        # Nếu chưa có file nào đang upload thì bắt đầu xử lý hàng đợi
        if not self.current_upload_session:
            self._process_upload_queue()

    def _process_upload_queue(self):
        """Lấy file tiếp theo trong hàng đợi và xử lý"""
        if not self.upload_queue:
            self.current_upload_session = None
            return

        # Lấy file đầu tiên ra
        file_path, recipient = self.upload_queue.popleft()
        filename = os.path.basename(file_path)
        filesize = os.path.getsize(file_path)

        # Container để UI gọi ngược lại logic (Pause/Resume/Cancel)
        session_container = {}

        def on_pause(): 
            if 's' in session_container: session_container['s'].pause()
        def on_resume(): 
            if 's' in session_container: session_container['s'].resume()
        def on_cancel(): 
            if 's' in session_container: session_container['s'].cancel()
            # Nếu hủy, chuyển sang file tiếp theo ngay lập tức
            self._process_upload_queue()

        callbacks = {'pause': on_pause, 'resume': on_resume, 'cancel': on_cancel}

        # Hiển thị UI Progress Bar
        update_func = None
        if self.client.chat_ui:
            update_func = MessageUI.display_upload_progress(
                self.client.chat_ui.messages_container,
                filename, filesize, callbacks
            )
            self.client.chat_ui.canvas.yview_moveto(1)

        # Tạo session upload mới
        session = UploadSession(
            self.client, 
            file_path, 
            recipient, 
            update_func,
            on_complete_callback=self._process_upload_queue # Xong file này thì chạy file tiếp
        )
        
        session_container['s'] = session
        self.current_upload_session = session
        session.start()

    # ------------------------------------------------------------------------
    # DOWNLOAD LOGIC
    # ------------------------------------------------------------------------
    def request_download(self, file_info):
        """Tải file (Hỗ trợ nhiều lượt tải cùng lúc)"""
        filename = file_info.get("filename") # Tên trên server (có timestamp)
        original_name = file_info.get("original_filename")
        filesize = file_info.get("filesize", 0)

        # Hỏi nơi lưu file
        save_path = filedialog.asksaveasfilename(initialfile=original_name)
        if not save_path: return

        # Tạo container điều khiển cho file này
        session_id = str(time.time()) # ID định danh cho lượt tải này
        session_container = {}

        def on_pause(): 
            if 's' in session_container: session_container['s'].pause()
        def on_resume(): 
            if 's' in session_container: session_container['s'].resume()
        def on_cancel(): 
            if 's' in session_container: session_container['s'].cancel()
            # Xóa session khỏi danh sách quản lý
            if session_id in self.download_sessions:
                del self.download_sessions[session_id]

        callbacks = {'pause': on_pause, 'resume': on_resume, 'cancel': on_cancel}

        # Hiển thị UI Progress Download (Bạn cần đảm bảo MessageUI có hàm này,
        # Nếu chưa có, dùng tạm display_upload_progress nhưng đổi màu hoặc title)
        update_func = None
        if self.client.chat_ui:
            # Tạm dùng UI upload cho download (hoặc bạn tạo hàm display_download_progress riêng)
            # Sửa tiêu đề trong UI thành "Đang tải về..."
            update_func = MessageUI.display_upload_progress(
                self.client.chat_ui.messages_container,
                f"⬇️ {original_name}", filesize, callbacks
            )
            self.client.chat_ui.canvas.yview_moveto(1)

        # Xác định URL tải về
        host = "127.0.0.1"
        if getattr(self.client, 'socket', None):
            try: host = self.client.socket.getpeername()[0]
            except: pass
        
        url = f"http://{host}:8000/downloads/{filename}"

        # Khởi tạo Session Download
        session = DownloadSession(self.client, url, save_path, filesize, update_func)
        
        session_container['s'] = session
        self.download_sessions[session_id] = session
        
        # Bắt đầu tải
        session.start()