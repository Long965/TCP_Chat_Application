/**
 * static/script.js - Logic Web Client
 * Updated: Parallel Uploads & Downloads + Pause/Resume + Cancel
 */
let ws;
let username = "";
let currentChat = null; // null = Chat nhóm
let messages = [];      // Lưu trữ lịch sử tin nhắn

// --- CẤU HÌNH ---
const UPLOAD_SPEED_LIMIT = 100 * 1024; // 100KB/s (Để demo)
const CHUNK_SIZE = 8192; 

// Quản lý Upload
const activeUploads = {};
const uploadStates = {};

// [MỚI] Quản lý Download
const activeDownloads = {};

// Tự động chạy khi trang web tải xong để reset UI
document.addEventListener("DOMContentLoaded", () => {
    resetUploadUI();
});

// --- 1. KẾT NỐI & LOGIN (GIỮ NGUYÊN) ---
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
        resetUploadUI();
    };
    ws.onmessage = (event) => {
        try { handleServerMessage(JSON.parse(event.data)); } catch (e) { console.error(e); }
    };
    ws.onclose = () => { alert("Mất kết nối server!"); location.reload(); };
}

// --- 2. XỬ LÝ TIN NHẮN (GIỮ NGUYÊN) ---
function handleServerMessage(data) {
    if (data.type === "SYSTEM" || data.type === "LIST_USERS") updateUserList(data.users || []);
    else if (data.type === "TEXT" || data.type === "FILE_INFO") {
        messages.push(data);
        if (isCurrentChat(data)) renderMessage(data);
    } 
    else if (data.type === "VIDEO_DATA") {
        const img = document.getElementById("remote-video-img");
        if(img && data.data) img.src = "data:image/jpeg;base64," + data.data;
    }
    else if (data.type === "CALL_REQUEST") showIncomingCall(data.caller);
    else if (data.type === "CALL_ACCEPT") {
        document.getElementById("incoming-call-modal").classList.add("hidden");
        switchChat(data.sender); document.getElementById("video-area").classList.remove("hidden"); startLocalVideo();
    }
    else if (data.type === "CALL_END" || data.type === "CALL_REJECT") {
        closeVideoArea(); document.getElementById("incoming-call-modal").classList.add("hidden");
        if (data.type === "CALL_REJECT") alert("Cuộc gọi bị từ chối.");
    }
}

// --- 3. RENDER DANH SÁCH USER (GIỮ NGUYÊN) ---
function updateUserList(users) {
    const list = document.getElementById("user-list");
    if (!list) return;
    list.innerHTML = "";
    const groupLi = document.createElement("li");
    groupLi.className = `user-item ${currentChat === null ? 'active' : ''}`;
    groupLi.onclick = () => switchChat(null);
    groupLi.innerHTML = `<div class="avatar" style="background: linear-gradient(135deg, #ff9a9e, #fecfef);">📢</div><div class="user-info"><div class="user-name">Trò chuyện nhóm</div><div class="user-preview">Tất cả mọi người</div></div>`;
    list.appendChild(groupLi);
    users.forEach(u => {
        if (u === username || u.includes("_upload_") || u.includes("_download_")) return; // [FIX] Lọc cả user download
        const li = document.createElement("li");
        li.className = `user-item ${currentChat === u ? 'active' : ''}`;
        li.onclick = () => switchChat(u);
        li.innerHTML = `<div class="avatar" style="${getAvatarColor(u)}">${u.charAt(0).toUpperCase()}</div><div class="user-info"><div class="user-name">${u}</div><div class="user-preview">Nhấn để chat riêng</div></div>`;
        list.appendChild(li);
    });
}

