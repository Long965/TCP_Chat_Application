"""
client/handlers/file_handler.py
"""
import os
import threading
import requests
import mimetypes
from tkinter import filedialog, messagebox
from common.config import CLIENT_DOWNLOAD_DIR
from datetime import datetime
from common.protocol import MessageType

class FileHandler:
    def __init__(self, client):
        self.client = client
        if not os.path.exists(CLIENT_DOWNLOAD_DIR):
            os.makedirs(CLIENT_DOWNLOAD_DIR)

    def send_file(self):
        file_path = filedialog.askopenfilename()
        if not file_path: return
        threading.Thread(target=self._upload_thread, args=(file_path,), daemon=True).start()

    def _upload_thread(self, file_path):
        filename = os.path.basename(file_path)
        try:
            host = self.client.socket.getpeername()[0] if self.client.socket else "127.0.0.1"
            api_url = f"http://{host}:8000/upload"
            
            # Lấy recipient
            current_recipient = None
            if self.client.chat_ui and self.client.chat_ui.current_chat:
                current_recipient = self.client.chat_ui.current_chat

            # Gửi recipient dạng chuỗi cho server form data
            data_recipient = current_recipient if current_recipient else ""

            with open(file_path, "rb") as f:
                mime_type, _ = mimetypes.guess_type(file_path)
                files = {'file': (filename, f, mime_type)}
                
                response = requests.post(api_url, files=files, 
                                         data={'username': self.client.username, 'recipient': data_recipient})

            if response.status_code == 200:
                print(f"✅ Upload xong: {filename}")
                resp_json = response.json()
                
                # --- [OPTIMISTIC UI] ---
                # Tạo tin nhắn giả để hiển thị ngay
                fake_msg = {
                    "type": "FILE_INFO",
                    "sender": self.client.username,
                    "recipient": current_recipient, # Giữ nguyên None nếu là group để ChatUI lọc đúng
                    "filename": resp_json.get("filename"),
                    "original_filename": filename,
                    "filesize": os.path.getsize(file_path),
                    "file_type": resp_json.get("file_type", "file"),
                    "timestamp": datetime.now().isoformat()
                }
                
                self.client.root.after(0, lambda: self.client.message_handler.handle_message(MessageType.FILE_INFO, fake_msg))
            else:
                print("Lỗi server:", response.text)
                self.client.root.after(0, lambda: messagebox.showerror("Lỗi Upload", f"Server: {response.text}"))
                
        except Exception as e:
            print(f"Upload error: {e}")
            self.client.root.after(0, lambda: messagebox.showerror("Lỗi", f"Không thể upload: {e}"))

    def request_download(self, file_info):
        save_path = filedialog.asksaveasfilename(initialfile=file_info.get("original_filename"))
        if not save_path: return
        threading.Thread(target=self._download_thread, args=(file_info.get("filename"), save_path), daemon=True).start()

    def _download_thread(self, server_filename, save_path):
        try:
            host = self.client.socket.getpeername()[0] if self.client.socket else "127.0.0.1"
            url = f"http://{host}:8000/downloads/{server_filename}"
            r = requests.get(url, stream=True)
            if r.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(8192): f.write(chunk)
                self.client.root.after(0, lambda: messagebox.showinfo("Thành công", "Đã tải file xong!"))
            else:
                self.client.root.after(0, lambda: messagebox.showerror("Lỗi", "File không tồn tại trên Server"))
        except Exception as e:
            self.client.root.after(0, lambda: messagebox.showerror("Lỗi Tải", str(e)))