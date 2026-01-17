"""
Xử lý logic cuộc gọi video/audio
Client/handlers/call_handler.py
"""

from common.protocol import Protocol, MessageType
from client.ui.call_ui import CallUI

class CallHandler:
    def __init__(self, client):
        self.client = client
    
    def handle_call_request(self, data):
        """Xử lý yêu cầu gọi đến"""
        caller = data.get("caller")
        call_type = data.get("call_type")
        
        # Kiểm tra nếu đang trong cuộc gọi khác
        if self.client.current_call:
            # Gửi BUSY
            Protocol.send_message(
                self.client.socket,
                MessageType.CALL_BUSY,
                {
                    "caller": caller,
                    "recipient": self.client.username
                }
            )
            return
        
        # Hiển thị incoming call UI
        self.client.root.after(0, self._show_incoming_call, caller, call_type)
    # Thêm các method xử lý data vào class CallHandler
    
    def handle_video_data(self, data):
        """Nhận dữ liệu video từ server"""
        if self.client.current_call:
            video_content = data.get("data")
            # Gọi giao diện để hiển thị
            self.client.current_call.process_incoming_video(video_content)

    def handle_audio_data(self, data):
        """Nhận dữ liệu audio từ server"""
        if self.client.current_call:
            audio_content = data.get("data")
            # Gọi giao diện để phát âm thanh
            self.client.current_call.process_incoming_audio(audio_content)
    def _show_incoming_call(self, caller, call_type):
        """Hiển thị UI cuộc gọi đến"""
        call_ui = CallUI(self.client, caller, call_type, is_caller=False)
    
    def handle_call_accept(self, data):
        """Xử lý khi cuộc gọi được chấp nhận"""
        if self.client.current_call:
            self.client.root.after(0, self.client.current_call.on_call_accepted)
    
    def handle_call_reject(self, data):
        """Xử lý khi cuộc gọi bị từ chối"""
        if self.client.current_call:
            self.client.root.after(0, self.client.current_call.on_call_rejected)
    
    def handle_call_busy(self, data):
        """Xử lý khi người nhận đang bận"""
        if self.client.current_call:
            self.client.root.after(0, 
                self.client.message_handler.show_system_message,
                f"📞 {data.get('recipient')} đang bận"
            )
            self.client.current_call.window.destroy()
            self.client.current_call = None
    
    def handle_call_end(self, data):
        """Xử lý khi cuộc gọi kết thúc"""
        if self.client.current_call:
            self.client.root.after(0, self.client.current_call.on_call_ended)
    
    def handle_webrtc_offer(self, data):
        """Xử lý WebRTC offer"""
        # TODO: Tích hợp WebRTC
        pass
    
    def handle_webrtc_answer(self, data):
        """Xử lý WebRTC answer"""
        # TODO: Tích hợp WebRTC
        pass
    
    def handle_webrtc_ice(self, data):
        """Xử lý ICE candidate"""
        # TODO: Tích hợp WebRTC
        pass