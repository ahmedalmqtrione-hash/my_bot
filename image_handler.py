import base64
import requests
import logging

logger = logging.getLogger(__name__)

class ImageHandler:
    def __init__(self, gemini_key):
        self.gemini_key = gemini_key
        self.url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

    def _get_gemini_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.gemini_key and self.gemini_key.startswith("AQ."):
            headers["x-goog-api-key"] = self.gemini_key
            return headers, None
        elif self.gemini_key and self.gemini_key.startswith("AIzaSy"):
            return headers, self.gemini_key
        return headers, None

    def analyze(self, image_path, prompt="اشرح ما في هذه الصورة بالتفصيل واقرأ أي نص موجود فيها"):
        try:
            if not self.gemini_key:
                return "❌ مفتاح Gemini غير محدد."
            headers, key_param = self._get_gemini_headers()
            url = self.url
            if key_param: url = f"{url}?key={key_param}"
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            payload = {"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}]}]}
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    return candidate["content"]["parts"][0]["text"]
            if "error" in result:
                return f"❌ خطأ Gemini: {result['error'].get('message', 'غير معروف')}"
            return "❌ لم أتمكن من تحليل الصورة."
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                return "❌ الحصة انتهت (429)."
            return f"❌ خطأ HTTP: {e.response.status_code}"
        except Exception as e:
            return f"❌ خطأ: {str(e)}"
