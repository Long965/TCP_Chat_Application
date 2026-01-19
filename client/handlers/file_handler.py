import os
import threading
import time
from tkinter import filedialog, messagebox
from common.config import CLIENT_DOWNLOAD_DIR
from common.protocol import Protocol, MessageType
from client.ui.message_ui import MessageUI

# Kích thước gói tin chia nhỏ
CHUNK_SIZE = 8192 

# [CẤU HÌNH] Giới hạn tốc độ Upload
# Ví dụ: 1024 * 1024 = 1 MB/s
# Để None hoặc 0 nếu không muốn giới hạn
UPLOAD_SPEED_LIMIT = 512 * 1024  # 512 KB/s (Để thấy thanh tiến độ chạy từ từ)

class UploadSession:
    def __init__(self, client, file_path, recipient, update_ui_callback):
        self.client = client
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
        self.filesize = os.path.getsize(file_path)
        self.recipient = recipient
        self.update_ui = update_ui_callback
        
        self.paused = False
        self.cancelled = False
        self.sent_bytes = 0

    def is_connected(self):
        return getattr(self.client, 'connected', False) and self.client.socket

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def pause(self): self.paused = True
    def resume(self): self.paused = False
    def cancel(self): self.cancelled = True

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

            # 2. Gửi Data (Có kiểm soát tốc độ)
            with open(self.file_path, "rb") as f:
                while self.sent_bytes < self.filesize:
                    # Đánh dấu thời gian bắt đầu gửi chunk
                    start_time = time.time()

                    if self.cancelled: return 
                    if not self.is_connected(): return
                    if self.paused:
                        time.sleep(0.1)
                        continue

                    chunk = f.read(CHUNK_SIZE)
                    if not chunk: break
                    
                    try:
                        self.client.socket.sendall(chunk)
                    except OSError as e:
                        if e.winerror in [10038, 10054, 10053] or e.errno == 9: 
                            return
                        raise e 

                    self.sent_bytes += len(chunk)
                    self.client.root.after(0, lambda: self.update_ui(self.sent_bytes))

                    # --- [LOGIC KIỂM SOÁT TỐC ĐỘ] ---
                    if UPLOAD_SPEED_LIMIT and UPLOAD_SPEED_LIMIT > 0:
                        # Thời gian thực tế đã trôi qua để gửi chunk này
                        elapsed = time.time() - start_time
                        
                        # Thời gian lý thuyết cần thiết để đạt đúng tốc độ giới hạn
                        # (Kích thước chunk / Tốc độ mong muốn)
                        expected_duration = len(chunk) / UPLOAD_SPEED_LIMIT
                        
                        # Nếu gửi quá nhanh (thời gian thực < thời gian lý thuyết) -> Ngủ bù
                        if elapsed < expected_duration:
                            time.sleep(expected_duration - elapsed)
                    # --------------------------------

            print(f"✅ Upload xong: {self.filename}")

        except Exception as e:
            err_str = str(e)
            if "10038" in err_str or "10054" in err_str:
                return
            if not self.cancelled:
                self.client.root.after(0, lambda: messagebox.showerror("Lỗi Upload", err_str))

class FileHandler:
    def __init__(self, client):
        self.client = client
        if not os.path.exists(CLIENT_DOWNLOAD_DIR):
            os.makedirs(CLIENT_DOWNLOAD_DIR)

    def send_file(self):
        file_path = filedialog.askopenfilename()
        if not file_path: return

        recipient = None
        if self.client.chat_ui and self.client.chat_ui.current_chat:
            recipient = self.client.chat_ui.current_chat

        filename = os.path.basename(file_path)
        filesize = os.path.getsize(file_path)

        session_container = {} 

        def on_pause(): 
            if 's' in session_container: session_container['s'].pause()
        def on_resume(): 
            if 's' in session_container: session_container['s'].resume()
        def on_cancel(): 
            if 's' in session_container: session_container['s'].cancel()

        callbacks = {'pause': on_pause, 'resume': on_resume, 'cancel': on_cancel}

        if self.client.chat_ui:
            update_func = MessageUI.display_upload_progress(
                self.client.chat_ui.messages_container,
                filename, filesize, callbacks
            )
            self.client.chat_ui.canvas.yview_moveto(1)

            session = UploadSession(self.client, file_path, recipient, update_func)
            session_container['s'] = session
            session.start()

    def request_download(self, file_info):
        save_path = filedialog.asksaveasfilename(initialfile=file_info.get("original_filename"))
        if not save_path: return
        
        import requests
        def _download():
            try:
                host = "127.0.0.1"
                if getattr(self.client, 'socket', None):
                    try: host = self.client.socket.getpeername()[0]
                    except: pass
                
                url = f"http://{host}:8000/downloads/{file_info.get('filename')}"
                r = requests.get(url, stream=True)
                
                if r.status_code == 200:
                    with open(save_path, 'wb') as f:
                        for chunk in r.iter_content(8192): f.write(chunk)
                    self.client.root.after(0, lambda: messagebox.showinfo("Thành công", "Tải xong!"))
                else:
                    self.client.root.after(0, lambda: messagebox.showerror("Lỗi", "File không tồn tại"))
            except Exception as e:
                err_str = str(e)
                self.client.root.after(0, lambda: messagebox.showerror("Lỗi Tải", err_str))
                
        threading.Thread(target=_download, daemon=True).start()