"""
Xử lý upload và download file
"""
import os
import threading
from tkinter import filedialog, Toplevel, Label
from tkinter import ttk

from common.protocol import Protocol, MessageType
from common.config import CHUNK_SIZE, UPLOAD_TIMEOUT

class FileHandler:
    def __init__(self, client):
        self.client = client
    
    def send_file(self):
        """Gửi file bất kỳ"""
        filepath = filedialog.askopenfilename(
            title="Chọn file để gửi",
            filetypes=[("All files", "*.*")]
        )
        
        if filepath:
            self.upload_file(filepath, "file")
    
    def send_image(self):
        """Gửi ảnh"""
        filepath = filedialog.askopenfilename(
            title="Chọn ảnh",
            filetypes=[
                ("Images", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"),
                ("All files", "*.*")
            ]
        )
        
        if filepath:
            self.upload_file(filepath, "image")
    
    def send_video(self):
        """Gửi video"""
        filepath = filedialog.askopenfilename(
            title="Chọn video",
            filetypes=[
                ("Videos", "*.mp4 *.avi *.mov *.mkv *.wmv"),
                ("All files", "*.*")
            ]
        )
        
        if filepath:
            self.upload_file(filepath, "video")
    
    def upload_file(self, filepath, file_type):
        """Upload file lên server"""
        try:
            filesize = os.path.getsize(filepath)
            filename = os.path.basename(filepath)
            
            # Tạo progress window
            progress = self._create_progress_window(filename, "Đang gửi...")
            pbar = progress["pbar"]
            plabel = progress["label"]
            window = progress["window"]
            
            def upload_thread():
                try:
                    # 1. Gửi yêu cầu upload
                    Protocol.send_message(
                        self.client.socket,
                        MessageType.FILE_UPLOAD,
                        {
                            "filename": filename,
                            "filesize": filesize,
                            "file_type": file_type
                        }
                    )
                    
                    # 2. Đợi server phản hồi "ready"
                    self.client.upload_event.clear()
                    
                    if not self.client.upload_event.wait(timeout=UPLOAD_TIMEOUT):
                        raise Exception("Timeout: Server không phản hồi yêu cầu gửi file.")
                    
                    if not self.client.upload_permission:
                        raise Exception("Server từ chối nhận file.")
                    
                    # 3. Gửi dữ liệu file
                    sent = 0
                    with open(filepath, 'rb') as f:
                        while sent < filesize:
                            chunk = f.read(CHUNK_SIZE)
                            if not chunk:
                                break
                            self.client.socket.sendall(chunk)
                            sent += len(chunk)
                            
                            # Update progress
                            percent = (sent / filesize) * 100
                            self.client.root.after(0, lambda p=percent: pbar.config(value=p))
                            self.client.root.after(0, lambda p=percent: plabel.config(text=f"{p:.0f}%"))
                    
                    # 4. Đóng window
                    self.client.root.after(0, window.destroy)
                    
                except Exception as e:
                    self.client.root.after(0, window.destroy)
                    self.client.root.after(0, 
                        self.client.message_handler.show_system_message, 
                        f"❌ Lỗi gửi file: {e}")
            
            threading.Thread(target=upload_thread, daemon=True).start()
            
        except Exception as e:
            self.client.message_handler.show_system_message(f"❌ Lỗi: {e}")
    
    def download_file(self, filename):
        """Gửi yêu cầu tải file và chuẩn bị giao diện"""
        try:
            # Tạo progress window
            progress = self._create_progress_window(filename, "Đang tải xuống...")
            
            # Lưu tham chiếu UI
            self.client.current_download_ui = progress
            
            # Gửi yêu cầu lên Server
            Protocol.send_message(
                self.client.socket,
                MessageType.FILE_DOWNLOAD,
                {"filename": filename}
            )
            
        except Exception as e:
            self.client.message_handler.show_system_message(
                f"❌ Lỗi khởi tạo download: {e}")
    
    def handle_file_download_data(self, filename, filesize):
        """Nhận dữ liệu file binary từ server"""
        try:
            filepath = os.path.join(self.client.download_dir, filename)
            received = 0
            
            # Mở file để ghi
            with open(filepath, 'wb') as f:
                while received < filesize:
                    chunk_size = min(CHUNK_SIZE, filesize - received)
                    chunk = self.client.socket.recv(chunk_size)
                    
                    if not chunk:
                        raise Exception("Mất kết nối khi đang tải file")
                    
                    f.write(chunk)
                    received += len(chunk)
                    
                    # Cập nhật UI
                    if self.client.current_download_ui:
                        percent = (received / filesize) * 100
                        pbar = self.client.current_download_ui["pbar"]
                        label = self.client.current_download_ui["label"]
                        
                        self.client.root.after(0, lambda p=percent: pbar.config(value=p))
                        self.client.root.after(0, lambda p=percent: label.config(text=f"{p:.0f}%"))
            
            # Hoàn tất
            self.client.root.after(0, 
                self.client.message_handler.show_system_message, 
                f"✅ Đã tải về: {filepath}")
            
        except Exception as e:
            self.client.root.after(0, 
                self.client.message_handler.show_system_message, 
                f"❌ Lỗi tải file: {e}")
        
        finally:
            # Đóng cửa sổ progress
            if self.client.current_download_ui:
                window = self.client.current_download_ui["window"]
                self.client.root.after(0, window.destroy)
                self.client.current_download_ui = None
    
    def _create_progress_window(self, filename, title):
        """Tạo cửa sổ progress bar"""
        progress = Toplevel(self.client.root)
        progress.title(title)
        progress.geometry("400x150")
        progress.transient(self.client.root)
        progress.resizable(False, False)
        
        # Center window
        progress.update_idletasks()
        x = (progress.winfo_screenwidth() // 2) - 200
        y = (progress.winfo_screenheight() // 2) - 75
        progress.geometry(f"400x150+{x}+{y}")
        
        Label(
            progress,
            text=f"{title} {filename}",
            font=("Arial", 10)
        ).pack(pady=15)
        
        pbar = ttk.Progressbar(progress, length=350, mode='determinate')
        pbar.pack(pady=10)
        
        plabel = Label(progress, text="0%", font=("Arial", 10))
        plabel.pack(pady=5)
        
        return {
            "window": progress,
            "pbar": pbar,
            "label": plabel,
            "filename": filename
        }