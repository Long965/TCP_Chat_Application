/**
 * static/script.js - Logic Web Client (Full + Upload Speed Limit)
 */
let ws;
let username = "";
let currentChat = null; // null = Chat nhóm
let messages = [];      // Lưu trữ lịch sử tin nhắn

// --- CẤU HÌNH UPLOAD ---
const UPLOAD_SPEED_LIMIT = 512 * 1024; // 512 KB/s (Giới hạn tốc độ)
const CHUNK_SIZE = 8192; // 8KB mỗi gói
let isUploading = false;
let uploadCancelled = false;

// --- 1. KẾT NỐI & LOGIN ---
function joinChat() {
    const input = document.getElementById("username-input");
    if (!input) return;

    username = input.value.trim();
    if (!username) return alert("Vui lòng nhập tên!");

    const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
    const host = window.location.host;

    ws = new WebSocket(`${protocol}${host}/ws/${username}`);

    ws.onopen = () => {
        console.log("✅ Đã kết nối Server");
        document.getElementById("login-screen").classList.add("hidden");
        document.getElementById("app").classList.remove("hidden");
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleServerMessage(data);
        } catch (e) {
            console.error("Lỗi parse JSON:", e);
        }
    };

    ws.onclose = () => {
        alert("Mất kết nối server!");
        location.reload();
    };
}

// --- 2. XỬ LÝ TIN NHẮN TỪ SERVER ---
function handleServerMessage(data) {
    if (data.type === "SYSTEM" || data.type === "LIST_USERS") {
        updateUserList(data.users || []);
    } 
    else if (data.type === "TEXT" || data.type === "FILE_INFO") {
        messages.push(data);
        if (isCurrentChat(data)) {
            renderMessage(data);
        }
    } 
    else if (data.type === "VIDEO_DATA") {
        const img = document.getElementById("remote-video-img");
        if(img) img.src = "data:image/jpeg;base64," + data.data;
    }
    else if (data.type === "CALL_REQUEST") {
        showIncomingCall(data.caller);
    }
    else if (data.type === "CALL_ACCEPT") {
        const modal = document.getElementById("incoming-call-modal");
        if (modal) modal.classList.add("hidden");
        switchChat(data.sender); 
        const area = document.getElementById("video-area");
        if(area) {
            area.classList.remove("hidden");
            startLocalVideo();
        }
    }
    else if (data.type === "CALL_END") {
        closeVideoArea();
    }
}

// --- 3. RENDER DANH SÁCH USER ---
function updateUserList(users) {
    const list = document.getElementById("user-list");
    if (!list) return;

    list.innerHTML = "";

    // Chat Nhóm
    const groupLi = document.createElement("li");
    groupLi.className = `user-item ${currentChat === null ? 'active' : ''}`;
    groupLi.onclick = () => switchChat(null);
    groupLi.innerHTML = `
        <div class="avatar" style="background: linear-gradient(135deg, #ff9a9e, #fecfef);">📢</div>
        <div class="user-info">
            <div class="user-name">Trò chuyện nhóm</div>
            <div class="user-preview">Tất cả mọi người</div>
        </div>
    `;
    list.appendChild(groupLi);

    // User Online
    users.forEach(u => {
        if (u === username) return;

        const li = document.createElement("li");
        li.className = `user-item ${currentChat === u ? 'active' : ''}`;
        li.onclick = () => switchChat(u);

        const initial = u.charAt(0).toUpperCase();
        li.innerHTML = `
            <div class="avatar" style="${getAvatarColor(u)}">${initial}</div>
            <div class="user-info">
                <div class="user-name">${u}</div>
                <div class="user-preview">Nhấn để chat riêng</div>
            </div>
        `;
        list.appendChild(li);
    });
}

