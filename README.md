chat_app/
│
├── common/                  # Module dùng chung
│   ├── __init__.py
│   ├── protocol.py         # Protocol và MessageType (CẬP NHẬT)
│   └── config.py           # Cấu hình chung
│
├── client/                 # Module client
│   ├── __init__.py
│   ├── main.py             # Entry point
│   ├── client_core.py      # Logic core (CẬP NHẬT)
│   ├── ui/                 # Giao diện
│   │   ├── __init__.py
│   │   ├── login_ui.py
│   │   ├── chat_ui.py      # Chat nhóm (CẬP NHẬT)
│   │   ├── message_ui.py
│   │   └── call_ui.py          # NEW: Giao diện call
│   └── handlers/           # Xử lý logic
│       ├── __init__.py
│       ├── file_handler.py
│       ├── message_handler.py  # CẬP NHẬT
│       └── call_handler.py     # NEW
│
├── server/                 # Module server
│   ├── __init__.py
│   ├── main.py             # Entry point
│   ├── server_core.py      # Logic core
│   └── handlers/           # Xử lý logic
│       ├── __init__.py
│       ├── client_handler.py   # CẬP NHẬT
│       ├── file_handler.py
│       └── message_handler.py  # CẬP NHẬT
│
├── requirements.txt        # Dependencies
└── README.md              # File này