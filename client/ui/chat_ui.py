"""
client/ui/chat_ui.py
"""
import tkinter as tk
from tkinter import ttk, messagebox
from common.config import Colors
from client.ui.message_ui import MessageUI

class ChatUI(tk.Frame):
    def __init__(self, client):
        super().__init__(client.root)
        self.client = client
        self.current_chat = None 
        self.configure(bg=Colors.BG_MAIN)
        
        # --- SIDEBAR ---
        self.sidebar = tk.Frame(self, width=280, bg=Colors.BG_SIDEBAR)
        self.sidebar.pack(side=tk.LEFT, fill="y")
        self.sidebar.pack_propagate(False)

        # Search Bar
        self.sidebar_header = tk.Frame(self.sidebar, bg=Colors.BG_SIDEBAR, height=60)
        self.sidebar_header.pack(fill="x", padx=10, pady=10)
        self.search_entry = tk.Entry(self.sidebar_header, bg="#242f3d", fg="white", 
                                     relief="flat", font=("Segoe UI", 10), insertbackground="white")
        self.search_entry.pack(fill="x", ipady=6)
        self.search_entry.insert(0, " 🔍 Tìm kiếm...")

        # Treeview User List
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=Colors.BG_SIDEBAR, foreground="white", 
                        fieldbackground=Colors.BG_SIDEBAR, rowheight=45, font=("Segoe UI", 11), borderwidth=0)
        style.map("Treeview", background=[('selected', Colors.MSG_SENT)])

        self.user_list = ttk.Treeview(self.sidebar, show="tree", selectmode="browse")
        self.user_list.pack(fill="both", expand=True)
        self.user_list.bind("<<TreeviewSelect>>", self.on_user_select)

        # --- MAIN CHAT ---
        self.main_area = tk.Frame(self, bg=Colors.BG_MAIN)
        self.main_area.pack(side=tk.RIGHT, fill="both", expand=True)

        # Header
        self.header = tk.Frame(self.main_area, bg=Colors.BG_SIDEBAR, height=60)
        self.header.pack(fill="x")
        self.chat_title = tk.Label(self.header, text="📢 Trò chuyện nhóm", 
                                   bg=Colors.BG_SIDEBAR, fg="white", 
                                   font=("Segoe UI", 14, "bold"), anchor="w")
        self.chat_title.pack(side=tk.LEFT, padx=20, pady=15)
        
        # Video Call Btn
        self.btn_call = tk.Button(self.header, text="📹", bg=Colors.BG_SIDEBAR, fg=Colors.ACCENT,
                                  font=("Arial", 16), bd=0, activebackground=Colors.BG_SIDEBAR,
                                  cursor="hand2", command=self.start_video_call)
        self.btn_call.pack(side=tk.RIGHT, padx=15)

        # Messages Area
        self.canvas = tk.Canvas(self.main_area, bg=Colors.BG_MAIN, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.main_area, orient="vertical", command=self.canvas.yview)
        self.messages_container = tk.Frame(self.canvas, bg=Colors.BG_MAIN)
        
        self.messages_container.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.messages_container, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side=tk.RIGHT, fill="y")
        self.canvas.pack(side=tk.LEFT, fill="both", expand=True)
        self.canvas.bind('<Configure>', self._on_canvas_resize)

        # Input Area
        self.input_frame = tk.Frame(self.main_area, bg=Colors.BG_SIDEBAR, height=70)
        self.input_frame.pack(fill="x", side=tk.BOTTOM)

        tk.Button(self.input_frame, text="📎", font=("Arial", 18), bg=Colors.BG_SIDEBAR, fg="#7f91a4", 
                  bd=0, activebackground=Colors.BG_SIDEBAR, cursor="hand2",
                  command=self.send_file).pack(side=tk.LEFT, padx=15)

        self.msg_entry = tk.Entry(self.input_frame, bg=Colors.BG_MAIN, fg="white", 
                                  insertbackground="white", font=("Segoe UI", 12), relief="flat")
        self.msg_entry.pack(side=tk.LEFT, fill="both", expand=True, padx=10, pady=15)
        self.msg_entry.bind("<Return>", self.send_message)

        tk.Button(self.input_frame, text="➤", font=("Arial", 16), bg=Colors.BG_SIDEBAR, fg=Colors.ACCENT, 
                  bd=0, activebackground=Colors.BG_SIDEBAR, cursor="hand2",
                  command=self.send_message).pack(side=tk.RIGHT, padx=15)

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self.canvas.find_withtag("all")[0], width=event.width)

    def update_user_list(self, users):
        for item in self.user_list.get_children(): self.user_list.delete(item)
        self.user_list.insert("", "end", iid="group", text=" 📢  Trò chuyện nhóm")
        for user in users:
            if user != self.client.username:
                self.user_list.insert("", "end", iid=user, text=f" 👤  {user}")

    def on_user_select(self, event):
        selected = self.user_list.selection()
        if not selected: return
        user_id = selected[0]
        self.current_chat = None if user_id == "group" else user_id
        self.chat_title.config(text="📢 Trò chuyện nhóm" if not self.current_chat else f"👤 Chat với {user_id}")
        self.reload_messages()

    def reload_messages(self):
        for widget in self.messages_container.winfo_children(): widget.destroy()
        for msg in self.client.messages: self.display_new_message(msg)
            
    def display_new_message(self, msg):
        sender = msg.get("sender")
        recipient = msg.get("recipient")
        
        # Logic hiển thị Chat Nhóm vs Chat Riêng
        should_show = False
        if self.current_chat is None: 
             if recipient is None or recipient == "": should_show = True
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
        self.client.send_text_message(text, self.current_chat)
        self.msg_entry.delete(0, 'end')

    def send_file(self):
        self.client.file_handler.send_file()

    def start_video_call(self):
        if not self.current_chat: return messagebox.showwarning("Lỗi", "Chỉ gọi Video Chat Riêng!")
        self.client.call_handler.start_call(self.current_chat)