// --- 4. RENDER TIN NHẮN (CẬP NHẬT NÚT TẢI) ---
function renderMessage(data) {
    const box = document.getElementById("messages");
    if (!box) return;
    const isMe = data.sender === username;
    const div = document.createElement("div");
    div.className = `message ${isMe ? 'sent' : 'received'}`;
    const time = new Date(data.timestamp || Date.now()).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
    
    let contentHtml = "";
    if (data.type === "FILE_INFO") {
        const displayName = data.original_filename || data.filename;
        const sizeStr = (data.filesize/1024).toFixed(1) + " KB";
        
        // [CẬP NHẬT] Nút Download gọi hàm startDownloadCustom
        contentHtml = `
            <div class="file-attachment">
                <div class="file-icon"><i class="fas fa-file"></i></div>
                <div class="file-info">
                    <div style="font-weight:bold; overflow:hidden; text-overflow:ellipsis; max-width:180px;">${displayName}</div>
                    <div style="font-size:11px">${sizeStr}</div>
                </div>
                <button onclick="startDownloadCustom('${data.filename}', '${displayName}', ${data.filesize})" 
                        style="background:none; border:none; color:white; cursor:pointer; font-size:18px; margin-left:10px;"
                        title="Tải xuống">
                    <i class="fas fa-download"></i>
                </button>
            </div>
        `;
    } else {
        contentHtml = data.message || data.content || "";
    }
    div.innerHTML = `<div class="bubble">${!isMe ? `<div class="sender-name">${data.sender}</div>` : ''}<div>${contentHtml}</div><span class="msg-time">${time}</span></div>`;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}

// --- 5. & 6. CHUYỂN TAB & GỬI TIN (GIỮ NGUYÊN) ---
function switchChat(user) {
    currentChat = user;
    const title = document.getElementById("chat-title");
    const status = document.getElementById("chat-status");
    if(title) title.innerText = user ? user : "Trò chuyện nhóm";
    if(status) status.innerText = user ? "Online" : "Trực tuyến";
    document.querySelectorAll(".user-item").forEach(el => {
        el.classList.remove("active");
        if (user === null && el.innerHTML.includes("Trò chuyện nhóm")) el.classList.add("active");
        else if (user && el.innerHTML.includes(user)) el.classList.add("active");
    });
    const msgBox = document.getElementById("messages");
    if(msgBox) {
        msgBox.innerHTML = "";
        messages.forEach(msg => { if (isCurrentChat(msg)) renderMessage(msg); });
    }
}
function isCurrentChat(msg) {
    if (currentChat === null) return !msg.recipient;
    return (msg.sender === currentChat && msg.recipient === username) || (msg.sender === username && msg.recipient === currentChat);
}
function sendMessage() {
    const input = document.getElementById("message-input");
    if (!input || !input.value.trim()) return;
    const msg = { type: "TEXT", message: input.value.trim(), sender: username, recipient: currentChat, timestamp: new Date().toISOString() };
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(msg)); messages.push(msg); renderMessage(msg); input.value = "";
    } else { alert("Chưa kết nối tới server!"); }
}
function handleEnter(e) { if(e.key === "Enter") sendMessage(); }

// ============================================================
// === TRÌNH QUẢN LÝ TIẾN TRÌNH (CHUNG CHO UPLOAD & DOWNLOAD) ===
// ============================================================

