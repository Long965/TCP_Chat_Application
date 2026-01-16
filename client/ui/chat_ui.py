"""
Giao diện chat chính
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
        
        # User list header
        Label(
            sidebar,
            text="Danh sách người dùng",
            font=("Arial", 10, "bold"),
            bg=self.colors.BG_WHITE,
            fg=self.colors.TEXT_SECONDARY
        ).pack(pady=10, padx=15, anchor=W)
        
        # User listbox
        user_frame = Frame(sidebar, bg=self.colors.BG_WHITE)
        user_frame.pack(fill=BOTH, expand=True, padx=10)
        
        scrollbar = Scrollbar(user_frame)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        self.user_listbox = Listbox(
            user_frame,
            font=UISettings.FONT_MESSAGE,
            bg=self.colors.BG_WHITE,
            fg=self.colors.TEXT_PRIMARY,
            bd=0,
            highlightthickness=0,
            selectbackground=self.colors.BG_SECONDARY,
            yscrollcommand=scrollbar.set
        )
        self.user_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=self.user_listbox.yview)
    
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
        """Cập nhật danh sách user"""
        self.user_listbox.delete(0, END)
        
        for user in users:
            display = f"🟢 {user}" if user == self.client.username else f"👤 {user}"
            self.user_listbox.insert(END, display)