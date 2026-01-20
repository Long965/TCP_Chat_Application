import threading
import time
import base64
import tkinter as tk
from tkinter import Toplevel, Label, Button, messagebox
from PIL import Image, ImageTk
from common.protocol import Protocol, MessageType

# Cố gắng import OpenCV
try:
    import cv2
except ImportError:
    cv2 = None
    print("⚠️ Warning: 'opencv-python' not installed. Video call will not work.")

class CallHandler:
    def __init__(self, client):
        self.client = client
        self.in_call = False
        self.cap = None
        self.video_window = None
        self.peer_name = None
        self.stop_event = threading.Event()

    # ==================================================================
    # [FIX] THÊM HÀM NÀY ĐỂ UI GỌI ĐƯỢC
    # ==================================================================
    def start_call(self, recipient):
        """
        Hàm này được gọi khi bấm nút 'Gọi Video' trên UI.
        Nó gửi yêu cầu kết nối đến Server.
        """
        if not recipient:
            messagebox.showwarning("Lỗi", "Vui lòng chọn một người để gọi!")
            return

        if not cv2:
            messagebox.showerror("Thiếu thư viện", "Chưa cài đặt OpenCV (pip install opencv-python).")
            return

        print(f"📞 Đang gửi yêu cầu gọi tới: {recipient}")
        
        # Gửi tín hiệu CALL_REQUEST
        Protocol.send_message(
            self.client.socket,
            MessageType.CALL_REQUEST,
            {
                "caller": self.client.username,
                "recipient": recipient
            }
        )
        
        messagebox.showinfo("Đang gọi", f"Đang chờ {recipient} trả lời...")

    # ==================================================================
    # CÁC HÀM XỬ LÝ TÍN HIỆU TỪ SERVER
    # ==================================================================

    def handle_call_request(self, data):
        """Xử lý khi có người khác gọi đến mình"""
        caller = data.get("caller")
        
        # Nếu đang bận -> Từ chối tự động
        if self.in_call:
            Protocol.send_message(
                self.client.socket,
                MessageType.CALL_BUSY,
                {"recipient": caller, "sender": self.client.username}
            )
            return

        # Hiện Popup hỏi ý kiến
        response = messagebox.askyesno(
            "Cuộc gọi đến", 
            f"📞 {caller} đang muốn gọi video với bạn.\nBạn có muốn chấp nhận không?"
        )

        if response:
            # Chấp nhận -> Gửi ACCEPT và bật Camera
            Protocol.send_message(
                self.client.socket,
                MessageType.CALL_ACCEPT,
                {"recipient": caller, "sender": self.client.username}
            )
            self.start_video_stream(caller) # Bắt đầu stream
        else:
            # Từ chối -> Gửi REJECT
            Protocol.send_message(
                self.client.socket,
                MessageType.CALL_REJECT,
                {"recipient": caller, "sender": self.client.username}
            )

    def handle_call_accept(self, data):
        """Xử lý khi đối phương đồng ý cuộc gọi"""
        recipient = data.get("sender")
        messagebox.showinfo("Kết nối", f"✅ {recipient} đã chấp nhận cuộc gọi!")
        self.start_video_stream(recipient) # Bắt đầu stream

    def handle_call_reject(self, data):
        """Xử lý khi đối phương từ chối"""
        sender = data.get("sender")
        messagebox.showinfo("Kết thúc", f"❌ {sender} đã từ chối cuộc gọi.")
        self.stop_video_call()

    def handle_call_end(self, data):
        """Xử lý khi đối phương ngắt máy"""
        if self.in_call:
            messagebox.showinfo("Kết thúc", "📴 Cuộc gọi đã kết thúc.")
            self.stop_video_call()

    def handle_ice_candidate(self, data):
        # Placeholder cho WebRTC (nếu nâng cấp sau này)
        pass

    # ==================================================================
    # LOGIC VIDEO STREAMING (OPENCV)
    # ==================================================================

    def start_video_stream(self, peer_name):
        """Bật Camera và bắt đầu gửi dữ liệu"""
        self.in_call = True
        self.peer_name = peer_name
        self.stop_event.clear()

        # Mở cửa sổ hiển thị video
        self._open_video_window()

        # Mở Camera (Index 0 là camera mặc định)
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            messagebox.showerror("Lỗi Camera", "Không thể mở Camera!")
            self.stop_video_call()
            return

        # Chạy luồng đọc/gửi video song song
        threading.Thread(target=self._video_stream_loop, daemon=True).start()

    def _open_video_window(self):
        """Tạo cửa sổ giao diện cuộc gọi"""
        self.video_window = Toplevel(self.client.root)
        self.video_window.title(f"Video Call - Đang gọi: {self.peer_name}")
        self.video_window.geometry("640x550")
        
        # Xử lý khi bấm nút X tắt cửa sổ
        self.video_window.protocol("WM_DELETE_WINDOW", self.request_end_call)

        # Label hiển thị hình ảnh camera
        self.lbl_local = Label(self.video_window, text="Đang tải Camera...", bg="black", fg="white")
        self.lbl_local.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        # Nút ngắt cuộc gọi
        btn_end = Button(self.video_window, text="📴 Kết thúc cuộc gọi", bg="#dc3545", fg="white", 
                         font=("Arial", 12, "bold"), command=self.request_end_call)
        btn_end.pack(side="bottom", fill="x", pady=10, padx=10)

    def _video_stream_loop(self):
        """Vòng lặp đọc Camera -> Encode JPEG -> Gửi Socket"""
        while self.in_call and not self.stop_event.is_set():
            if not self.cap: break
            
            ret, frame = self.cap.read()
            if not ret: break

            # 1. Resize ảnh nhỏ lại để gửi nhanh hơn (320x240)
            frame_resized = cv2.resize(frame, (320, 240))

            # 2. Lật ngược ảnh cho giống gương (Mirror)
            frame_resized = cv2.flip(frame_resized, 1)

            # 3. Nén ảnh thành JPEG -> Chuyển sang Base64
            _, buffer = cv2.imencode('.jpg', frame_resized, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')

            # 4. Gửi dữ liệu qua Server
            try:
                Protocol.send_message(
                    self.client.socket,
                    MessageType.VIDEO_DATA,
                    {
                        "recipient": self.peer_name,
                        "data": jpg_as_text,
                        "sender": self.client.username
                    }
                )
            except Exception as e:
                print(f"Lỗi gửi video: {e}")
                break
            
            # 5. Hiển thị lên màn hình của mình
            self._update_local_preview(frame_resized)
            
            # Giới hạn tốc độ gửi (khoảng 20 FPS)
            time.sleep(0.05)

    def _update_local_preview(self, frame):
        """Vẽ hình ảnh lên cửa sổ Tkinter"""
        if self.video_window and self.video_window.winfo_exists():
            # Chuyển hệ màu từ BGR (OpenCV) sang RGB (Tkinter)
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)
            
            # Update UI phải dùng root.after để thread-safe
            self.client.root.after(0, lambda: self._set_image(imgtk))

    def _set_image(self, imgtk):
        if self.lbl_local and self.lbl_local.winfo_exists():
            self.lbl_local.imgtk = imgtk # Giữ tham chiếu để không bị Garbage Collected
            self.lbl_local.configure(image=imgtk)

    def request_end_call(self):
        """Người dùng chủ động bấm nút Tắt"""
        if self.peer_name:
            Protocol.send_message(
                self.client.socket,
                MessageType.CALL_END,
                {"recipient": self.peer_name, "sender": self.client.username}
            )
        self.stop_video_call()

    def stop_video_call(self):
        """Dọn dẹp tài nguyên khi tắt"""
        self.in_call = False
        self.stop_event.set()
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        if self.video_window:
            self.video_window.destroy()
            self.video_window = None
            
        self.peer_name = None