function createProgressItem(name, type) {
    // type: 'up' (Upload - Xanh lá), 'down' (Download - Xanh dương)
    const container = document.getElementById("upload-progress-container");
    if (!container) return null;
    container.classList.remove("hidden");
    
    const id = type + "-" + Date.now() + "-" + Math.floor(Math.random() * 1000);
    const div = document.createElement("div");
    div.className = "upload-item"; 
    div.id = id;
    div.style.cssText = "margin-bottom:10px; background:rgba(255,255,255,0.1); padding:8px; border-radius:5px; transition:opacity 0.5s;";

    // Chọn màu và icon
    const iconClass = type === 'down' ? 'fa-arrow-down' : 'fa-arrow-up';
    const color = type === 'down' ? '#2196f3' : '#4caf50'; 

    div.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; font-size:12px;">
            <div style="display:flex; flex-direction:column; overflow:hidden; padding-right:10px; flex-grow:1;">
                <span style="font-weight:bold; color:white; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                    <i class="fas ${iconClass}" style="margin-right:5px; color:${color}"></i>${name}
                </span>
                <span id="${id}-percent" style="color:#eee; font-size:10px;">0%</span>
            </div>
            <div style="display:flex; gap: 10px;">
                <span onclick="${type === 'up' ? `togglePauseUpload('${id}')` : `togglePauseDownload('${id}')`}" 
                      style="color:${color}; cursor:pointer; font-size:14px;" title="Tạm dừng/Tiếp tục">
                      <i id="${id}-btn-icon" class="fas fa-pause"></i>
                </span>
                <span onclick="${type === 'up' ? `cancelUpload('${id}')` : `cancelDownload('${id}')`}" 
                      style="color:#ff6b6b; cursor:pointer; font-size:16px; font-weight:bold;" title="Hủy">✖</span>
            </div>
        </div>
        <div style="width:100%; background:#444; height:4px; border-radius:2px; margin-top:2px;">
            <div id="${id}-bar" style="width:0%; height:100%; background:${color}; border-radius:2px; transition: width 0.2s;"></div>
        </div>
    `;
    container.appendChild(div);
    return id;
}

function checkAndHideContainer() {
    const container = document.getElementById("upload-progress-container");
    if (container && container.children.length === 0) container.classList.add("hidden");
}

// ============================================================
// === LOGIC DOWNLOAD (MỚI) ===
// ============================================================

function startDownloadCustom(serverFilename, displayFilename, filesize) {
    const uiID = createProgressItem(displayFilename, 'down');
    
    activeDownloads[uiID] = {
        serverFilename: serverFilename,
        displayFilename: displayFilename,
        totalBytes: filesize,
        receivedBytes: 0,
        chunks: [], // Lưu trữ binary data
        socket: null,
        isPaused: false
    };

    connectDownloadSocket(uiID);
}

function connectDownloadSocket(uiID) {
    const task = activeDownloads[uiID];
    if (!task) return;

    const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
    const host = window.location.host;
    const ghostUser = `${username}_download_${Date.now()}`;
    const wsDown = new WebSocket(`${protocol}${host}/ws/${ghostUser}`);

    task.socket = wsDown;

    wsDown.onopen = () => {
        wsDown.send(JSON.stringify({
            type: "FILE_DOWNLOAD_REQUEST",
            data: { filename: task.serverFilename, offset: task.receivedBytes }
        }));
    };

    wsDown.onmessage = (event) => {
        // 1. Nhận thông báo hoàn tất hoặc lỗi (JSON)
        if (typeof event.data === "string") {
            const msg = JSON.parse(event.data);
            if (msg.type === "DOWNLOAD_COMPLETE") {
                finishDownload(uiID);
            } else if (msg.type === "ERROR") {
                alert("Lỗi tải file: " + msg.message);
                cancelDownload(uiID);
            }
        } 
        // 2. Nhận dữ liệu Binary (Blob)
        else if (event.data instanceof Blob) {
            if (task.isPaused) return;

            const blob = event.data;
            task.chunks.push(blob);
            task.receivedBytes += blob.size;

            // Cập nhật UI
            const percent = (task.receivedBytes / task.totalBytes) * 100;
            const bar = document.getElementById(`${uiID}-bar`);
            const label = document.getElementById(`${uiID}-percent`);
            
            if (bar) bar.style.width = percent + "%";
            if (label && !task.isPaused) label.innerText = Math.round(percent) + "%";
        }
    };

    wsDown.onclose = () => {
        // Nếu đóng socket mà chưa xong và không phải do user pause -> Lỗi mạng
        if (activeDownloads[uiID] && !task.isPaused && task.receivedBytes < task.totalBytes) {
            const label = document.getElementById(`${uiID}-percent`);
            if(label) { label.innerText = "Lỗi mạng"; label.style.color = "red"; }
        }
    };
}

function togglePauseDownload(uiID) {
    const task = activeDownloads[uiID];
    const btnIcon = document.getElementById(`${uiID}-btn-icon`);
    const label = document.getElementById(`${uiID}-percent`);
    
    if (!task) return;

    if (task.isPaused) {
        // --- RESUME ---
        task.isPaused = false;
        if(btnIcon) { btnIcon.classList.remove("fa-play"); btnIcon.classList.add("fa-pause"); }
        if(label) label.style.color = "#eee";
        connectDownloadSocket(uiID); // Mở lại socket mới để tải tiếp
    } else {
        // --- PAUSE ---
        task.isPaused = true;
        if(task.socket) task.socket.close(); // Đóng socket để ngắt tải
        if(btnIcon) { btnIcon.classList.remove("fa-pause"); btnIcon.classList.add("fa-play"); }
        if(label) { label.innerText = "Tạm dừng"; label.style.color = "#ffcc00"; }
    }
}

function cancelDownload(uiID) {
    const task = activeDownloads[uiID];
    if (task) {
        if (task.socket) task.socket.close();
        task.chunks = []; // Xóa dữ liệu trong RAM
        delete activeDownloads[uiID];
    }
    const item = document.getElementById(uiID);
    if (item) item.remove();
    checkAndHideContainer();
}

function finishDownload(uiID) {
    const task = activeDownloads[uiID];
    if (!task) return;

    // Gộp chunks thành file hoàn chỉnh
    const completeBlob = new Blob(task.chunks);
    const url = URL.createObjectURL(completeBlob);

    // Kích hoạt tải xuống trình duyệt
    const a = document.createElement("a");
    a.href = url;
    a.download = task.displayFilename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    // Xóa UI sau 2s
    const label = document.getElementById(`${uiID}-percent`);
    if(label) { label.innerText = "Hoàn tất"; label.style.color = "#2196f3"; }
    
    // Ẩn nút
    const btnIcon = document.getElementById(`${uiID}-btn-icon`);
    if(btnIcon && btnIcon.parentElement) btnIcon.parentElement.style.display = 'none';

    if(task.socket) task.socket.close();
    delete activeDownloads[uiID];

    setTimeout(() => {
        const item = document.getElementById(uiID);
        if (item) item.remove();
        checkAndHideContainer();
    }, 2000);
}

// ============================================================
// === LOGIC UPLOAD (ĐÃ NÂNG CẤP VÀ ĐỔI TÊN HÀM CHO KHỚP UI) ===
// ============================================================

function togglePauseUpload(uiID) { 
    const state = uploadStates[uiID];
    const btnIcon = document.getElementById(`${uiID}-btn-icon`);
    const label = document.getElementById(`${uiID}-percent`);
    if (!state) return;
    if (state.isPaused) {
        state.isPaused = false;
        if(btnIcon) { btnIcon.classList.remove("fa-play"); btnIcon.classList.add("fa-pause"); }
        if(label) label.style.color = "#eee";
        if (state.resume) state.resume(); 
    } else {
        state.isPaused = true;
        if(btnIcon) { btnIcon.classList.remove("fa-pause"); btnIcon.classList.add("fa-play"); }
        if(label) { label.innerText = "Tạm dừng"; label.style.color = "#ffcc00"; }
    }
}

function cancelUpload(uiID) { 
    const item = document.getElementById(uiID);
    if (activeUploads[uiID]) {
        try { activeUploads[uiID].send(JSON.stringify({ type: "FILE_UPLOAD_CANCEL" })); activeUploads[uiID].close(); } catch(e){}
        delete activeUploads[uiID]; delete uploadStates[uiID];
    }
    if (item) item.remove();
    checkAndHideContainer();
}

async function uploadFiles() {
    const fileInput = document.getElementById("file-input");
    if (!fileInput || !fileInput.files.length) return;
    const files = Array.from(fileInput.files);
    fileInput.value = ""; 
    files.forEach(file => {
        // [QUAN TRỌNG] Gọi createProgressItem với type 'up'
        const uiID = createProgressItem(file.name, 'up'); 
        if (uiID) uploadFileParallel(file, uiID);
    });
}

function uploadFileParallel(file, uiID) {
    const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
    const host = window.location.host;
    const ghostUsername = `${username}_upload_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
    const wsUpload = new WebSocket(`${protocol}${host}/ws/${ghostUsername}`);

    activeUploads[uiID] = wsUpload;
    uploadStates[uiID] = { isPaused: false, resume: null };

    const filesize = file.size;
    const originalFilename = file.name;
    const safeFilename = `${Date.now()}_${originalFilename}`;
    const recipient = currentChat || "";
    const bar = document.getElementById(`${uiID}-bar`);
    const label = document.getElementById(`${uiID}-percent`);

    const removeUI = (delay) => {
        delete activeUploads[uiID]; delete uploadStates[uiID];
        setTimeout(() => {
            const item = document.getElementById(uiID);
            if (item) { item.style.opacity = "0"; setTimeout(() => { if(item)item.remove(); checkAndHideContainer(); }, 500); }
        }, delay);
    };

    wsUpload.onopen = () => {
        if (!document.getElementById(uiID)) { wsUpload.close(); delete activeUploads[uiID]; return; }
        wsUpload.send(JSON.stringify({
            type: "FILE_UPLOAD_START",
            data: { filename: safeFilename, original_filename: originalFilename, filesize, recipient, sender: username }
        }));

        let offset = 0;
        const reader = new FileReader();

        const sendNextChunk = async () => {
            if (!document.getElementById(uiID) || !activeUploads[uiID]) { wsUpload.close(); return; }
            if (uploadStates[uiID] && uploadStates[uiID].isPaused) {
                uploadStates[uiID].resume = sendNextChunk; return;
            }
            const slice = file.slice(offset, offset + CHUNK_SIZE);
            reader.readAsArrayBuffer(slice);
        };

        reader.onload = async (e) => {
            if (wsUpload.readyState !== WebSocket.OPEN) return;
            const chunk = e.target.result;
            const startTime = Date.now();
            wsUpload.send(chunk); 
            
            const expectedDuration = (chunk.byteLength / UPLOAD_SPEED_LIMIT) * 1000;
            const actualDuration = Date.now() - startTime;
            if (actualDuration < expectedDuration) await new Promise(r => setTimeout(r, expectedDuration - actualDuration));

            offset += chunk.byteLength;
            const percent = Math.min((offset / filesize) * 100, 100);
            
            if (offset < filesize) {
                if(bar) bar.style.width = percent + "%";
                if(label && !uploadStates[uiID].isPaused) label.innerText = Math.round(percent) + "%";
                setTimeout(sendNextChunk, 0);
            } else {
                if(bar) bar.style.width = "100%";
                if(label) { label.innerText = "Hoàn tất"; label.style.color = "#4caf50"; }
                const btnIcon = document.getElementById(`${uiID}-btn-icon`);
                if(btnIcon && btnIcon.parentElement) btnIcon.parentElement.style.display = 'none';

                try {
                    addLocalFileMessage(safeFilename, originalFilename, filesize);
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({
                            type: "FILE_INFO", sender: username, recipient: recipient,
                            filename: safeFilename, original_filename: originalFilename, filesize,
                            file_type: isImage(safeFilename) ? "image" : "file", timestamp: new Date().toISOString()
                        }));
                    }
                } finally { wsUpload.close(); removeUI(2000); }
            }
        };
        sendNextChunk();
    };
    wsUpload.onerror = () => { wsUpload.close(); removeUI(2000); };
}

