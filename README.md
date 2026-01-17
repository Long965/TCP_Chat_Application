chat_app/
│
├── common/                  # Module dùng chung
│   ├── __init__.py
│   ├── protocol.py         # Protocol và MessageType
│   └── config.py           # Cấu hình chung
│
├── client/                 # Module client
│   ├── __init__.py
│   ├── main.py             # Entry point
│   ├── client_core.py      # Logic core
│   ├── ui/                 # Giao diện
│   │   ├── __init__.py
│   │   ├── login_ui.py
│   │   ├── chat_ui.py
│   │   └── message_ui.py
│   └── handlers/           # Xử lý logic
│       ├── __init__.py
│       ├── file_handler.py
│       └── message_handler.py
│
├── server/                 # Module server
│   ├── __init__.py
│   ├── main.py             # Entry point
│   ├── server_core.py      # Logic core
│   └── handlers/           # Xử lý logic
│       ├── __init__.py
│       ├── client_handler.py
│       ├── file_handler.py
│       └── message_handler.py
│
├── requirements.txt        # Dependencies
└── README.md              # File này