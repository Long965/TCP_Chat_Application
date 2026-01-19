"""
client/ui/message_ui.py
"""
from tkinter import Frame, Label, Button, LEFT, RIGHT, W, E
from datetime import datetime

class MessageUI:
    @staticmethod
    def _format_time(timestamp_str):
        if not timestamp_str: return datetime.now().strftime("%H:%M")
        try:
            return datetime.fromisoformat(timestamp_str).strftime("%H:%M")
        except: return ""

    @staticmethod
    def display_text_message(parent, msg, is_sender, colors):
        bg = colors.MSG_SENT if is_sender else colors.MSG_RECV
        fg = colors.TEXT_PRIMARY
        anchor = E if is_sender else W
        
        wrapper = Frame(parent, bg=colors.BG_MAIN)
        wrapper.pack(fill="x", pady=2, padx=15)
        
        bubble = Frame(wrapper, bg=bg, padx=12, pady=8)
        bubble.pack(side=RIGHT if is_sender else LEFT, anchor=anchor)

        if not is_sender and not msg.get("recipient"): 
             Label(bubble, text=msg.get("sender"), font=("Segoe UI", 9, "bold"), 
                   bg=bg, fg=colors.ACCENT).pack(anchor="w", pady=(0, 2))

        Label(bubble, text=msg.get("message") or msg.get("content", ""), 
              font=("Segoe UI", 11), bg=bg, fg=fg, 
              justify="left", wraplength=400).pack(anchor="w")

        Label(bubble, text=MessageUI._format_time(msg.get("timestamp")), 
              font=("Segoe UI", 8), bg=bg, fg=colors.TEXT_SECONDARY).pack(anchor="e", pady=(2,0))

    @staticmethod
    def display_file_message(parent, msg, is_sender, colors, download_callback=None):
        bg = colors.MSG_SENT if is_sender else colors.MSG_RECV
        anchor = E if is_sender else W
        
        wrapper = Frame(parent, bg=colors.BG_MAIN)
        wrapper.pack(fill="x", pady=5, padx=15)
        
        bubble = Frame(wrapper, bg=bg, padx=10, pady=8)
        bubble.pack(side=RIGHT if is_sender else LEFT, anchor=anchor)

        if not is_sender and not msg.get("recipient"):
             Label(bubble, text=msg.get("sender"), font=("Segoe UI", 9, "bold"), 
                   bg=bg, fg=colors.ACCENT).pack(anchor="w", pady=(0, 5))

        # --- LAYOUT FILE ---
        row = Frame(bubble, bg=bg)
        row.pack(fill="x")

        # [FIX] Chọn icon dựa trên loại file
        file_type = msg.get("file_type", "file")
        if file_type and "image" in file_type:
            icon_char = "🖼️" # Ảnh
        else:
            icon_char = "📄" # File thường

        Label(row, text=icon_char, font=("Segoe UI Emoji", 20), bg=bg, fg="white").pack(side=LEFT, padx=5)
        
        # Info
        info = Frame(row, bg=bg)
        info.pack(side=LEFT, padx=10)
        
        filename = msg.get("original_filename", "File")
        if len(filename) > 25: filename = filename[:22] + "..."
            
        Label(info, text=filename, font=("Segoe UI", 10, "bold"), bg=bg, fg="white").pack(anchor="w")
        Label(info, text=f"{msg.get('filesize', 0)/1024:.1f} KB", font=("Segoe UI", 9), bg=bg, fg=colors.TEXT_SECONDARY).pack(anchor="w")

        # Nút Tải
        def on_click():
            if download_callback: download_callback(msg)
            
        Button(row, text="⬇", font=("Arial", 12, "bold"), bg=bg, fg=colors.ACCENT, bd=0, 
               activebackground=bg, cursor="hand2", command=on_click).pack(side=LEFT, padx=5)
        
        Label(bubble, text=MessageUI._format_time(msg.get("timestamp")), 
              font=("Segoe UI", 8), bg=bg, fg=colors.TEXT_SECONDARY).pack(anchor="e", pady=(5,0))