// --- 4. RENDER TIN NHẮN ---
function renderMessage(data) {
    const box = document.getElementById("messages");
    if (!box) return;

    const isMe = data.sender === username;
    const div = document.createElement("div");
    div.className = `message ${isMe ? 'sent' : 'received'}`;

    const senderHtml = !isMe ? `<div class="sender-name">${data.sender}</div>` : '';
    const time = new Date(data.timestamp || Date.now()).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    let contentHtml = "";

    if (data.type === "FILE_INFO") {
        const url = `/downloads/${data.filename}`;
        if (data.file_type === "image") {
            contentHtml = `<img src="${url}" style="max-width: 250px; border-radius: 8px; cursor: pointer; margin-top:5px;" onclick="window.open('${url}')">`;
        } else {
            contentHtml = `
                <a href="${url}" target="_blank" class="file-attachment">
                    <div class="file-icon"><i class="fas fa-file"></i></div>
                    <div class="file-info">
                        <div>${data.original_filename}</div>
                        <div>${(data.filesize/1024).toFixed(1)} KB</div>
                    </div>
                </a>
            `;
        }
    } else {
        contentHtml = data.message || data.content || "";
    }

    div.innerHTML = `
        <div class="bubble">
            ${senderHtml}
            <div>${contentHtml}</div>
            <span class="msg-time">${time}</span>
        </div>
    `;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}

// --- 5. CHUYỂN TAB CHAT ---
function switchChat(user) {
    currentChat = user;

    const title = document.getElementById("chat-title");
    const status = document.getElementById("chat-status");
    if(title) title.innerText = user ? user : "Trò chuyện nhóm";
    if(status) status.innerText = user ? "Online" : "Trực tuyến";

    const items = document.querySelectorAll(".user-item");
    items.forEach(el => {
        el.classList.remove("active");
        if (user === null && el.innerHTML.includes("Trò chuyện nhóm")) el.classList.add("active");
        else if (user && el.innerHTML.includes(user)) el.classList.add("active");
    });

    const msgBox = document.getElementById("messages");
    if(msgBox) {
        msgBox.innerHTML = "";
        messages.forEach(msg => {
            if (isCurrentChat(msg)) renderMessage(msg);
        });
    }
}

function isCurrentChat(msg) {
    if (currentChat === null) return !msg.recipient;
    return (msg.sender === currentChat && msg.recipient === username) || 
           (msg.sender === username && msg.recipient === currentChat);
}

// --- 6. GỬI TIN ---
function sendMessage() {
    const input = document.getElementById("message-input");
    if (!input) return;
    const txt = input.value.trim();
    if (!txt) return;

    const msg = {
        type: "TEXT",
        message: txt,
        sender: username,
        recipient: currentChat,
        timestamp: new Date().toISOString()
    };

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(msg));
        messages.push(msg);
        renderMessage(msg);
        input.value = "";
    } else {
        alert("Chưa kết nối tới server!");
    }
}

function handleEnter(e) { if(e.key === "Enter") sendMessage(); }

// --- 7. UPLOAD FILE (WebSocket Stream + Speed Control) ---
async function uploadFile() {
    const fileInput = document.getElementById("file-input");
    if (!fileInput || !fileInput.files.length) return;
    
    const file = fileInput.files[0];
    const filesize = file.size;
    const filename = file.name;
    const recipient = currentChat || "";

    // 1. Reset UI
    isUploading = true;
    uploadCancelled = false;
    
    const progressContainer = document.getElementById("upload-progress-container");
    const filenameLabel = document.getElementById("upload-filename");
    const percentLabel = document.getElementById("upload-percent");
    const bar = document.getElementById("upload-bar");

    if(progressContainer) {
        progressContainer.classList.remove("hidden");
        filenameLabel.innerText = `Đang gửi: ${filename}`;
        percentLabel.innerText = "0%";
        bar.style.width = "0%";
    }

    // 2. Gửi Header (Báo hiệu bắt đầu)
    ws.send(JSON.stringify({
        type: "FILE_UPLOAD_START",
        data: {
            filename: filename,
            filesize: filesize,
            recipient: recipient
        }
    }));

    // 3. Bắt đầu gửi file từng phần
    let offset = 0;
    const reader = new FileReader();

    const sendNextChunk = () => {
        if (uploadCancelled) {
            resetUploadUI();
            return;
        }
        // Cắt file
        const slice = file.slice(offset, offset + CHUNK_SIZE);
        reader.readAsArrayBuffer(slice);
    };

    reader.onload = async (e) => {
        if (!isUploading) return;

        const chunk = e.target.result; // ArrayBuffer
        const chunkLen = chunk.byteLength;
        const startTime = Date.now();

        // [QUAN TRỌNG] Gửi Binary Data qua WebSocket
        ws.send(chunk);

        // --- Logic Giới Hạn Tốc Độ ---
        const expectedDuration = (chunkLen / UPLOAD_SPEED_LIMIT) * 1000; // ms
        const actualDuration = Date.now() - startTime;
        
        // Nếu gửi nhanh hơn tốc độ cho phép -> Ngủ bù
        if (actualDuration < expectedDuration) {
            await new Promise(r => setTimeout(r, expectedDuration - actualDuration));
        }
        // -----------------------------

        offset += chunkLen;

        // Cập nhật UI
        const percent = Math.min((offset / filesize) * 100, 100);
        if(bar) bar.style.width = percent + "%";
        if(percentLabel) percentLabel.innerText = Math.round(percent) + "%";

        // Kiểm tra xong chưa
        if (offset < filesize) {
            sendNextChunk(); // Tiếp tục gói sau
        } else {
            console.log("Upload hoàn tất");
            resetUploadUI();
        }
    };

    // Bắt đầu
    sendNextChunk();
    fileInput.value = "";
}

