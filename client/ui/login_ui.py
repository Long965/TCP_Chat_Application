"""
client/ui/login_ui.py
"""
from tkinter import Frame, Label, Entry, Button, messagebox, SOLID
from common.config import Colors, UISettings

class LoginUI(Frame):
    def __init__(self, client):
        super().__init__(client.root, bg=Colors.BG_MAIN)
        self.client = client
        self._create_widgets()

    def _create_widgets(self):
        # Card Container (Khung đăng nhập)
        # Light Mode: Dùng màu nền trắng, thêm viền nhẹ
        card = Frame(self, bg="#FFFFFF", padx=40, pady=40)
        card.place(relx=0.5, rely=0.5, anchor="center")
        
        # Viền đổ bóng giả lập bằng highlight
        card.configure(highlightbackground=Colors.BORDER_LIGHT, highlightthickness=1)

        # Logo
        Label(card, text="💬", font=("Segoe UI Emoji", 50), 
              bg="#FFFFFF", fg=Colors.ACCENT).pack(pady=(0, 10))
        
        Label(card, text="TCP Chat", font=UISettings.FONT_TITLE,
              bg="#FFFFFF", fg=Colors.TEXT_PRIMARY).pack(pady=(0, 5))

        # Inputs
        # Username
        Label(card, text="Tên hiển thị", font=("Segoe UI", 10, "bold"),
              bg="#FFFFFF", fg=Colors.TEXT_PRIMARY, anchor="w").pack(fill="x")
        
        self.username_entry = Entry(card, font=UISettings.FONT_NORMAL, width=30,
                                    bd=1, relief=SOLID, bg=Colors.INPUT_BG,
                                    fg=Colors.TEXT_PRIMARY, insertbackground="black") # [FIX] Con trỏ màu đen
        self.username_entry.pack(pady=(5, 15), ipady=5)
        self.username_entry.focus()

        # Server IP
        Label(card, text="Server IP", font=("Segoe UI", 10, "bold"),
              bg="#FFFFFF", fg=Colors.TEXT_PRIMARY, anchor="w").pack(fill="x")
        
        self.server_entry = Entry(card, font=UISettings.FONT_NORMAL, width=30,
                                  bd=1, relief=SOLID, bg=Colors.INPUT_BG,
                                  fg=Colors.TEXT_PRIMARY, insertbackground="black") # [FIX] Con trỏ màu đen
        self.server_entry.insert(0, "127.0.0.1:5555")
        self.server_entry.pack(pady=(5, 25), ipady=5)

        # Button
        Button(card, text="ĐĂNG NHẬP", font=("Segoe UI", 11, "bold"),
               bg=Colors.ACCENT, fg="white", bd=0, cursor="hand2", pady=10,
               command=self._handle_login).pack(fill="x")

        self.username_entry.bind("<Return>", lambda e: self._handle_login())

    def _handle_login(self):
        self.client.connect_to_server(self.username_entry.get().strip(), self.server_entry.get().strip())

    def show_error(self, message):
        messagebox.showerror("Lỗi", message)