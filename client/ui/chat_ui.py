"""
client/ui/chat_ui.py
"""
import tkinter as tk
from tkinter import ttk, messagebox, SOLID
from common.config import Colors, UISettings
from client.ui.message_ui import MessageUI
from datetime import datetime

class ChatUI(tk.Frame):
    def __init__(self, client):
        super().__init__(client.root)
        self.client = client
        self.current_chat = None
        self.configure(bg=Colors.BG_MAIN)

        # --- SIDEBAR (TRÁI) - Cố định width ---
        self.sidebar = tk.Frame(self, width=280, bg=Colors.BG_SIDEBAR)
        self.sidebar.pack(side=tk.LEFT, fill="y")
        self.sidebar.pack_propagate(False)
        
        # Đường kẻ dọc ngăn cách sidebar
        tk.Frame(self.sidebar, width=1, bg=Colors.BORDER).pack(side=tk.RIGHT, fill="y")

        # 1. HEADER "Chats"
        self.sidebar_header = tk.Frame(self.sidebar, bg=Colors.BG_SIDEBAR_HEADER, height=60)
        self.sidebar_header.pack(fill="x")
        self.sidebar_header.pack_propagate(False)
        
        lbl_chats = tk.Label(self.sidebar_header, text="Chats", 
                             font=UISettings.FONT_HEADER,
                             bg=Colors.BG_SIDEBAR_HEADER, fg=Colors.TEXT_WHITE)
        lbl_chats.place(relx=0.5, rely=0.5, anchor="center")

        # 2. Danh sách User
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                        background=Colors.BG_SIDEBAR, 
                        foreground=Colors.TEXT_PRIMARY,
                        fieldbackground=Colors.BG_SIDEBAR, 
                        rowheight=50, 
                        font=("Segoe UI", 11), 
                        borderwidth=0)
        style.map("Treeview", 
                  background=[('selected', Colors.BG_HOVER)], 
                  foreground=[('selected', Colors.ACCENT)])
        
        self.user_list = ttk.Treeview(self.sidebar, show="tree", selectmode="browse")
        self.user_list.pack(fill="both", expand=True)
        self.user_list.bind("<<TreeviewSelect>>", self.on_user_select)

        # --- MAIN CHAT (PHẢI) ---
        self.main_area = tk.Frame(self, bg=Colors.BG_MAIN)
        self.main_area.pack(side=tk.RIGHT, fill="both", expand=True)

        # 3. HEADER Tên người chat
        self.header = tk.Frame(self.main_area, bg=Colors.BG_MAIN, height=60)
        self.header.pack(fill="x", side=tk.TOP)
        
        # Đường kẻ dưới header
        tk.Frame(self.header, height=1, bg=Colors.BORDER).pack(side=tk.BOTTOM, fill="x")

        # Container Header
        header_content = tk.Frame(self.header, bg=Colors.BG_MAIN)
        header_content.pack(fill="both", expand=True)

        # Tên người chat - Căn giữa, Font to
        self.chat_title = tk.Label(header_content, text="Trò chuyện nhóm",
                                   bg=Colors.BG_MAIN, fg=Colors.TEXT_PRIMARY,
                                   font=UISettings.FONT_CHAT_NAME)
        self.chat_title.place(relx=0.5, rely=0.5, anchor="center")

        # Nút Video Call (Góc phải)
        self.btn_call = tk.Button(header_content, text="📹", bg=Colors.BG_MAIN, fg=Colors.ACCENT,
                                  font=("Arial", 16), bd=0, cursor="hand2", 
                                  activebackground=Colors.BG_HOVER,
                                  command=self.start_video_call)
        self.btn_call.pack(side=tk.RIGHT, padx=20)

        # 5. INPUT AREA - [FIXED LAYOUT: SỬ DỤNG GRID ĐỂ CÂN ĐỐI]
        # Chúng ta đưa phần này lên TRƯỚC phần Chat Area trong code (nhưng pack bottom)
        # để đảm bảo nó luôn nằm dưới cùng và không bị Chat Area che mất.
        self.input_frame = tk.Frame(self.main_area, bg=Colors.BG_MAIN, height=80)
        self.input_frame.pack(side=tk.BOTTOM, fill="x")
        
        # Đường kẻ ngăn cách trên ô nhập liệu
        tk.Frame(self.input_frame, height=1, bg=Colors.BORDER).pack(side=tk.TOP, fill="x")
        
        # Container bên trong
        inner_input = tk.Frame(self.input_frame, bg=Colors.BG_MAIN)
        inner_input.pack(fill="both", expand=True, padx=20, pady=15)

        # Cấu hình Grid: 3 Cột (0: Attach, 1: Entry, 2: Send)
        inner_input.columnconfigure(0, weight=0) # Cột nút Attach: Co theo nội dung
        inner_input.columnconfigure(1, weight=1) # Cột Entry: Giãn hết cỡ (QUAN TRỌNG)
        inner_input.columnconfigure(2, weight=0) # Cột nút Send: Co theo nội dung

        # [CỘT 0] Nút Đính kèm
        tk.Button(inner_input, text="📎", font=("Arial", 18), bg=Colors.BG_MAIN, fg="#888",
                  bd=0, cursor="hand2", command=self.send_file)\
                  .grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        # [CỘT 1] Ô nhập liệu (Sticky="ew" để giãn ngang)
        self.msg_entry = tk.Entry(inner_input, bg="white", fg="black",
                                  insertbackground="black", font=("Segoe UI", 12), 
                                  bd=1, relief=SOLID)
        self.msg_entry.grid(row=0, column=1, sticky="ew", ipady=8)
        self.msg_entry.bind("<Return>", self.send_message)
        self.msg_entry.focus()

        # [CỘT 2] Nút Send
        tk.Button(inner_input, text="Gửi ➤", font=("Segoe UI", 11, "bold"), 
                  bg=Colors.ACCENT, fg="white",
                  bd=0, padx=20, pady=5, cursor="hand2",
                  command=self.send_message)\
                  .grid(row=0, column=2, padx=(10, 0), sticky="e")

        # 4. Khu vực tin nhắn (Pack sau cùng để chiếm phần giữa)
        self.canvas = tk.Canvas(self.main_area, bg=Colors.BG_MAIN, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.main_area, orient="vertical", command=self.canvas.yview)
        self.messages_container = tk.Frame(self.canvas, bg=Colors.BG_MAIN)

        self.messages_container.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.messages_container, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side=tk.RIGHT, fill="y")
        self.canvas.pack(side=tk.LEFT, fill="both", expand=True)
        self.canvas.bind('<Configure>', self._on_canvas_resize)

    def _on_canvas_resize(self, event):
        items = self.canvas.find_withtag("all")
        if items:
            self.canvas.itemconfig(items[0], width=event.width)

    def update_user_list(self, users):
        current_selection = self.user_list.selection()
        for item in self.user_list.get_children(): self.user_list.delete(item)
        
        self.user_list.insert("", "end", iid="group", text=" Trò chuyện nhóm")
        for user in users:
            if user != self.client.username:
                self.user_list.insert("", "end", iid=user, text=f" {user}")
                
        if current_selection and self.user_list.exists(current_selection[0]):
            self.user_list.selection_set(current_selection[0])
        elif not self.current_chat:
            self.user_list.selection_set("group")
            self.current_chat = None

    def on_user_select(self, event):
        selected = self.user_list.selection()
        if not selected: return
        user_id = selected[0]
        
        if user_id == "group":
            self.current_chat = None
            self.chat_title.config(text="Trò chuyện nhóm")
        else:
            self.current_chat = user_id
            self.chat_title.config(text=f"{user_id}")
            
        self.reload_messages()

    def reload_messages(self):
        for widget in self.messages_container.winfo_children(): widget.destroy()
        for msg in self.client.messages: self.display_new_message(msg)

    def display_new_message(self, msg):
        sender = msg.get("sender")
        recipient = msg.get("recipient")

        should_show = False
        if self.current_chat is None: 
            if not recipient: should_show = True
        else: 
            if (sender == self.current_chat and recipient == self.client.username) or \
               (sender == self.client.username and recipient == self.current_chat):
                should_show = True

        if should_show:
            is_sender = (sender == self.client.username)
            if msg.get("type") == "FILE_INFO":
                download_cb = self.client.file_handler.request_download
                MessageUI.display_file_message(self.messages_container, msg, is_sender, Colors, download_cb)
            else:
                MessageUI.display_text_message(self.messages_container, msg, is_sender, Colors)
            
            self.messages_container.update_idletasks()
            self.canvas.yview_moveto(1)

    def send_message(self, event=None):
        text = self.msg_entry.get().strip()
        if not text: return
        
        # 1. Tạo msg giả lập
        msg = {
            "type": "TEXT",
            "sender": self.client.username,
            "recipient": self.current_chat,
            "message": text,
            "timestamp": datetime.now().isoformat()
        }
        # 2. Lưu & Hiện
        self.client.messages.append(msg)
        self.display_new_message(msg)

        # 3. Gửi Server
        try:
            self.client.send_text_message(text, self.current_chat)
            self.msg_entry.delete(0, 'end')
        except Exception as e:
            messagebox.showerror("Lỗi", f"Gửi thất bại: {e}")

    def send_file(self):
        self.client.file_handler.send_file()

    def start_video_call(self):
        if not self.current_chat: 
            return messagebox.showwarning("Lỗi", "Chỉ gọi Video Chat Riêng!")
        self.client.call_handler.start_call(self.current_chat)