"""
Giao diện chat chính - Chat riêng tích hợp trong cùng cửa sổ
"""

from tkinter import Frame, Label, Button, Text, Canvas, Scrollbar
from tkinter import LEFT, RIGHT, BOTTOM, TOP, X, Y, BOTH, W, END, WORD
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
        self.current_chat = None  # None = group chat, "username" = private chat
        
        # Main container
        self.main_container = Frame(self.client.root, bg=self.colors.BG_SECONDARY)
        self.main_container.pack(fill=BOTH, expand=True)
        
        self._create_sidebar()
        self._create_chat_area()
    
    def _create_sidebar(self):
        """Tạo sidebar với danh sách user"""
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
        
        # Group chat button
        group_btn_frame = Frame(sidebar, bg=self.colors.BG_WHITE)
        group_btn_frame.pack(fill=X, pady=10, padx=10)
        
        self.group_chat_btn = Button(
            group_btn_frame,
            text="💬 Trò chuyện nhóm",
            font=("Arial", 10, "bold"),
            bg=self.colors.BG_PRIMARY,
            fg="white",
            bd=0,
            cursor="hand2",
            pady=10,
            command=self._switch_to_group_chat
        )
        self.group_chat_btn.pack(fill=X)
        
        # User list header
        Label(
            sidebar,
            text="Danh sách người dùng",
            font=("Arial", 10, "bold"),
            bg=self.colors.BG_WHITE,
            fg=self.colors.TEXT_SECONDARY
        ).pack(pady=10, padx=15, anchor=W)
        
        # User list container
        user_container = Frame(sidebar, bg=self.colors.BG_WHITE)
        user_container.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
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
        self.chat_header = Frame(parent, bg=self.colors.BG_WHITE,
                                height=UISettings.CHAT_HEADER_HEIGHT)
        self.chat_header.pack(fill=X)
        self.chat_header.pack_propagate(False)
        
        # Title (sẽ thay đổi theo chat mode)
        self.chat_title = Label(
            self.chat_header,
            text="💬 Trò chuyện nhóm",
            font=("Arial", 14, "bold"),
            bg=self.colors.BG_WHITE
        )
        self.chat_title.pack(side=LEFT, padx=20, pady=15)
        
        # Call buttons frame (ẩn khi ở group chat)
        self.call_buttons_frame = Frame(self.chat_header, bg=self.colors.BG_WHITE)
        self.call_buttons_frame.pack(side=RIGHT, padx=20)
        
        # Video call button
        self.video_call_btn = Button(
            self.call_buttons_frame,
            text="📹",
            font=("Arial", 18),
            bg=self.colors.BG_WHITE,
            fg=self.colors.BG_PRIMARY,
            bd=0,
            cursor="hand2",
            command=lambda: self._start_call("video")
        )
        self.video_call_btn.pack(side=LEFT, padx=5)
        
        # Audio call button
        self.audio_call_btn = Button(
            self.call_buttons_frame,
            text="📞",
            font=("Arial", 18),
            bg=self.colors.BG_WHITE,
            fg=self.colors.BG_PRIMARY,
            bd=0,
            cursor="hand2",
            command=lambda: self._start_call("audio")
        )
        self.audio_call_btn.pack(side=LEFT, padx=5)
        
        # Ẩn call buttons ban đầu
        self.call_buttons_frame.pack_forget()
        
        Frame(self.chat_header, height=1, bg="#E4E6EB").pack(side=BOTTOM, fill=X)
    
    def _create_messages_area(self, parent):
        """Tạo khu vực hiển thị messages"""
        messages_frame = Frame(parent, bg=self.colors.BG_SECONDARY)
        messages_frame.pack(fill=BOTH, expand=True, padx=15, pady=10)
        
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
        """Tạo các nút hành động"""
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
        """Xử lý gửi tin nhắn"""
        message = self.message_entry.get("1.0", END).strip()
        
        if not message:
            return
        
        # Gửi với hoặc không recipient tùy mode
        if self.client.send_text_message(message, self.current_chat):
            from datetime import datetime
            self.client.message_handler.display_message_in_current_view({
                "sender": self.client.username,
                "recipient": self.current_chat,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
            
            self.message_entry.delete("1.0", END)
    
    def update_user_list(self, users):
        """Cập nhật danh sách user với avatar clickable"""
        for widget in self.user_list_frame.winfo_children():
            widget.destroy()
        
        for user in users:
            if user == self.client.username:
                continue
            
            self._create_user_item(user)
    
    def _create_user_item(self, username):
        """Tạo item user với avatar clickable"""
        # Kiểm tra xem đang chat với user này không
        is_active = (self.current_chat == username)
        
        user_frame = Frame(
            self.user_list_frame, 
            bg=self.colors.BG_SECONDARY if is_active else self.colors.BG_WHITE,
            cursor="hand2"
        )
        user_frame.pack(fill=X, pady=3, padx=5)
        
        def on_enter(e):
            if not is_active:
                user_frame.config(bg=self.colors.BG_SECONDARY)
                for child in user_frame.winfo_children():
                    if isinstance(child, (Label, Frame)):
                        child.config(bg=self.colors.BG_SECONDARY)
        
        def on_leave(e):
            if not is_active:
                user_frame.config(bg=self.colors.BG_WHITE)
                for child in user_frame.winfo_children():
                    if isinstance(child, (Label, Frame)):
                        child.config(bg=self.colors.BG_WHITE)
        
        def on_click(e):
            self._switch_to_private_chat(username)
        
        user_frame.bind("<Enter>", on_enter)
        user_frame.bind("<Leave>", on_leave)
        user_frame.bind("<Button-1>", on_click)
        
        content_frame = Frame(user_frame, bg=user_frame.cget("bg"))
        content_frame.pack(fill=X, padx=10, pady=8)
        content_frame.bind("<Button-1>", on_click)
        
        avatar_label = Label(
            content_frame,
            text="👤",
            font=("Arial", 20),
            bg=content_frame.cget("bg"),
            fg=self.colors.BG_PRIMARY
        )
        avatar_label.pack(side=LEFT, padx=(0, 10))
        avatar_label.bind("<Button-1>", on_click)
        
        info_frame = Frame(content_frame, bg=content_frame.cget("bg"))
        info_frame.pack(side=LEFT, fill=X, expand=True)
        info_frame.bind("<Button-1>", on_click)
        
        username_label = Label(
            info_frame,
            text=username,
            font=("Arial", 11, "bold"),
            bg=info_frame.cget("bg"),
            fg=self.colors.TEXT_PRIMARY,
            anchor=W
        )
        username_label.pack(fill=X)
        username_label.bind("<Button-1>", on_click)
        
        status_label = Label(
            info_frame,
            text="🟢 Online",
            font=("Arial", 8),
            bg=info_frame.cget("bg"),
            fg="green",
            anchor=W
        )
        status_label.pack(fill=X)
        status_label.bind("<Button-1>", on_click)
    
    def _switch_to_group_chat(self):
        """Chuyển sang chế độ chat nhóm"""
        self.current_chat = None
        self.chat_title.config(text="💬 Trò chuyện nhóm")
        self.call_buttons_frame.pack_forget()
        
        # Clear messages và load lại group messages
        self._clear_messages()
        self._load_group_messages()
        
        # Update user list để bỏ highlight
        self.update_user_list(self.client.users)
        
        # Update group chat button
        self.group_chat_btn.config(bg=self.colors.BG_PRIMARY)
    
    def _switch_to_private_chat(self, username):
        """Chuyển sang chế độ chat riêng"""
        self.current_chat = username
        self.chat_title.config(text=f"💬 Chat với {username}")
        self.call_buttons_frame.pack(side=RIGHT, padx=20)
        
        # Clear messages và load lại private messages
        self._clear_messages()
        self._load_private_messages(username)
        
        # Update user list để highlight user đang chat
        self.update_user_list(self.client.users)
        
        # Update group chat button
        self.group_chat_btn.config(bg=self.colors.BG_WHITE)
    
    def _clear_messages(self):
        """Xóa tất cả messages hiện tại"""
        for widget in self.messages_container.winfo_children():
            widget.destroy()
    
    def _load_group_messages(self):
        """Load lại messages của group chat"""
        for msg in self.client.messages:
            if not msg.get("recipient"):  # Chỉ load tin nhắn không có recipient
                self.client.message_handler.display_message_in_current_view(msg)
    
    def _load_private_messages(self, username):
        """Load lại messages với user cụ thể"""
        for msg in self.client.messages:
            sender = msg.get("sender")
            recipient = msg.get("recipient")
            
            # Hiển thị nếu tin nhắn giữa mình và user
            if (sender == username and recipient == self.client.username) or \
               (sender == self.client.username and recipient == username):
                self.client.message_handler.display_message_in_current_view(msg)
    
    def _start_call(self, call_type):
        """Bắt đầu cuộc gọi"""
        if self.current_chat:
            from client.ui.call_ui import CallUI
            call_ui = CallUI(self.client, self.current_chat, call_type, is_caller=True)
            
            from common.protocol import Protocol, MessageType
            Protocol.send_message(
                self.client.socket,
                MessageType.CALL_REQUEST,
                {
                    "recipient": self.current_chat,
                    "call_type": call_type,
                    "caller": self.client.username
                }
            )