import os
import re
import logging

try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

logger = logging.getLogger(__name__)

class FileHandler:
    def __init__(self):
        self.max_size = 50 * 1024 * 1024

    def extract_text(self, file_path):
        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".pdf":
                return self._extract_pdf(file_path)
            elif ext in [".doc", ".docx"]:
                return self._extract_docx(file_path)
            elif ext == ".txt":
                return self._extract_txt(file_path)
            else:
                return None
        except Exception as e:
            logger.error(f"Extract text error: {e}")
            return None

    def _extract_pdf(self, file_path):
        if not PDF_AVAILABLE:
            return "❌ مكتبة PyPDF2 غير مثبتة."
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text[:8000]
        except Exception as e:
            return f"❌ خطأ في قراءة PDF: {str(e)}"

    def _extract_docx(self, file_path):
        if not DOCX_AVAILABLE:
            return "❌ مكتبة python-docx غير مثبتة."
        try:
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text[:8000]
        except Exception as e:
            return f"❌ خطأ في قراءة Word: {str(e)}"

    def _extract_txt(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()[:8000]
        except:
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    return f.read()[:8000]
            except Exception as e:
                return f"❌ خطأ: {str(e)}"

    def summarize(self, text, max_sentences=5):
        if not text or len(text) < 100:
            return "❌ النص قصير جداً للتلخيص."
        sentences = re.split(r"[.!?\n]+", text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        if len(sentences) <= max_sentences:
            return "\n".join(sentences)
        selected = [sentences[0]]
        step = len(sentences) // max_sentences
        for i in range(1, max_sentences - 1):
            idx = i * step
            if idx < len(sentences):
                selected.append(sentences[idx])
        selected.append(sentences[-1])
        return "\n".join(selected)
