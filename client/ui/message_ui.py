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
        """Hiển thị tin nhắn văn bản"""
        bg = colors.MSG_SENT if is_sender else colors.MSG_RECV
        fg = "white" if is_sender else "black"
        anchor = E if is_sender else W
        
        wrapper = Frame(parent, bg=colors.BG_MAIN)
        wrapper.pack(fill="x", pady=2, padx=15)
        
        bubble = Frame(wrapper, bg=bg, padx=12, pady=8)
        bubble.pack(side=RIGHT if is_sender else LEFT, anchor=anchor)

        # Hiện tên người gửi (nếu là nhóm)
        if not is_sender and not msg.get("recipient"):
            Label(bubble, text=msg.get("sender"), font=("Segoe UI", 9, "bold"),
                  bg=bg, fg="#555").pack(anchor="w", pady=(0, 2))

        Label(bubble, text=msg.get("message") or msg.get("content", ""),
              font=("Segoe UI", 11), bg=bg, fg=fg,
              justify="left", wraplength=400).pack(anchor="w")

        Label(bubble, text=MessageUI._format_time(msg.get("timestamp")),
              font=("Segoe UI", 8), bg=bg, fg="#DDD" if is_sender else "#888").pack(anchor="e", pady=(2,0))

    @staticmethod
    def display_file_message(parent, msg, is_sender, colors, download_callback=None):
        """Hiển thị tin nhắn file (Bong bóng tĩnh)"""
        bg = colors.MSG_SENT if is_sender else colors.MSG_RECV
        fg = "white" if is_sender else "black"
        anchor = E if is_sender else W
        
        wrapper = Frame(parent, bg=colors.BG_MAIN)
        wrapper.pack(fill="x", pady=5, padx=15)
        
        bubble = Frame(wrapper, bg=bg, padx=10, pady=8)
        bubble.pack(side=RIGHT if is_sender else LEFT, anchor=anchor)
        
        if not is_sender and not msg.get("recipient"):
            Label(bubble, text=msg.get("sender"), font=("Segoe UI", 9, "bold"),
                  bg=bg, fg="#555").pack(anchor="w", pady=(0, 5))

        row = Frame(bubble, bg=bg)
        row.pack(fill="x")

        # Xác định icon
        file_type = msg.get("file_type", "file")
        icon_char = "🖼️" if file_type and "image" in file_type else "📄"

        Label(row, text=icon_char, font=("Segoe UI Emoji", 20), bg=bg, fg=fg).pack(side=LEFT, padx=5)
        
        info = Frame(row, bg=bg)
        info.pack(side=LEFT, padx=10)
        
        filename = msg.get("original_filename", msg.get("filename", "File"))
        # Cắt ngắn tên file nếu quá dài
        display_name = (filename[:20] + '...') if len(filename) > 23 else filename
        
        Label(info, text=display_name, font=("Segoe UI", 10, "bold"), bg=bg, fg=fg).pack(anchor="w")
        
        # Format filesize
        size_kb = msg.get('filesize', 0) / 1024
        size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB"
        
        Label(info, text=size_str, font=("Segoe UI", 9), 
              bg=bg, fg="#DDD" if is_sender else "#666").pack(anchor="w")

        # Nút Download (Chỉ hiện khi là người nhận)
        if not is_sender:
            def on_click():
                if download_callback: download_callback(msg)
                
            Button(row, text="⬇", font=("Arial", 12, "bold"), bg=bg, fg=colors.ACCENT, bd=0,
                   activebackground=bg, cursor="hand2", command=on_click).pack(side=LEFT, padx=5)
                
        Label(bubble, text=MessageUI._format_time(msg.get("timestamp")),
              font=("Segoe UI", 8), bg=bg, fg="#DDD" if is_sender else "#888").pack(anchor="e", pady=(5,0))

    @staticmethod
    def display_upload_progress(parent, filename, filesize, callbacks, is_download=False):
        """
        Hiển thị thanh tiến trình Upload/Download động.
        Hỗ trợ: Pause, Resume, Cancel.
        """
        # Màu sắc phân biệt Upload (Xanh dương) vs Download (Xanh lá)
        theme_color = Colors.MSG_SENT if not is_download else "#E8F5E9" # Xanh lá nhạt
        text_color = "white" if not is_download else "black"
        status_prefix = "📤 Đang gửi" if not is_download else "📥 Đang tải"
        
        wrapper = Frame(parent, bg=Colors.BG_MAIN)
        wrapper.pack(fill="x", pady=5, padx=15)
        
        # Căn lề: Upload bên Phải, Download bên Trái (hoặc giữ nguyên bên phải để dễ nhìn)
        side = RIGHT if not is_download else RIGHT 
        
        bubble = Frame(wrapper, bg=theme_color, padx=10, pady=8, bd=1, relief="solid" if is_download else "flat")
        bubble.pack(side=side, anchor=E)
        
        # Dòng tiêu đề
        lbl_title = Label(bubble, text=f"{status_prefix}: {filename}", font=("Segoe UI", 9, "bold"), 
              bg=theme_color, fg=text_color)
        lbl_title.pack(anchor="w")

        # Progress Bar Style
        style = ttk.Style()
        style.theme_use('clam')
        # Tạo style riêng cho bar này
        bar_style = "upload.Horizontal.TProgressbar"
        style.configure(bar_style, background=Colors.SUCCESS, troughcolor="#E0E0E0", borderwidth=0)

        progress = ttk.Progressbar(bubble, style=bar_style, orient="horizontal", length=220, mode="determinate")
        progress.pack(fill="x", pady=5)

        # Stats & Controls
        ctrl_frame = Frame(bubble, bg=theme_color)
        ctrl_frame.pack(fill="x")

        size_lbl = Label(ctrl_frame, text="0%", font=("Segoe UI", 8), bg=theme_color, fg=text_color)
        size_lbl.pack(side=LEFT)
        
        # --- Logic điều khiển ---
        state = {"paused": False}
        
        def toggle_pause():
            state["paused"] = not state["paused"]
            if state["paused"]:
                btn_pause.config(text="▶", fg="orange")
                lbl_title.config(text=f"⏸ Đã tạm dừng: {filename}")
                callbacks['pause']()
            else:
                btn_pause.config(text="⏸", fg=text_color)
                lbl_title.config(text=f"{status_prefix}: {filename}")
                callbacks['resume']()

        def cancel_action():
            callbacks['cancel']()
            wrapper.destroy()

        # Nút Cancel (Stop)
        Button(ctrl_frame, text="⏹", font=("Segoe UI", 9), bg=theme_color, fg="red" if is_download else "#FFCCCC", bd=0, 
               activebackground=theme_color, cursor="hand2", command=cancel_action).pack(side=RIGHT, padx=2)

        # Nút Pause/Resume
        btn_pause = Button(ctrl_frame, text="⏸", font=("Segoe UI", 9), bg=theme_color, fg=text_color, bd=0, 
                           activebackground=theme_color, cursor="hand2", command=toggle_pause)
        btn_pause.pack(side=RIGHT, padx=2)

        # Hàm update UI (trả về cho FileHandler gọi)
        def update_progress(current_bytes):
            try:
                # Kiểm tra widget còn tồn tại không
                if not wrapper.winfo_exists(): return
                
                percent = (current_bytes / filesize) * 100
                progress['value'] = percent
                size_lbl.config(text=f"{int(percent)}%")

                # Khi hoàn tất
                if current_bytes >= filesize:
                    lbl_title.config(text=f"✅ Hoàn tất: {filename}")
                    btn_pause.destroy() # Ẩn nút pause
                    # Tự động đóng thanh progress sau 2s
                    wrapper.after(2000, lambda: wrapper.destroy() if wrapper.winfo_exists() else None)
            except Exception:
                pass
        
        return update_progress