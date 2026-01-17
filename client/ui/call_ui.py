"""
Giao diện Video/Audio Call
"""

from tkinter import Frame, Label, Button, Toplevel
from tkinter import CENTER, BOTH
from common.protocol import Protocol, MessageType
import time

class CallUI:
    def __init__(self, client, peer_username, call_type, is_caller=False):
        self.client = client
        self.peer = peer_username
        self.call_type = call_type  # "video" or "audio"
        self.is_caller = is_caller
        self.colors = client.colors
        self.call_active = False
        self.start_time = None
        
        # Tạo cửa sổ call
        self.window = Toplevel(client.root)
        self.window.title(f"{'Video' if call_type == 'video' else 'Audio'} Call")
        self.window.geometry("600x500" if call_type == "video" else "400x300")
        self.window.resizable(False, False)
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 if call_type == "video" else 400) // 2
        y = (self.window.winfo_screenheight() // 2) - (500 if call_type == "video" else 300) // 2
        self.window.geometry(f"{'600x500' if call_type == 'video' else '400x300'}+{x}+{y}")
        
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
        # Video placeholder (if video call)
        if self.call_type == "video":
            video_frame = Frame(self.main_container, bg="#000000", height=350)
            video_frame.pack(fill="x", padx=20, pady=20)
            video_frame.pack_propagate(False)
            
            Label(
                video_frame,
                text="📹",
                font=("Arial", 80),
                bg="#000000",
                fg="#666666"
            ).place(relx=0.5, rely=0.5, anchor=CENTER)
        
        # Status
        self.status_label = Label(
            self.main_container,
            text=f"Đang gọi {self.peer}...",
            font=("Arial", 16),
            bg="#1a1a1a",
            fg="white"
        )
        self.status_label.pack(pady=20)
        
        # Timer (hidden initially)
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
        
        # Reject button
        reject_btn = Button(
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
        )
        reject_btn.pack(side="left", padx=20)
        
        # Accept button
        accept_btn = Button(
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
        )
        accept_btn.pack(side="left", padx=20)
    
    def _create_call_controls(self):
        """Tạo các nút điều khiển cuộc gọi"""
        controls_frame = Frame(self.main_container, bg="#1a1a1a")
        controls_frame.pack(pady=20)
        
        # Mute button (if audio/video)
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
        # Gửi ACCEPT về server
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
        
        self.window.destroy()
        if self.client.current_call == self:
            self.client.current_call = None
    
    def _start_call_session(self):
        """Bắt đầu phiên gọi"""
        self.call_active = True
        self.start_time = time.time()
        
        # Update status
        self.status_label.config(text=f"Đang gọi với {self.peer}")
        
        # Show timer
        self.timer_label.pack(pady=5)
        self._update_timer()
    
    def _update_timer(self):
        """Cập nhật bộ đếm thời gian"""
        if self.call_active and self.start_time:
            elapsed = int(time.time() - self.start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
            
            # Update every second
            self.window.after(1000, self._update_timer)
    
    def _toggle_mute(self):
        """Bật/tắt mic"""
        # Placeholder - tích hợp WebRTC sau
        current_bg = self.mute_btn.cget("bg")
        if current_bg == "#333333":
            self.mute_btn.config(bg="#ff3b30", text="🔇")
        else:
            self.mute_btn.config(bg="#333333", text="🎤")
    
    def _toggle_camera(self):
        """Bật/tắt camera"""
        # Placeholder - tích hợp WebRTC sau
        current_bg = self.camera_btn.cget("bg")
        if current_bg == "#333333":
            self.camera_btn.config(bg="#ff3b30", text="📵")
        else:
            self.camera_btn.config(bg="#333333", text="📹")
    
    def on_call_accepted(self):
        """Được gọi khi cuộc gọi được chấp nhận"""
        self._start_call_session()
    
    def on_call_rejected(self):
        """Được gọi khi cuộc gọi bị từ chối"""
        self.status_label.config(text=f"{self.peer} đã từ chối cuộc gọi")
        self.window.after(2000, self.window.destroy)
        if self.client.current_call == self:
            self.client.current_call = None
    
    def on_call_ended(self):
        """Được gọi khi cuộc gọi kết thúc từ phía đối phương"""
        self.call_active = False
        self.status_label.config(text="Cuộc gọi đã kết thúc")
        self.window.after(2000, self.window.destroy)
        if self.client.current_call == self:
            self.client.current_call = None