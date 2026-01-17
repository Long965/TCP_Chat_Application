"""
Giao diện chat chính - CẬP NHẬT với avatar clickable
"""

from tkinter import Frame, Label, Button, Listbox, Text, Canvas, Scrollbar
from tkinter import LEFT, RIGHT, BOTTOM, TOP, X, Y, BOTH, W, END, WORD, SOLID
from common.config import UISettings

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  Pillow not installed. Image preview disabled.")

class ChatUI:
    def __init__(self, client):
        self.client = client
        self.colors = client.colors
        
        # Main container
        self.main_container = Frame(self.client.root, bg=self.colors.BG_SECONDARY)
        self.main_container.pack(fill=BOTH, expand=True)
        
        self._create_sidebar()
        self._create_chat_area()
    
    def _create_sidebar(self):
        """Tạo sidebar với danh sách user - CẬP NHẬT với avatar clickable"""
        sidebar = Frame(self.main_container, bg=self.colors.BG_WHITE,
                       width=UISettings.SIDEBAR_WIDTH)
        sidebar.pack(side=LEFT, fill=Y)
        sidebar.pack_propagate(False)
        
        # Sidebar header
        sidebar_header = Frame(sidebar, bg=self.colors.BG_PRIMARY,
                              height=UISettings.CHAT_HEADER_HEIGHT)
        sidebar_header.pack(fill=X)
        sidebar_header.pack_propagate(False)
        
        Label(
            sidebar_header,
            text=f"👤 {self.client.username}",
            font=("Arial", 12, "bold"),
            bg=self.colors.BG_PRIMARY,
            fg="white"
        ).pack(side=LEFT, padx=15, pady=15)
        
        # User list header
        Label(
            sidebar,
            text="Danh sách người dùng",
            font=("Arial", 10, "bold"),
            bg=self.colors.BG_WHITE,
            fg=self.colors.TEXT_SECONDARY
        ).pack(pady=10, padx=15, anchor=W)
        
        # User list container với Canvas để có thể custom
        user_container = Frame(sidebar, bg=self.colors.BG_WHITE)
        user_container.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        # Canvas và Scrollbar
        canvas = Canvas(user_container, bg=self.colors.BG_WHITE, 
                       highlightthickness=0)
        scrollbar = Scrollbar(user_container, command=canvas.yview)
        
        self.user_list_frame = Frame(canvas, bg=self.colors.BG_WHITE)
        
        scrollbar.pack(side=RIGHT, fill=Y)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas_window = canvas.create_window(
            (0, 0),
            window=self.user_list_frame,
            anchor="nw"
        )
        
        def configure_scroll(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=event.width)
        
        self.user_list_frame.bind("<Configure>", configure_scroll)
        canvas.bind("<Configure>", 
                   lambda e: canvas.itemconfig(canvas_window, width=e.width))
    
    def _create_chat_area(self):
        """Tạo khu vực chat"""
        chat_container = Frame(self.main_container, bg=self.colors.BG_WHITE)
        chat_container.pack(side=RIGHT, fill=BOTH, expand=True)
        
        # Chat header
        self._create_chat_header(chat_container)
        
        # Messages area
        self._create_messages_area(chat_container)
        
        # Input area
        self._create_input_area(chat_container)
    
    def _create_chat_header(self, parent):
        """Tạo header cho chat area"""
        chat_header = Frame(parent, bg=self.colors.BG_WHITE,
                           height=UISettings.CHAT_HEADER_HEIGHT)
        chat_header.pack(fill=X)
        chat_header.pack_propagate(False)
        
        Label(
            chat_header,
            text="💬 Trò chuyện nhóm",
            font=("Arial", 14, "bold"),
            bg=self.colors.BG_WHITE
        ).pack(side=LEFT, padx=20, pady=15)
        
        Frame(chat_header, height=1, bg="#E4E6EB").pack(side=BOTTOM, fill=X)
    
    def _create_messages_area(self, parent):
        """Tạo khu vực hiển thị messages"""
        messages_frame = Frame(parent, bg=self.colors.BG_SECONDARY)
        messages_frame.pack(fill=BOTH, expand=True, padx=15, pady=10)
        
        # Canvas + Scrollbar
        msg_canvas = Canvas(messages_frame, bg=self.colors.BG_SECONDARY,
                           highlightthickness=0)
        msg_scrollbar = Scrollbar(messages_frame, command=msg_canvas.yview)
        
        self.messages_container = Frame(msg_canvas, bg=self.colors.BG_SECONDARY)
        
        msg_scrollbar.pack(side=RIGHT, fill=Y)
        msg_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        msg_canvas.configure(yscrollcommand=msg_scrollbar.set)
        
        canvas_frame = msg_canvas.create_window(
            (0, 0),
            window=self.messages_container,
            anchor="nw"
        )
        
        def configure_scroll(event):
            msg_canvas.configure(scrollregion=msg_canvas.bbox("all"))
            msg_canvas.itemconfig(canvas_frame, width=event.width)
            msg_canvas.yview_moveto(1.0)
        
        self.messages_container.bind("<Configure>", configure_scroll)
        msg_canvas.bind("<Configure>",
                       lambda e: msg_canvas.itemconfig(canvas_frame, width=e.width))
    
    def _create_input_area(self, parent):
        """Tạo khu vực nhập tin nhắn"""
        input_container = Frame(parent, bg=self.colors.BG_WHITE,
                               height=UISettings.INPUT_AREA_HEIGHT)
        input_container.pack(fill=X, side=BOTTOM)
        input_container.pack_propagate(False)
        
        Frame(input_container, height=1, bg="#E4E6EB").pack(fill=X)
        
        input_frame = Frame(input_container, bg=self.colors.BG_WHITE)
        input_frame.pack(fill=BOTH, expand=True, padx=15, pady=10)
        
        # Buttons frame
        self._create_action_buttons(input_frame)
        
        # Message input
        self.message_entry = Text(
            input_frame,
            height=2,
            font=UISettings.FONT_NORMAL,
            bg=self.colors.BG_SECONDARY,
            fg=self.colors.TEXT_PRIMARY,
            bd=0,
            wrap=WORD,
            padx=10,
            pady=8
        )
        self.message_entry.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))
        self.message_entry.focus()
        
        # Send button
        self.send_btn = Button(
            input_frame,
            text="➤",
            font=("Arial", 16, "bold"),
            bg=self.colors.BG_PRIMARY,
            fg="white",
            width=3,
            bd=0,
            cursor="hand2",
            command=self._handle_send_text
        )
        self.send_btn.pack(side=RIGHT)
        
        # Bind Enter
        self.message_entry.bind("<Return>",
                               lambda e: self._handle_send_text() or "break")
        self.message_entry.bind("<Shift-Return>", lambda e: None)
    
    def _create_action_buttons(self, parent):
        """Tạo các nút hành động (gửi file, ảnh, video)"""
        buttons_frame = Frame(parent, bg=self.colors.BG_WHITE)
        buttons_frame.pack(side=LEFT, padx=(0, 10))
        
        Button(
            buttons_frame,
            text="📎",
            font=("Arial", 16),
            bg=self.colors.BG_WHITE,
            fg=self.colors.BG_PRIMARY,
            bd=0,
            cursor="hand2",
            command=self.client.file_handler.send_file
        ).pack(side=LEFT, padx=2)
        
        if PIL_AVAILABLE:
            Button(
                buttons_frame,
                text="🖼️",
                font=("Arial", 16),
                bg=self.colors.BG_WHITE,
                fg=self.colors.BG_PRIMARY,
                bd=0,
                cursor="hand2",
                command=self.client.file_handler.send_image
            ).pack(side=LEFT, padx=2)
            
            Button(
                buttons_frame,
                text="🎬",
                font=("Arial", 16),
                bg=self.colors.BG_WHITE,
                fg=self.colors.BG_PRIMARY,
                bd=0,
                cursor="hand2",
                command=self.client.file_handler.send_video
            ).pack(side=LEFT, padx=2)
    
    def _handle_send_text(self):
        """Xử lý gửi tin nhắn text"""
        message = self.message_entry.get("1.0", END).strip()
        
        if not message:
            return
        
        if self.client.send_text_message(message):
            # Hiển thị tin nhắn của mình
            from datetime import datetime
            self.client.message_handler.display_text_message({
                "sender": self.client.username,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Clear input
            self.message_entry.delete("1.0", END)
    
    def update_user_list(self, users):
        """Cập nhật danh sách user với avatar clickable"""
        # Xóa tất cả widgets cũ
        for widget in self.user_list_frame.winfo_children():
            widget.destroy()
        
        # Tạo lại danh sách user
        for user in users:
            if user == self.client.username:
                continue  # Không hiển thị bản thân
            
            self._create_user_item(user)
    
    def _create_user_item(self, username):
        """Tạo item user với avatar clickable"""
        user_frame = Frame(self.user_list_frame, bg=self.colors.BG_WHITE,
                          cursor="hand2")
        user_frame.pack(fill=X, pady=3, padx=5)
        
        # Hover effect
        def on_enter(e):
            user_frame.config(bg=self.colors.BG_SECONDARY)
            for child in user_frame.winfo_children():
                if isinstance(child, (Label, Frame)):
                    child.config(bg=self.colors.BG_SECONDARY)
        
        def on_leave(e):
            user_frame.config(bg=self.colors.BG_WHITE)
            for child in user_frame.winfo_children():
                if isinstance(child, (Label, Frame)):
                    child.config(bg=self.colors.BG_WHITE)
        
        def on_click(e):
            self._open_private_chat(username)
        
        user_frame.bind("<Enter>", on_enter)
        user_frame.bind("<Leave>", on_leave)
        user_frame.bind("<Button-1>", on_click)
        
        # Container cho avatar và tên
        content_frame = Frame(user_frame, bg=self.colors.BG_WHITE)
        content_frame.pack(fill=X, padx=10, pady=8)
        content_frame.bind("<Button-1>", on_click)
        
        # Avatar
        avatar_label = Label(
            content_frame,
            text="👤",
            font=("Arial", 20),
            bg=self.colors.BG_WHITE,
            fg=self.colors.BG_PRIMARY
        )
        avatar_label.pack(side=LEFT, padx=(0, 10))
        avatar_label.bind("<Button-1>", on_click)
        
        # Username và status
        info_frame = Frame(content_frame, bg=self.colors.BG_WHITE)
        info_frame.pack(side=LEFT, fill=X, expand=True)
        info_frame.bind("<Button-1>", on_click)
        
        username_label = Label(
            info_frame,
            text=username,
            font=("Arial", 11, "bold"),
            bg=self.colors.BG_WHITE,
            fg=self.colors.TEXT_PRIMARY,
            anchor=W
        )
        username_label.pack(fill=X)
        username_label.bind("<Button-1>", on_click)
        
        status_label = Label(
            info_frame,
            text="🟢 Online",
            font=("Arial", 8),
            bg=self.colors.BG_WHITE,
            fg="green",
            anchor=W
        )
        status_label.pack(fill=X)
        status_label.bind("<Button-1>", on_click)
    
    def _open_private_chat(self, username):
        """Mở cửa sổ chat riêng với user"""
        # Kiểm tra xem đã mở chưa
        if username in self.client.private_chats:
            # Focus vào cửa sổ đã mở
            self.client.private_chats[username].window.lift()
            self.client.private_chats[username].window.focus_force()
        else:
            # Tạo cửa sổ chat mới
            from client.ui.private_chat_ui import PrivateChatUI
            private_chat = PrivateChatUI(self.client, username)
            self.client.private_chats[username] = private_chat