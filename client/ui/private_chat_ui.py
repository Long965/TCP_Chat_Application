"""
Giao diện chat riêng 1-1
"""

from tkinter import Frame, Label, Button, Text, Canvas, Scrollbar, Toplevel
from tkinter import LEFT, RIGHT, BOTTOM, TOP, X, Y, BOTH, W, END, WORD
from common.config import UISettings
from datetime import datetime

class PrivateChatUI:
    def __init__(self, client, recipient_username):
        self.client = client
        self.recipient = recipient_username
        self.colors = client.colors
        
        # Tạo cửa sổ mới
        self.window = Toplevel(client.root)
        self.window.title(f"Chat với {recipient_username}")
        self.window.geometry("800x600")
        self.window.minsize(600, 400)
        
        # Main container
        self.main_container = Frame(self.window, bg=self.colors.BG_WHITE)
        self.main_container.pack(fill=BOTH, expand=True)
        
        self._create_header()
        self._create_messages_area()
        self._create_input_area()
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _create_header(self):
        """Tạo header với thông tin người chat và nút call"""
        header = Frame(self.main_container, bg=self.colors.BG_WHITE, 
                      height=UISettings.CHAT_HEADER_HEIGHT)
        header.pack(fill=X)
        header.pack_propagate(False)
        
        # User info
        user_frame = Frame(header, bg=self.colors.BG_WHITE)
        user_frame.pack(side=LEFT, padx=20, pady=10)
        
        Label(
            user_frame,
            text=f"👤 {self.recipient}",
            font=("Arial", 14, "bold"),
            bg=self.colors.BG_WHITE
        ).pack(side=LEFT)
        
        Label(
            user_frame,
            text="🟢 Online",
            font=("Arial", 9),
            bg=self.colors.BG_WHITE,
            fg="green"
        ).pack(side=LEFT, padx=10)
        
        # Call buttons
        call_frame = Frame(header, bg=self.colors.BG_WHITE)
        call_frame.pack(side=RIGHT, padx=20)
        
        # Video call button
        Button(
            call_frame,
            text="📹",
            font=("Arial", 18),
            bg=self.colors.BG_WHITE,
            fg=self.colors.BG_PRIMARY,
            bd=0,
            cursor="hand2",
            command=lambda: self._start_call("video")
        ).pack(side=LEFT, padx=5)
        
        # Audio call button
        Button(
            call_frame,
            text="📞",
            font=("Arial", 18),
            bg=self.colors.BG_WHITE,
            fg=self.colors.BG_PRIMARY,
            bd=0,
            cursor="hand2",
            command=lambda: self._start_call("audio")
        ).pack(side=LEFT, padx=5)
        
        # Separator
        Frame(header, height=1, bg="#E4E6EB").pack(side=BOTTOM, fill=X)
    
    def _create_messages_area(self):
        """Tạo khu vực hiển thị messages"""
        messages_frame = Frame(self.main_container, bg=self.colors.BG_SECONDARY)
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
    
    def _create_input_area(self):
        """Tạo khu vực nhập tin nhắn"""
        input_container = Frame(self.main_container, bg=self.colors.BG_WHITE,
                               height=UISettings.INPUT_AREA_HEIGHT)
        input_container.pack(fill=X, side=BOTTOM)
        input_container.pack_propagate(False)
        
        Frame(input_container, height=1, bg="#E4E6EB").pack(fill=X)
        
        input_frame = Frame(input_container, bg=self.colors.BG_WHITE)
        input_frame.pack(fill=BOTH, expand=True, padx=15, pady=10)
        
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
    
    def _handle_send_text(self):
        """Xử lý gửi tin nhắn riêng"""
        message = self.message_entry.get("1.0", END).strip()
        
        if not message:
            return
        
        # Gửi tin nhắn riêng
        from common.protocol import Protocol, MessageType
        
        try:
            Protocol.send_message(
                self.client.socket,
                MessageType.TEXT,
                {
                    "message": message,
                    "recipient": self.recipient
                }
            )
            
            # Hiển thị tin nhắn của mình
            self.display_message({
                "sender": self.client.username,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Clear input
            self.message_entry.delete("1.0", END)
            
        except Exception as e:
            print(f"Error sending private message: {e}")
    
    def display_message(self, data):
        """Hiển thị tin nhắn trong chat riêng"""
        sender = data.get("sender")
        message = data.get("message")
        
        is_mine = (sender == self.client.username)
        
        # Message container
        msg_frame = Frame(self.messages_container, bg=self.colors.BG_SECONDARY)
        msg_frame.pack(fill="x", pady=5)
        
        if is_mine:
            # Tin nhắn của mình - bên phải
            bubble = Frame(msg_frame, bg=self.colors.MESSAGE_SENT, padx=12, pady=8)
            bubble.pack(side=RIGHT, anchor="e", padx=10)
            
            Label(
                bubble,
                text=message,
                font=("Arial", 10),
                bg=self.colors.MESSAGE_SENT,
                fg="white",
                wraplength=400,
                justify=LEFT
            ).pack()
        else:
            # Tin nhắn người khác - bên trái
            container_frame = Frame(msg_frame, bg=self.colors.BG_SECONDARY)
            container_frame.pack(side=LEFT, anchor=W, padx=10)
            
            bubble = Frame(container_frame, bg=self.colors.MESSAGE_RECEIVED,
                          padx=12, pady=8)
            bubble.pack(anchor=W, pady=(2, 0))
            
            Label(
                bubble,
                text=message,
                font=("Arial", 10),
                bg=self.colors.MESSAGE_RECEIVED,
                fg=self.colors.TEXT_PRIMARY,
                wraplength=400,
                justify=LEFT
            ).pack()
    
    def _start_call(self, call_type):
        """Bắt đầu cuộc gọi video/audio"""
        from client.ui.call_ui import CallUI
        
        # Tạo cửa sổ call
        call_ui = CallUI(self.client, self.recipient, call_type, is_caller=True)
        
        # Gửi yêu cầu call
        from common.protocol import Protocol, MessageType
        
        Protocol.send_message(
            self.client.socket,
            MessageType.CALL_REQUEST,
            {
                "recipient": self.recipient,
                "call_type": call_type,
                "caller": self.client.username
            }
        )
    
    def on_closing(self):
        """Đóng cửa sổ chat riêng"""
        # Xóa khỏi danh sách private chats
        if self.recipient in self.client.private_chats:
            del self.client.private_chats[self.recipient]
        
        self.window.destroy()