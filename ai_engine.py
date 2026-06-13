import requests
import logging
import time

logger = logging.getLogger(__name__)

class AIEngine:
    def __init__(self, gemini_key, openrouter_key, groq_key, together_key, huggingface_key):
        self.gemini_key = gemini_key
        self.openrouter_key = openrouter_key
        self.groq_key = groq_key
        self.together_key = together_key
        self.huggingface_key = huggingface_key
        self.gemini_models = ["gemini-2.0-flash", "gemini-1.5-flash-8b", "gemini-1.5-flash-latest", "gemini-1.5-pro-latest"]
        self.openrouter_models = ["meta-llama/llama-3.3-70b-instruct:free", "deepseek/deepseek-chat:free", "google/gemini-2.0-flash-exp:free", "mistralai/mistral-7b-instruct:free"]
        self.groq_models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
        self.together_url = "https://api.together.xyz/v1/chat/completions"
        self.huggingface_url = "https://api-inference.huggingface.co/models"

    def _get_gemini_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.gemini_key and self.gemini_key.startswith("AQ."):
            headers["x-goog-api-key"] = self.gemini_key
            return headers, None
        elif self.gemini_key and self.gemini_key.startswith("AIzaSy"):
            return headers, self.gemini_key
        return headers, None

    def ask_gemini(self, prompt, system=""):
        headers, key_param = self._get_gemini_headers()
        if not self.gemini_key: return None
        text = f"{system}\n\n{prompt}" if system else prompt
        payload = {"contents": [{"parts": [{"text": text}]}], "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048}}
        for model in self.gemini_models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                if key_param: url = f"{url}?key={key_param}"
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                if response.status_code == 429:
                    logger.warning(f"Gemini {model}: 429")
                    time.sleep(1)
                    continue
                response.raise_for_status()
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        logger.info(f"Gemini {model} success")
                        return candidate["content"]["parts"][0]["text"]
            except Exception as e:
                logger.warning(f"Gemini {model} failed: {e}")
                continue
        return None

    def ask_openrouter(self, prompt, system=""):
        if not self.openrouter_key or not self.openrouter_key.startswith("sk-or-v1"): return None
        headers = {"Authorization": f"Bearer {self.openrouter_key}", "Content-Type": "application/json", "HTTP-Referer": "https://moallem-bot.yemen", "X-Title": "Moallem Bot"}
        messages = []
        if system: messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        for model in self.openrouter_models:
            try:
                payload = {"model": model, "messages": messages, "temperature": 0.3}
                response = requests.post(self.openrouter_url, headers=headers, json=payload, timeout=30)
                if response.status_code == 429: continue
                response.raise_for_status()
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
            except Exception as e:
                logger.warning(f"OpenRouter {model} failed: {e}")
                continue
        return None

    def ask_groq(self, prompt, system=""):
        if not self.groq_key or not self.groq_key.startswith("gsk_"): return None
        headers = {"Authorization": f"Bearer {self.groq_key}", "Content-Type": "application/json"}
        messages = []
        if system: messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        for model in self.groq_models:
            try:
                payload = {"model": model, "messages": messages, "temperature": 0.3, "max_tokens": 2048}
                response = requests.post(self.groq_url, headers=headers, json=payload, timeout=30)
                if response.status_code == 429:
                    time.sleep(1)
                    continue
                response.raise_for_status()
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
            except Exception as e:
                logger.warning(f"Groq {model} failed: {e}")
                continue
        return None

    def ask_together(self, prompt, system=""):
        if not self.together_key: return None
        headers = {"Authorization": f"Bearer {self.together_key}", "Content-Type": "application/json"}
        messages = []
        if system: messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            payload = {"model": "meta-llama/Llama-3.3-70B-Instruct-Turbo", "messages": messages, "temperature": 0.3, "max_tokens": 2048}
            response = requests.post(self.together_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"Together failed: {e}")
        return None

    def ask_huggingface(self, prompt, system=""):
        if not self.huggingface_key: return None
        try:
            headers = {"Authorization": f"Bearer {self.huggingface_key}"}
            payload = {"inputs": f"{system}\n\n{prompt}" if system else prompt, "parameters": {"max_new_tokens": 2048, "temperature": 0.3}}
            response = requests.post(f"{self.huggingface_url}/meta-llama/Llama-3.1-8B-Instruct", headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", "")
        except Exception as e:
            logger.warning(f"HuggingFace failed: {e}")
        return None

    def ask(self, prompt, dept_name="", context=None):
        system = f"أنت خبير عالمي في {dept_name}. أجب بشكل علمي دقيق وموضوعي. لا تذكر اليمن أو جامعة تعز إلا إذا طُلب صراحة. أجب بالعربية الفصحى." if dept_name else "أنت مساعد أكاديمي ذكي. أجب بالعربية الفصحى."
        if context:
            prompt = f"سياق المحادثة السابقة:\n{context}\n\nالسؤال الجديد: {prompt}"
        engines = [("Gemini", self.ask_gemini(prompt, system)), ("Groq", self.ask_groq(prompt, system)), ("OpenRouter", self.ask_openrouter(prompt, system)), ("Together", self.ask_together(prompt, system)), ("HuggingFace", self.ask_huggingface(prompt, system))]
        for name, answer in engines:
            if answer and not answer.startswith("❌") and len(answer) > 10:
                logger.info(f"Engine {name} succeeded")
                return answer
        return "❌ جميع خدمات الذكاء الاصطناعي غير متاحة حالياً.\n\n💡 الحلول:\n• جرّب بعد دقيقة\n• تأكد من الاتصال بالإنترنت"
