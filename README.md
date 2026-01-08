TCP_Chat_Appication/
│
├── server/
│   ├── server.py              # Chạy server chính
│   ├── client_handler.py      # Xử lý từng client (thread)
│   ├── protocol.py            # Quy ước định dạng message
│   ├── file_handler.py        # Nhận & gửi file
│   ├── user_manager.py        # Quản lý danh sách user
│   └── config.py              # IP, PORT, BUFFER_SIZE
│
├── client/
│   ├── client.py              # Chạy client
│   ├── receive_thread.py      # Luồng nhận dữ liệu
│   ├── send_handler.py        # Gửi tin nhắn / file
│   ├── file_handler.py        # Gửi & lưu file
│   ├── ui_console.py          # Giao diện console
│   └── config.py              # IP, PORT
│
├── shared/
│   └── protocol.py            # Dùng chung cho client & server
│
├── files/
│   ├── server_storage/        # File client gửi lên server
│   └── client_downloads/      # File client nhận về
│
└── README.md
