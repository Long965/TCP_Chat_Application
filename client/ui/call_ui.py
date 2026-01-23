"""
client/ui/call_ui.py - Full Logic Video Call + Dark Mode UI
"""
from tkinter import Frame, Label, Button, Toplevel, Canvas, BOTH, CENTER
import time
import threading
import base64
from PIL import Image, ImageTk
from common.config import Colors, UISettings
from common.protocol import Protocol, MessageType

# WebRTC imports (OpenCV + PyAudio)
try:
    import cv2
    import numpy as np
    import pyaudio
    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False
    print("⚠️ WebRTC dependencies not available. Install: pip install opencv-python pyaudio pillow numpy")

class CallUI:
    def __init__(self, client, peer_username, call_type, is_caller=False):
        self.client = client
        self.peer = peer_username
        self.call_type = call_type  # "video" or "audio"
        self.is_caller = is_caller
        self.call_active = False
        self.start_time = None
        
        # WebRTC components
        self.video_capture = None
        self.audio_stream = None
        self.audio_output = None
        self.is_muted = False
        self.is_camera_on = True
        
        # Setup Window
        self.window = Toplevel(client.root)
        self.window.title(f"{'Video' if call_type == 'video' else 'Audio'} Call - {peer_username}")
        self.window.configure(bg=Colors.BG_MAIN)
        
        # Kích thước cửa sổ
        w, h = (800, 650) if call_type == "video" else (400, 350)
        x = (self.window.winfo_screenwidth() // 2) - (w // 2)
        y = (self.window.winfo_screenheight() // 2) - (h // 2)
        self.window.geometry(f"{w}x{h}+{x}+{y}")
        
        # Main Container
        self.main_container = Frame(self.window, bg=Colors.BG_MAIN)
        self.main_container.pack(fill=BOTH, expand=True)
        
        # Render UI tương ứng
        if is_caller:
            self._create_calling_ui()
        else:
            self._create_incoming_ui()
        
        # Lưu tham chiếu để Handler gọi
        self.client.current_call = self
        
        # Xử lý khi đóng cửa sổ
        self.window.protocol("WM_DELETE_WINDOW", self._end_call)

    def _create_calling_ui(self):
        """Giao diện đang gọi đi"""
        # Video Canvas
        if self.call_type == "video":
            self.video_canvas = Canvas(self.main_container, bg="black", width=640, height=480, highlightthickness=0)
            self.video_canvas.pack(pady=20)
            
            self.placeholder_text = self.video_canvas.create_text(
                320, 240, text="📷 Đang kết nối...", font=UISettings.FONT_HEADER, fill="gray"
            )
        else:
            # Avatar placeholder cho Audio call
            Label(self.main_container, text="👤", font=("Arial", 80), bg=Colors.BG_MAIN, fg=Colors.TEXT_SECONDARY).pack(pady=40)

        # Info
        Label(self.main_container, text=f"Đang gọi {self.peer}...", font=UISettings.FONT_HEADER, 
              bg=Colors.BG_MAIN, fg=Colors.TEXT_PRIMARY).pack(pady=10)
        
        # Timer (ẩn lúc đầu)
        self.timer_label = Label(self.main_container, text="00:00", font=UISettings.FONT_NORMAL, 
                                 bg=Colors.BG_MAIN, fg=Colors.TEXT_SECONDARY)
        self.timer_label.pack(pady=5)
        self.timer_label.pack_forget()

        # Controls
        self._create_call_controls()

    def _create_incoming_ui(self):
        """Giao diện nhận cuộc gọi"""
        # Placeholder
        Label(self.main_container, text="📞", font=("Arial", 80), bg=Colors.BG_MAIN, fg=Colors.ACCENT).pack(pady=50)
        
        # Info
        Label(self.main_container, text=f"{self.peer}", font=UISettings.FONT_TITLE, 
              bg=Colors.BG_MAIN, fg=Colors.TEXT_PRIMARY).pack(pady=10)
        
        Label(self.main_container, text=f"Cuộc gọi {'Video' if self.call_type == 'video' else 'Thoại'} đến...", 
              font=UISettings.FONT_NORMAL, bg=Colors.BG_MAIN, fg=Colors.TEXT_SECONDARY).pack(pady=5)

        # Buttons Frame
        btn_frame = Frame(self.main_container, bg=Colors.BG_MAIN)
        btn_frame.pack(pady=40)

        # Từ chối
        Button(btn_frame, text="❌ Từ chối", font=UISettings.FONT_HEADER, bg=Colors.ERROR, fg="white", 
               bd=0, padx=20, pady=10, cursor="hand2", command=self._reject_call).pack(side="left", padx=20)
        
        # Chấp nhận
        Button(btn_frame, text="📞 Nghe máy", font=UISettings.FONT_HEADER, bg=Colors.SUCCESS, fg="white", 
               bd=0, padx=20, pady=10, cursor="hand2", command=self._accept_call).pack(side="left", padx=20)

    def _create_call_controls(self):
        """Thanh điều khiển (Mute, Cam, End)"""
        controls_frame = Frame(self.main_container, bg=Colors.BG_SIDEBAR, pady=15)
        controls_frame.pack(side="bottom", fill="x")
        
        # Frame giữa để căn giữa các nút
        center_frame = Frame(controls_frame, bg=Colors.BG_SIDEBAR)
        center_frame.pack()

        # Mute Btn
        self.mute_btn = Button(center_frame, text="🎤", font=("Arial", 16), bg=Colors.BG_HOVER, fg="white", 
                               bd=0, width=4, cursor="hand2", command=self._toggle_mute)
        self.mute_btn.pack(side="left", padx=15)

        # Camera Btn (Only Video)
        if self.call_type == "video":
            self.camera_btn = Button(center_frame, text="📷", font=("Arial", 16), bg=Colors.BG_HOVER, fg="white", 
                                     bd=0, width=4, cursor="hand2", command=self._toggle_camera)
            self.camera_btn.pack(side="left", padx=15)

        # End Call Btn
        Button(center_frame, text="📞", font=("Arial", 16), bg=Colors.ERROR, fg="white", 
               bd=0, width=4, cursor="hand2", command=self._end_call).pack(side="left", padx=15)

    # --- LOGIC XỬ LÝ CHÍNH ---
    
    def _accept_call(self):
        Protocol.send_message(self.client.socket, MessageType.CALL_ACCEPT, 
                              {"caller": self.peer, "recipient": self.client.username})
        
        # Reset UI sang chế độ đang gọi
        for widget in self.main_container.winfo_children(): widget.destroy()
        
        if self.call_type == "video":
            self.video_canvas = Canvas(self.main_container, bg="black", width=640, height=480, highlightthickness=0)
            self.video_canvas.pack(pady=20)
        else:
            Label(self.main_container, text="👤", font=("Arial", 80), bg=Colors.BG_MAIN, fg=Colors.TEXT_SECONDARY).pack(pady=40)

        self.status_label = Label(self.main_container, text=f"Đang gọi {self.peer}", font=UISettings.FONT_HEADER, 
                                  bg=Colors.BG_MAIN, fg=Colors.TEXT_PRIMARY)
        self.status_label.pack(pady=10)
        
        self.timer_label = Label(self.main_container, text="00:00", font=UISettings.FONT_NORMAL, 
                                 bg=Colors.BG_MAIN, fg=Colors.TEXT_SECONDARY)
        self.timer_label.pack(pady=5)
        
        self._create_call_controls()
        self._start_call_session()

    def _reject_call(self):
        Protocol.send_message(self.client.socket, MessageType.CALL_REJECT, 
                              {"caller": self.peer, "recipient": self.client.username})
        self._cleanup_media()
        self.window.destroy()
        if self.client.current_call == self: self.client.current_call = None

    def _end_call(self):
        if self.call_active:
            Protocol.send_message(self.client.socket, MessageType.CALL_END, {"peer": self.peer})
        self._cleanup_media()
        self.window.destroy()
        if self.client.current_call == self: self.client.current_call = None

    def _start_call_session(self):
        self.call_active = True
        self.start_time = time.time()
        self._update_timer()
        
        if WEBRTC_AVAILABLE:
            threading.Thread(target=self._start_media_streaming, daemon=True).start()
        else:
            if hasattr(self, 'status_label'):
                self.status_label.config(text="⚠️ Thiếu thư viện WebRTC (opencv, pyaudio)", fg=Colors.WARNING)

    # --- MEDIA STREAMING (OpenCV + PyAudio) ---
    
    def _start_media_streaming(self):
        try:
            if self.call_type == "video" and self.is_camera_on: self._start_video_capture()
            self._start_audio_streaming()
        except Exception as e:
            print(f"Media Error: {e}")

    def _start_video_capture(self):
        try:
            self.video_capture = cv2.VideoCapture(0)
            if not self.video_capture.isOpened(): raise Exception("No Webcam")
            
            self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            if hasattr(self, 'placeholder_text'): 
                self.video_canvas.delete(self.placeholder_text)
            
            # Bắt đầu vòng lặp update frame
            self._update_video_frame()
            
        except Exception as e:
            print(f"Cam Error: {e}")

    def _update_video_frame(self):
        if not self.call_active or not self.is_camera_on: return
        try:
            ret, frame = self.video_capture.read()
            if ret:
                # 1. Local Mirror (Hiển thị phía mình)
                if not hasattr(self, 'has_peer_video') or not self.has_peer_video:
                    self._render_frame_to_canvas(frame)
                
                # 2. Gửi đi (Resize 320x240 để tối ưu tốc độ mạng TCP)
                frame_small = cv2.resize(frame, (320, 240))
                # Nén JPEG chất lượng 50
                _, buffer = cv2.imencode('.jpg', frame_small, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                # Encode Base64
                jpg_as_text = base64.b64encode(buffer).decode('utf-8')
                
                Protocol.send_message(self.client.socket, MessageType.VIDEO_DATA, 
                                      {"recipient": self.peer, "data": jpg_as_text})
            
            # Gọi lại sau 30ms (~33 FPS)
            self.window.after(30, self._update_video_frame) 
        except Exception as e: 
            print(f"Video Loop Error: {e}")

    def _render_frame_to_canvas(self, frame):
        try:
            # Convert BGR (OpenCV) -> RGB (Tkinter)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Nếu chưa có video người kia thì lật gương camera mình cho tự nhiên
            if not hasattr(self, 'has_peer_video'): 
                frame_rgb = cv2.flip(frame_rgb, 1) 
            
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            
            if hasattr(self, 'video_canvas'):
                self.video_canvas.create_image(0, 0, image=imgtk, anchor="nw")
                self.video_canvas.image = imgtk # Giữ tham chiếu để không bị Garbage Collected
        except: pass

    def _start_audio_streaming(self):
        try:
            p = pyaudio.PyAudio()
            # Input Stream (Mic)
            if not self.is_muted:
                self.audio_stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, 
                                           frames_per_buffer=1024, stream_callback=self._audio_callback)
                self.audio_stream.start_stream()
            
            # Output Stream (Loa)
            self.audio_output = p.open(format=pyaudio.paInt16, channels=1, rate=44100, output=True, frames_per_buffer=1024)
        except Exception as e:
            print(f"Audio Error: {e}")

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback thu âm thanh và gửi đi ngay lập tức"""
        if self.call_active and not self.is_muted:
            try:
                data_str = base64.b64encode(in_data).decode('utf-8')
                # Sử dụng Protocol.send_message nhưng cần thread-safe (thực tế socket.send là thread-safe)
                Protocol.send_message(self.client.socket, MessageType.AUDIO_DATA, 
                                      {"recipient": self.peer, "data": data_str})
            except: pass
        return (in_data, pyaudio.paContinue)

    # --- INCOMING DATA HANDLERS (Được gọi từ CallHandler) ---
    
    def process_incoming_video(self, data_str):
        """Nhận dữ liệu video từ server -> hiển thị"""
        try:
            self.has_peer_video = True # Đánh dấu để ngừng hiện mirror local
            
            img_data = base64.b64decode(data_str)
            np_arr = np.frombuffer(img_data, dtype=np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if frame is not None: 
                # Resize frame nhận được cho vừa canvas (640x480)
                frame = cv2.resize(frame, (640, 480))
                self._render_frame_to_canvas(frame)
        except: pass

    def process_incoming_audio(self, data_str):
        """Nhận dữ liệu audio từ server -> phát ra loa"""
        try:
            if self.audio_output:
                audio_data = base64.b64decode(data_str)
                self.audio_output.write(audio_data)
        except: pass

    # --- UTILS ---
    def _update_timer(self):
        if self.call_active and self.start_time:
            elapsed = int(time.time() - self.start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            if hasattr(self, 'timer_label'):
                self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
            self.window.after(1000, self._update_timer)

    def _toggle_mute(self):
        self.is_muted = not self.is_muted
        # Đổi màu nút khi mute
        btn_bg = Colors.ERROR if self.is_muted else Colors.BG_HOVER
        self.mute_btn.config(bg=btn_bg, text="🔇" if self.is_muted else "🎤")

    def _toggle_camera(self):
        self.is_camera_on = not self.is_camera_on
        # Đổi màu nút khi tắt cam
        btn_bg = Colors.ERROR if not self.is_camera_on else Colors.BG_HOVER
        self.camera_btn.config(bg=btn_bg, text="📵" if not self.is_camera_on else "📷")
        
    def _cleanup_media(self):
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

    # Event handlers từ MessageHandler gọi sang
    def on_call_accepted(self): 
        self._start_call_session()
        
    def on_call_rejected(self):
        if hasattr(self, 'status_label'):
            self.status_label.config(text="Bị từ chối", fg=Colors.ERROR)
        self.window.after(1500, self._end_call)
        
    def on_call_ended(self):
        if hasattr(self, 'status_label'):
            self.status_label.config(text="Đã kết thúc", fg=Colors.TEXT_SECONDARY)
        self.window.after(1500, self._end_call)