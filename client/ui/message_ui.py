import tkinter as tk
from tkinter import Frame, Label, Button, LEFT, RIGHT, W, E, ttk
from datetime import datetime
from common.config import Colors

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

        row = Frame(bubble, bg=bg)
        row.pack(fill="x")
        
        file_type = msg.get("file_type", "file")
        icon_char = "🖼️" if file_type and "image" in file_type else "📄"
        
        Label(row, text=icon_char, font=("Segoe UI Emoji", 20), bg=bg, fg="white").pack(side=LEFT, padx=5)

        info = Frame(row, bg=bg)
        info.pack(side=LEFT, padx=10)

        filename = msg.get("original_filename", "File")
        if len(filename) > 25: filename = filename[:22] + "..."

        Label(info, text=filename, font=("Segoe UI", 10, "bold"), bg=bg, fg="white").pack(anchor="w")
        Label(info, text=f"{msg.get('filesize', 0)/1024:.1f} KB", font=("Segoe UI", 9), bg=bg, fg=colors.TEXT_SECONDARY).pack(anchor="w")

        def on_click():
            if download_callback: download_callback(msg)

        Button(row, text="⬇", font=("Arial", 12, "bold"), bg=bg, fg=colors.ACCENT, bd=0,
               activebackground=bg, cursor="hand2", command=on_click).pack(side=LEFT, padx=5)

        Label(bubble, text=MessageUI._format_time(msg.get("timestamp")),
              font=("Segoe UI", 8), bg=bg, fg=colors.TEXT_SECONDARY).pack(anchor="e", pady=(5,0))

    @staticmethod
    def display_upload_progress(parent, filename, filesize, control_callbacks):
        """
        Hiển thị UI đang upload (Progress Bar + Pause/Resume + Cancel)
        """
        wrapper = Frame(parent, bg=Colors.BG_MAIN)
        wrapper.pack(fill="x", pady=5, padx=15)

        # Bubble
        bubble = Frame(wrapper, bg=Colors.MSG_SENT, padx=10, pady=8)
        bubble.pack(side=RIGHT, anchor=E)

        # Info
        Label(bubble, text=f"📤 Đang gửi: {filename}", font=("Segoe UI", 10, "bold"), bg=Colors.MSG_SENT, fg="white").pack(anchor="w")
        
        # Progress Bar
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("green.Horizontal.TProgressbar", background=Colors.SUCCESS, troughcolor=Colors.BG_HOVER, borderwidth=0)
        
        progress = ttk.Progressbar(bubble, style="green.Horizontal.TProgressbar", orient="horizontal", length=200, mode="determinate")
        progress.pack(fill="x", pady=5)
        
        # Stats & Controls
        ctrl_frame = Frame(bubble, bg=Colors.MSG_SENT)
        ctrl_frame.pack(fill="x")
        
        size_lbl = Label(ctrl_frame, text="0%", font=("Segoe UI", 9), bg=Colors.MSG_SENT, fg="#b0c4de")
        size_lbl.pack(side=LEFT)

        # Logic nút bấm
        state = {"paused": False}

        def toggle_pause():
            state["paused"] = not state["paused"]
            if state["paused"]:
                btn_pause.config(text="▶", bg=Colors.WARNING)
                control_callbacks['pause']()
            else:
                btn_pause.config(text="⏸", bg=Colors.BG_HOVER)
                control_callbacks['resume']()

        def cancel_upload():
            control_callbacks['cancel']()
            wrapper.destroy()

        btn_cancel = Button(ctrl_frame, text="❌", font=("Segoe UI", 9), bg=Colors.BG_HOVER, fg="white", bd=0, command=cancel_upload)
        btn_cancel.pack(side=RIGHT, padx=2)
        
        btn_pause = Button(ctrl_frame, text="⏸", font=("Segoe UI", 9), bg=Colors.BG_HOVER, fg="white", bd=0, command=toggle_pause)
        btn_pause.pack(side=RIGHT, padx=2)

        def update_progress(sent):
            # [FIX QUAN TRỌNG] Bắt lỗi nếu Widget đã bị hủy
            try:
                if not wrapper.winfo_exists(): 
                    return

                percent = (sent / filesize) * 100
                progress['value'] = percent
                size_lbl.config(text=f"{int(percent)}%")
                
                if sent >= filesize:
                    # Delay việc xóa một chút để người dùng kịp nhìn thấy 100%
                    wrapper.after(500, lambda: wrapper.destroy() if wrapper.winfo_exists() else None)
            except Exception:
                # Nếu có lỗi (do widget bị hủy giữa chừng), chỉ cần bỏ qua
                pass

        return update_progress