"""
Giao diện đăng nhập
"""
from tkinter import Frame, Label, Entry, Button, BOTH, W, SOLID

from common.config import DEFAULT_SERVER, UISettings

class LoginUI:
    def __init__(self, client):
        self.client = client
        self.colors = client.colors
        
        self.login_frame = Frame(self.client.root, bg=self.colors.BG_PRIMARY)
        self.login_frame.pack(fill=BOTH, expand=True)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Tạo các widgets cho login UI"""
        # Logo/Title
        title_frame = Frame(self.login_frame, bg=self.colors.BG_PRIMARY)
        title_frame.pack(pady=80)
        
        Label(
            title_frame,
            text="💬",
            font=("Arial", 60),
            bg=self.colors.BG_PRIMARY,
            fg="white"
        ).pack()
        
        Label(
            title_frame,
            text="Zalo Chat",
            font=UISettings.FONT_TITLE,
            bg=self.colors.BG_PRIMARY,
            fg="white"
        ).pack(pady=10)
        
        # Login form
        form_frame = Frame(self.login_frame, bg="white", padx=40, pady=30)
        form_frame.pack(pady=20)
        
        Label(
            form_frame,
            text="Đăng nhập",
            font=UISettings.FONT_HEADER,
            bg="white"
        ).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        Label(
            form_frame,
            text="Tên đăng nhập:",
            font=UISettings.FONT_NORMAL,
            bg="white"
        ).grid(row=1, column=0, sticky=W, pady=5)
        
        self.username_entry = Entry(
            form_frame,
            font=UISettings.FONT_NORMAL,
            width=25,
            bd=1,
            relief=SOLID
        )
        self.username_entry.grid(row=2, column=0, pady=(0, 15), ipady=8)
        self.username_entry.focus()
        
        Label(
            form_frame,
            text="Server:",
            font=UISettings.FONT_NORMAL,
            bg="white"
        ).grid(row=3, column=0, sticky=W, pady=5)
        
        self.server_entry = Entry(
            form_frame,
            font=UISettings.FONT_NORMAL,
            width=25,
            bd=1,
            relief=SOLID
        )
        self.server_entry.insert(0, DEFAULT_SERVER)
        self.server_entry.grid(row=4, column=0, pady=(0, 20), ipady=8)
        
        self.login_btn = Button(
            form_frame,
            text="Đăng nhập",
            font=("Arial", 11, "bold"),
            bg=self.colors.BG_PRIMARY,
            fg="white",
            width=25,
            height=2,
            cursor="hand2",
            bd=0,
            command=self._handle_login
        )
        self.login_btn.grid(row=5, column=0, pady=10)
        
        self.status_label = Label(
            form_frame,
            text="",
            font=UISettings.FONT_SMALL,
            bg="white",
            fg="red"
        )
        self.status_label.grid(row=6, column=0, pady=5)
        
        # Bind Enter key
        self.username_entry.bind("<Return>", lambda e: self._handle_login())
        self.server_entry.bind("<Return>", lambda e: self._handle_login())
    
    def _handle_login(self):
        """Xử lý sự kiện đăng nhập"""
        username = self.username_entry.get().strip()
        server_info = self.server_entry.get().strip()
        
        if not username:
            self.status_label.config(text="Vui lòng nhập tên đăng nhập!")
            return
        
        self.status_label.config(text="Đang kết nối...", fg="blue")
        self.login_btn.config(state="disabled")
        self.client.root.update()
        
        # Thực hiện đăng nhập
        success, message = self.client.login(username, server_info)
        
        if success:
            # Chuyển sang chat UI
            self.client.setup_chat_ui()
        else:
            self.status_label.config(text=message, fg="red")
            self.login_btn.config(state="normal")
    
    def destroy(self):
        """Hủy login UI"""
        self.login_frame.destroy()