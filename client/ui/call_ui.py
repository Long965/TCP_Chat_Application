"""
Giao diện Video/Audio Call với WebRTC thực
"""

from tkinter import Frame, Label, Button, Toplevel, Canvas
from tkinter import CENTER, BOTH
from common.protocol import Protocol, MessageType
import time
import threading
import base64
import cv2
import numpy as np
from PIL import Image, ImageTk

# WebRTC imports
try:
    import cv2
    import numpy as np
    from PIL import Image, ImageTk
    import pyaudio
    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False
    print("⚠️  WebRTC dependencies not available. Install: opencv-python, pyaudio")

class CallUI:
    def __init__(self, client, peer_username, call_type, is_caller=False):
        self.client = client
        self.peer = peer_username
        self.call_type = call_type  # "video" or "audio"
        self.is_caller = is_caller
        self.colors = client.colors
        self.call_active = False
        self.start_time = None
        
        # WebRTC components
        self.video_capture = None
        self.audio_stream = None
        self.audio_output = None
        self.is_muted = False
        self.is_camera_on = True
        
        # Tạo cửa sổ call
        self.window = Toplevel(client.root)
        self.window.title(f"{'Video' if call_type == 'video' else 'Audio'} Call")
        
        if call_type == "video":
            self.window.geometry("800x600")
        else:
            self.window.geometry("400x300")
        
        # Center window
        self.window.update_idletasks()
        w = 800 if call_type == "video" else 400
        h = 600 if call_type == "video" else 300
        x = (self.window.winfo_screenwidth() // 2) - w // 2
        y = (self.window.winfo_screenheight() // 2) - h // 2
        self.window.geometry(f"{w}x{h}+{x}+{y}")
        
        # Main container
        self.main_container = Frame(self.window, bg="#1a1a1a")
        self.main_container.pack(fill=BOTH, expand=True)
        
        if is_caller:
            self._create_calling_ui()
        else:
            self._create_incoming_ui()
        
        # Lưu reference
        self.client.current_call = self
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._end_call)
    
    def _create_calling_ui(self):
        """UI khi đang gọi đi"""
        # Video canvas (if video call)
        if self.call_type == "video":
            self.video_canvas = Canvas(
                self.main_container, 
                bg="#000000", 
                width=640, 
                height=480,
                highlightthickness=0
            )
            self.video_canvas.pack(padx=20, pady=20)
            
            # Placeholder text
            self.placeholder_text = self.video_canvas.create_text(
                320, 240,
                text="📹 Đang kết nối...",
                font=("Arial", 24),
                fill="#666666"
            )
        
        # Status
        self.status_label = Label(
            self.main_container,
            text=f"Đang gọi {self.peer}...",
            font=("Arial", 16),
            bg="#1a1a1a",
            fg="white"
        )
        self.status_label.pack(pady=10)
        
        # Timer
        self.timer_label = Label(
            self.main_container,
            text="00:00",
            font=("Arial", 14),
            bg="#1a1a1a",
            fg="#888888"
        )
        self.timer_label.pack(pady=5)
        self.timer_label.pack_forget()
        
        # Controls
        self._create_call_controls()
    
    def _create_incoming_ui(self):
        """UI khi nhận cuộc gọi"""
        # Video placeholder (if video call)
        if self.call_type == "video":
            video_frame = Frame(self.main_container, bg="#000000", height=250)
            video_frame.pack(fill="x", padx=20, pady=20)
            video_frame.pack_propagate(False)
            
            Label(
                video_frame,
                text="📹",
                font=("Arial", 60),
                bg="#000000",
                fg="#666666"
            ).place(relx=0.5, rely=0.5, anchor=CENTER)
        
        # Caller info
        Label(
            self.main_container,
            text=f"{self.peer}",
            font=("Arial", 20, "bold"),
            bg="#1a1a1a",
            fg="white"
        ).pack(pady=20)
        
        Label(
            self.main_container,
            text=f"Cuộc gọi {'video' if self.call_type == 'video' else 'thoại'} đến...",
            font=("Arial", 14),
            bg="#1a1a1a",
            fg="#cccccc"
        ).pack(pady=5)
        
        # Answer/Reject buttons
        buttons_frame = Frame(self.main_container, bg="#1a1a1a")
        buttons_frame.pack(pady=30)
        
        Button(
            buttons_frame,
            text="❌",
            font=("Arial", 30),
            bg="#ff3b30",
            fg="white",
            width=5,
            height=2,
            bd=0,
            cursor="hand2",
            command=self._reject_call
        ).pack(side="left", padx=20)
        
        Button(
            buttons_frame,
            text="✅",
            font=("Arial", 30),
            bg="#34c759",
            fg="white",
            width=5,
            height=2,
            bd=0,
            cursor="hand2",
            command=self._accept_call
        ).pack(side="left", padx=20)
    
    def _create_call_controls(self):
        """Tạo các nút điều khiển cuộc gọi"""
        controls_frame = Frame(self.main_container, bg="#1a1a1a")
        controls_frame.pack(pady=10)
        
        # Mute button
        self.mute_btn = Button(
            controls_frame,
            text="🎤",
            font=("Arial", 20),
            bg="#333333",
            fg="white",
            width=4,
            height=2,
            bd=0,
            cursor="hand2",
            command=self._toggle_mute
        )
        self.mute_btn.pack(side="left", padx=10)
        
        # Camera button (if video)
        if self.call_type == "video":
            self.camera_btn = Button(
                controls_frame,
                text="📹",
                font=("Arial", 20),
                bg="#333333",
                fg="white",
                width=4,
                height=2,
                bd=0,
                cursor="hand2",
                command=self._toggle_camera
            )
            self.camera_btn.pack(side="left", padx=10)
        
        # End call button
        Button(
            controls_frame,
            text="📞",
            font=("Arial", 20),
            bg="#ff3b30",
            fg="white",
            width=4,
            height=2,
            bd=0,
            cursor="hand2",
            command=self._end_call
        ).pack(side="left", padx=10)
    
    def _accept_call(self):
        """Chấp nhận cuộc gọi"""
        Protocol.send_message(
            self.client.socket,
            MessageType.CALL_ACCEPT,
            {
                "caller": self.peer,
                "recipient": self.client.username
            }
        )
        
        # Chuyển sang UI đang gọi
        for widget in self.main_container.winfo_children():
            widget.destroy()
        
        self._create_calling_ui()
        self._start_call_session()
    
    def _reject_call(self):
        """Từ chối cuộc gọi"""
        Protocol.send_message(
            self.client.socket,
            MessageType.CALL_REJECT,
            {
                "caller": self.peer,
                "recipient": self.client.username
            }
        )
        
        self._cleanup_media()
        self.window.destroy()
        if self.client.current_call == self:
            self.client.current_call = None
    
    def _end_call(self):
        """Kết thúc cuộc gọi"""
        if self.call_active:
            Protocol.send_message(
                self.client.socket,
                MessageType.CALL_END,
                {
                    "peer": self.peer
                }
            )
        
        self._cleanup_media()
        self.window.destroy()
        if self.client.current_call == self:
            self.client.current_call = None
    
    def _start_call_session(self):
        """Bắt đầu phiên gọi - Khởi động media"""
        self.call_active = True
        self.start_time = time.time()
        
        # Update status
        self.status_label.config(text=f"Đang gọi với {self.peer}")
        
        # Show timer
        self.timer_label.pack(pady=5)
        self._update_timer()
        
        # Khởi động media streaming
        if WEBRTC_AVAILABLE:
            threading.Thread(target=self._start_media_streaming, daemon=True).start()
        else:
            self.status_label.config(
                text="⚠️ WebRTC không khả dụng. Chỉ demo UI.",
                fg="#ff9500"
            )
    
    def _start_media_streaming(self):
        """Khởi động video/audio streaming"""
        try:
            # Video streaming
            if self.call_type == "video" and self.is_camera_on:
                self._start_video_capture()
            
            # Audio streaming
            self._start_audio_streaming()
            
        except Exception as e:
            print(f"Error starting media: {e}")
            self.window.after(0, lambda: self.status_label.config(
                text=f"⚠️ Lỗi media: {e}",
                fg="#ff3b30"
            ))
    
    def _start_video_capture(self):
        """Bắt đầu capture video từ webcam"""
        try:
            self.video_capture = cv2.VideoCapture(0)
            
            if not self.video_capture.isOpened():
                raise Exception("Không thể mở webcam")
            
            # Set resolution
            self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # Xóa placeholder
            if hasattr(self, 'placeholder_text'):
                self.video_canvas.delete(self.placeholder_text)
            
            # Bắt đầu video loop
            self._update_video_frame()
            
        except Exception as e:
            print(f"Video capture error: {e}")
    
    def _update_video_frame(self):
        """Cập nhật frame video: Hiển thị local + Gửi đi"""
        if not self.call_active or not self.is_camera_on:
            return

        # --- CẤU HÌNH (Dễ dàng điều chỉnh tại đây) ---
        SEND_WIDTH, SEND_HEIGHT = 320, 240  # Giảm độ phân giải khi gửi để mượt hơn
        JPEG_QUALITY = 50                   # Chất lượng ảnh (0-100), thấp hơn = nhanh hơn
        FPS_TARGET = 30                     # Tốc độ khung hình
        # ---------------------------------------------

        try:
            ret, frame = self.video_capture.read()
            if ret:
                # 1. Xử lý hiển thị Local (Mirror)
                # Chỉ hiển thị local nếu chưa có video từ đối phương (hoặc bạn có thể vẽ PIP)
                if not hasattr(self, 'has_peer_video') or not self.has_peer_video:
                    self._render_frame_to_canvas(frame)

                # 2. Xử lý gửi đi (Send)
                try:
                    # Resize nhỏ lại để gửi qua mạng
                    frame_small = cv2.resize(frame, (SEND_WIDTH, SEND_HEIGHT))
                    
                    # Nén thành JPEG
                    _, buffer = cv2.imencode('.jpg', frame_small, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
                    
                    # Mã hóa Base64
                    jpg_as_text = base64.b64encode(buffer).decode('utf-8')
                    
                    # Gửi qua socket
                    from common.protocol import Protocol, MessageType
                    Protocol.send_message(
                        self.client.socket,
                        MessageType.VIDEO_DATA,
                        {
                            "recipient": self.peer,
                            "data": jpg_as_text
                        }
                    )
                except Exception as e:
                    print(f"Send video error: {e}")

            # Loop
            self.window.after(int(1000/FPS_TARGET), self._update_video_frame)

        except Exception as e:
            print(f"Frame update error: {e}")

    def _render_frame_to_canvas(self, frame):
        """Hàm hỗ trợ vẽ frame lên canvas"""
        try:
            # Convert màu BGR -> RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Nếu là camera trước (selfie), lật ngược lại cho giống gương
            if not hasattr(self, 'has_peer_video') or not self.has_peer_video:
                 frame_rgb = cv2.flip(frame_rgb, 1)

            # Resize cho vừa Canvas
            canvas_width = self.video_canvas.winfo_width()
            canvas_height = self.video_canvas.winfo_height()
            if canvas_width > 1 and canvas_height > 1: # Tránh lỗi khi window chưa load xong
                frame_rgb = cv2.resize(frame_rgb, (canvas_width, canvas_height))

            image = Image.fromarray(frame_rgb)
            photo = ImageTk.PhotoImage(image=image)

            self.video_canvas.delete("all")
            self.video_canvas.create_image(0, 0, image=photo, anchor="nw")
            self.video_canvas.image = photo # Giữ tham chiếu
        except Exception as e:
            pass
    
    def _start_audio_streaming(self):
        """Bắt đầu audio streaming"""
        try:
            # PyAudio setup
            p = pyaudio.PyAudio()
            
            # Input stream (microphone)
            if not self.is_muted:
                self.audio_stream = p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=44100,
                    input=True,
                    frames_per_buffer=1024,
                    stream_callback=self._audio_callback
                )
                self.audio_stream.start_stream()
            
            # Output stream (speaker) - để nhận audio từ peer
            self.audio_output = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                output=True,
                frames_per_buffer=1024
            )
            
        except Exception as e:
            print(f"Audio streaming error: {e}")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback xử lý audio: Thu từ mic -> Gửi đi"""
        if self.call_active and not self.is_muted:
            try:
                # Mã hóa dữ liệu âm thanh raw sang Base64
                data_str = base64.b64encode(in_data).decode('utf-8')
                
                # Gửi qua socket
                # Lưu ý: socket.sendall an toàn với thread trong Python
                from common.protocol import Protocol, MessageType
                Protocol.send_message(
                    self.client.socket,
                    MessageType.AUDIO_DATA,
                    {
                        "recipient": self.peer,
                        "data": data_str
                    }
                )
            except Exception as e:
                # Không print lỗi liên tục để tránh spam console
                pass
                
        return (in_data, pyaudio.paContinue)
    
    # Thêm các hàm này vào class CallUI

    def process_incoming_video(self, data_str):
        """Xử lý video nhận được từ đối phương"""
        try:
            # Đánh dấu là đã có video từ peer (để ngừng hiển thị local mirror)
            self.has_peer_video = True
            
            # Decode Base64 -> Bytes
            img_data = base64.b64decode(data_str)
            
            # Bytes -> Numpy Array
            np_arr = np.frombuffer(img_data, dtype=np.uint8)
            
            # Decode JPEG -> Frame
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if frame is not None:
                self._render_frame_to_canvas(frame)
                
                # Xóa placeholder text nếu còn
                if hasattr(self, 'placeholder_text'):
                    self.video_canvas.delete(self.placeholder_text)
                    del self.placeholder_text
                    
        except Exception as e:
            print(f"Decode video error: {e}")

    def process_incoming_audio(self, data_str):
        """Xử lý audio nhận được từ đối phương"""
        try:
            if self.audio_output:
                # Decode Base64 -> Raw bytes
                audio_data = base64.b64decode(data_str)
                # Phát ra loa
                self.audio_output.write(audio_data)
        except Exception as e:
            print(f"Decode audio error: {e}")

    def _update_timer(self):
        """Cập nhật bộ đếm thời gian"""
        if self.call_active and self.start_time:
            elapsed = int(time.time() - self.start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
            
            self.window.after(1000, self._update_timer)
    
    def _toggle_mute(self):
        """Bật/tắt mic"""
        self.is_muted = not self.is_muted
        
        if self.is_muted:
            self.mute_btn.config(bg="#ff3b30", text="🔇")
            if self.audio_stream:
                self.audio_stream.stop_stream()
        else:
            self.mute_btn.config(bg="#333333", text="🎤")
            if self.audio_stream:
                self.audio_stream.start_stream()
    
    def _toggle_camera(self):
        """Bật/tắt camera"""
        self.is_camera_on = not self.is_camera_on
        
        if self.is_camera_on:
            self.camera_btn.config(bg="#333333", text="📹")
            if not self.video_capture:
                self._start_video_capture()
        else:
            self.camera_btn.config(bg="#ff3b30", text="📵")
            if self.video_capture:
                self.video_capture.release()
                self.video_capture = None
            
            # Show camera off message
            self.video_canvas.delete("all")
            self.video_canvas.create_text(
                320, 240,
                text="📵 Camera tắt",
                font=("Arial", 24),
                fill="#666666"
            )
    
    def _cleanup_media(self):
        """Dọn dẹp media resources"""
        self.call_active = False
        
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
        
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
        
        if self.audio_output:
            self.audio_output.close()
            self.audio_output = None
    
    def on_call_accepted(self):
        """Được gọi khi cuộc gọi được chấp nhận"""
        self._start_call_session()
    
    def on_call_rejected(self):
        """Được gọi khi cuộc gọi bị từ chối"""
        self.status_label.config(text=f"{self.peer} đã từ chối cuộc gọi")
        self.window.after(2000, lambda: (self._cleanup_media(), self.window.destroy()))
        if self.client.current_call == self:
            self.client.current_call = None
    
    def on_call_ended(self):
        """Được gọi khi cuộc gọi kết thúc từ phía đối phương"""
        self.call_active = False
        self.status_label.config(text="Cuộc gọi đã kết thúc")
        self.window.after(2000, lambda: (self._cleanup_media(), self.window.destroy()))
        if self.client.current_call == self:
            self.client.current_call = None