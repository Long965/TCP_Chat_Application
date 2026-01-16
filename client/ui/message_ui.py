"""
Components hiển thị các loại message
"""
from tkinter import Frame, Label, Button, LEFT, RIGHT, W, E, SOLID

class MessageUI:
    """Class chứa các hàm hiển thị message"""
    
    @staticmethod
    def display_text_message(container, data, username, colors):
        """Hiển thị tin nhắn text"""
        sender = data.get("sender")
        message = data.get("message")
        
        is_mine = (sender == username)
        
        # Message container
        msg_frame = Frame(container, bg=colors.BG_SECONDARY)
        msg_frame.pack(fill="x", pady=5)
        
        if is_mine:
            # Tin nhắn của mình - bên phải
            bubble = Frame(msg_frame, bg=colors.MESSAGE_SENT, padx=12, pady=8)
            bubble.pack(side=RIGHT, anchor=E, padx=10)
            
            Label(
                bubble,
                text=message,
                font=("Arial", 10),
                bg=colors.MESSAGE_SENT,
                fg="white",
                wraplength=400,
                justify=LEFT
            ).pack()
        else:
            # Tin nhắn người khác - bên trái
            container_frame = Frame(msg_frame, bg=colors.BG_SECONDARY)
            container_frame.pack(side=LEFT, anchor=W, padx=10)
            
            Label(
                container_frame,
                text=sender,
                font=("Arial", 8, "bold"),
                bg=colors.BG_SECONDARY,
                fg=colors.TEXT_SECONDARY
            ).pack(anchor=W)
            
            bubble = Frame(container_frame, bg=colors.MESSAGE_RECEIVED, 
                          padx=12, pady=8)
            bubble.pack(anchor=W, pady=(2, 0))
            
            Label(
                bubble,
                text=message,
                font=("Arial", 10),
                bg=colors.MESSAGE_RECEIVED,
                fg=colors.TEXT_PRIMARY,
                wraplength=400,
                justify=LEFT
            ).pack()
    
    @staticmethod
    def display_file_message(container, data, download_callback, colors):
        """Hiển thị thông báo file"""
        sender = data.get("sender")
        filename = data.get("filename")
        original_filename = data.get("original_filename", filename)
        filesize = data.get("filesize", 0)
        file_type = data.get("file_type", "file")
        
        # Message container
        msg_frame = Frame(container, bg=colors.BG_SECONDARY)
        msg_frame.pack(fill="x", pady=5)
        
        container_frame = Frame(msg_frame, bg=colors.BG_SECONDARY)
        container_frame.pack(side=LEFT, anchor=W, padx=10)
        
        if sender:
            Label(
                container_frame,
                text=sender,
                font=("Arial", 8, "bold"),
                bg=colors.BG_SECONDARY,
                fg=colors.TEXT_SECONDARY
            ).pack(anchor=W)
        
        # File bubble
        file_frame = Frame(container_frame, bg="white", bd=1, relief=SOLID)
        file_frame.pack(anchor=W, pady=(2, 0))
        
        content_frame = Frame(file_frame, bg="white", padx=15, pady=10)
        content_frame.pack()
        
        # Icon based on file type
        icon = "🖼️" if file_type == "image" else "🎬" if file_type == "video" else "📎"
        
        Label(
            content_frame,
            text=icon,
            font=("Arial", 24),
            bg="white"
        ).pack(side=LEFT, padx=(0, 10))
        
        info_frame = Frame(content_frame, bg="white")
        info_frame.pack(side=LEFT)
        
        Label(
            info_frame,
            text=original_filename,
            font=("Arial", 10, "bold"),
            bg="white"
        ).pack(anchor=W)
        
        Label(
            info_frame,
            text=f"{filesize / 1024:.1f} KB",
            font=("Arial", 8),
            bg="white",
            fg=colors.TEXT_SECONDARY
        ).pack(anchor=W)
        
        # Download button
        Button(
            content_frame,
            text="⬇️ Tải về",
            font=("Arial", 9),
            bg=colors.BG_PRIMARY,
            fg="white",
            bd=0,
            cursor="hand2",
            padx=15,
            pady=5,
            command=lambda: download_callback(filename)
        ).pack(side=RIGHT, padx=(10, 0))
    
    @staticmethod
    def display_system_message(container, message, colors):
        """Hiển thị thông báo hệ thống"""
        msg_frame = Frame(container, bg=colors.BG_SECONDARY)
        msg_frame.pack(fill="x", pady=5)
        
        Label(
            msg_frame,
            text=message,
            font=("Arial", 9, "italic"),
            bg=colors.BG_SECONDARY,
            fg=colors.TEXT_SECONDARY
        ).pack()