function cancelWebUpload() {
    uploadCancelled = true;
    isUploading = false;
    resetUploadUI();
    // Gửi tín hiệu hủy cho server
    ws.send(JSON.stringify({ type: "FILE_UPLOAD_CANCEL" }));
}

function resetUploadUI() {
    const progressContainer = document.getElementById("upload-progress-container");
    if (progressContainer) progressContainer.classList.add("hidden");
}

// --- 8. VIDEO CALL ---
function toggleVideo() {
    if (!currentChat) return alert("Chỉ hỗ trợ gọi video trong Chat Riêng!");
    ws.send(JSON.stringify({ type: "CALL_REQUEST", caller: username, recipient: currentChat }));

    const area = document.getElementById("video-area");
    if(area) {
        area.classList.remove("hidden");
        startLocalVideo();
    }
}

async function startLocalVideo() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        const video = document.getElementById("local-video");
        if(video) video.srcObject = stream;
    } catch (e) {
        console.error("Camera Error:", e);
        alert("Không thể truy cập Camera. Vui lòng cấp quyền!");
    }
}

function closeVideoArea() {
    const area = document.getElementById("video-area");
    if (area) area.classList.add("hidden");
    const video = document.getElementById("local-video");
    if(video && video.srcObject) {
        video.srcObject.getTracks().forEach(t => t.stop());
    }
}

function endCall() {
    if (ws && currentChat) {
        ws.send(JSON.stringify({ type: "CALL_END", recipient: currentChat, sender: username }));
    }
    closeVideoArea();
}

function showIncomingCall(caller) {
    const nameEl = document.getElementById("caller-name");
    const modal = document.getElementById("incoming-call-modal");
    if (nameEl && modal) {
        nameEl.innerText = `${caller} đang gọi...`;
        modal.classList.remove("hidden");
    }
}

function acceptCall() {
    const modal = document.getElementById("incoming-call-modal");
    if (modal) modal.classList.add("hidden");
    const nameEl = document.getElementById("caller-name");
    const callerName = nameEl ? nameEl.innerText.replace(" đang gọi...", "") : "";
    if (ws) {
        ws.send(JSON.stringify({ type: "CALL_ACCEPT", recipient: callerName, sender: username }));
    }
}

function rejectCall() {
    const modal = document.getElementById("incoming-call-modal");
    if (modal) modal.classList.add("hidden");
}

function getAvatarColor(name) {
    const colors = ["background: linear-gradient(135deg, #667eea, #764ba2)", "background: linear-gradient(135deg, #ff9a9e, #fecfef)", "background: linear-gradient(135deg, #43e97b, #38f9d7)"];
    let hash = 0;
    for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
    return colors[Math.abs(hash) % colors.length];
}