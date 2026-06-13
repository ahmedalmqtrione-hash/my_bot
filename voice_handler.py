import os
import requests

class VoiceHandler:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.url = "https://api.groq.com/openai/v1/audio/transcriptions"

    def transcribe(self, audio_path):
        try:
            if not self.api_key:
                return "❌ لم يتم تعيين مفتاح API للصوت.\n\n💡 استخدم الكتابة الصوتية في لوحة المفاتيح."
            headers = {"Authorization": f"Bearer {self.api_key}"}
            with open(audio_path, "rb") as f:
                files = {"file": (os.path.basename(audio_path), f, "audio/ogg")}
                data = {"model": "whisper-large-v3", "language": "ar", "response_format": "text"}
                response = requests.post(self.url, headers=headers, files=files, data=data, timeout=60)
                response.raise_for_status()
                return response.text.strip()
        except Exception as e:
            return f"❌ خطأ في تحويل الصوت: {str(e)}"