// --- UTILS & VIDEO CALL (GIỮ NGUYÊN) ---
function addLocalFileMessage(safeFilename, originalFilename, filesize) {
    const msg = { type: "FILE_INFO", sender: username, recipient: currentChat, filename: safeFilename, original_filename: originalFilename, filesize: filesize, file_type: isImage(safeFilename) ? "image" : "file", timestamp: new Date().toISOString() };
    messages.push(msg); if (isCurrentChat(msg)) renderMessage(msg);
}
function resetUploadUI() { const c = document.getElementById("upload-progress-container"); if(c) { c.innerHTML=""; c.classList.add("hidden"); } }
function togglePauseWebUpload() { alert("Đã hỗ trợ tạm dừng từng file!"); }
function cancelWebUpload() {} 

function updateUserList(users) {
    const list = document.getElementById("user-list"); if(!list) return; list.innerHTML = "";
    const groupLi = document.createElement("li"); groupLi.className = `user-item ${currentChat === null ? 'active' : ''}`; groupLi.onclick = () => switchChat(null); groupLi.innerHTML = `<div class="avatar" style="background: linear-gradient(135deg, #ff9a9e, #fecfef);">📢</div><div class="user-info"><div class="user-name">Trò chuyện nhóm</div><div class="user-preview">Tất cả mọi người</div></div>`; list.appendChild(groupLi);
    users.forEach(u => {
        if (u === username || u.includes("_upload_") || u.includes("_download_")) return;
        const li = document.createElement("li"); li.className = `user-item ${currentChat === u ? 'active' : ''}`; li.onclick = () => switchChat(u); li.innerHTML = `<div class="avatar" style="${getAvatarColor(u)}">${u.charAt(0).toUpperCase()}</div><div class="user-info"><div class="user-name">${u}</div><div class="user-preview">Nhấn để chat riêng</div></div>`; list.appendChild(li);
    });
}
function toggleVideo() { if (!currentChat) return alert("Chỉ hỗ trợ Chat Riêng!"); ws.send(JSON.stringify({ type: "CALL_REQUEST", caller: username, recipient: currentChat })); document.getElementById("video-area").classList.remove("hidden"); startLocalVideo(); }
async function startLocalVideo() { try { const s = await navigator.mediaDevices.getUserMedia({ video: true, audio: true }); const v = document.getElementById("local-video"); if(v) v.srcObject = s; } catch (e) { alert("Lỗi Camera: " + e); } }
function closeVideoArea() { document.getElementById("video-area").classList.add("hidden"); const v = document.getElementById("local-video"); if(v && v.srcObject) { v.srcObject.getTracks().forEach(t => t.stop()); v.srcObject = null; } document.getElementById("remote-video-img").src = ""; }
function endCall() { if (ws && currentChat) ws.send(JSON.stringify({ type: "CALL_END", recipient: currentChat, sender: username })); closeVideoArea(); }
function showIncomingCall(c) { document.getElementById("caller-name").innerText = `${c} đang gọi...`; document.getElementById("incoming-call-modal").classList.remove("hidden"); }
function acceptCall() { document.getElementById("incoming-call-modal").classList.add("hidden"); const c = document.getElementById("caller-name").innerText.replace(" đang gọi...", ""); if (ws) ws.send(JSON.stringify({ type: "CALL_ACCEPT", recipient: c, sender: username })); if (c) switchChat(c); document.getElementById("video-area").classList.remove("hidden"); startLocalVideo(); }
function rejectCall() { document.getElementById("incoming-call-modal").classList.add("hidden"); const c = document.getElementById("caller-name").innerText.replace(" đang gọi...", ""); if (ws) ws.send(JSON.stringify({ type: "CALL_REJECT", recipient: c, sender: username })); }
function isImage(filename) { return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(filename.split('.').pop().toLowerCase()); }
function getAvatarColor(n) { const c = ["background: linear-gradient(135deg, #667eea, #764ba2)", "background: linear-gradient(135deg, #ff9a9e, #fecfef)", "background: linear-gradient(135deg, #43e97b, #38f9d7)"]; let h = 0; for (let i = 0; i < n.length; i++) h = n.charCodeAt(i) + ((h << 5) - h); return c[Math.abs(h) % c.length]; }