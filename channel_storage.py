import logging
from database import db

logger = logging.getLogger(__name__)

class ChannelStorage:
    def __init__(self, channel_id):
        self.channel_id = channel_id

    async def store_file(self, bot, file_obj, file_name, file_type, category, department, caption, uploaded_by):
        try:
            if not self.channel_id:
                logger.error("Channel ID not configured")
                return None, "❌ قناة التخزين غير مكونة."
            if hasattr(file_obj, "file_id"):
                if file_type in ["photo", "jpg", "jpeg", "png"]:
                    msg = await bot.send_photo(chat_id=self.channel_id, photo=file_obj.file_id, caption=f"📁 {file_name}\n📂 {category}\n🏛️ {department}\n💬 {caption or ''}")
                elif file_type in ["video", "mp4"]:
                    msg = await bot.send_video(chat_id=self.channel_id, video=file_obj.file_id, caption=f"📁 {file_name}\n📂 {category}\n🏛️ {department}")
                elif file_type in ["audio", "voice", "ogg"]:
                    msg = await bot.send_audio(chat_id=self.channel_id, audio=file_obj.file_id, caption=f"📁 {file_name}\n📂 {category}")
                else:
                    msg = await bot.send_document(chat_id=self.channel_id, document=file_obj.file_id, caption=f"📁 {file_name}\n📂 {category}\n🏛️ {department}\n💬 {caption or ''}")
                db.save_channel_file(file_id=file_obj.file_id, file_unique_id=getattr(file_obj, "file_unique_id", file_obj.file_id), file_name=file_name, file_type=file_type, category=category, department=department, caption=caption, file_size=getattr(file_obj, "file_size", 0), uploaded_by=uploaded_by, message_id=msg.message_id)
                return file_obj.file_id, "✅ تم حفظ الملف في القناة بنجاح!"
            return None, "❌ خطأ في معالجة الملف."
        except Exception as e:
            logger.error(f"Store file error: {e}")
            return None, f"❌ خطأ: {str(e)}"

    async def retrieve_file(self, bot, file_id):
        try:
            return await bot.get_file(file_id)
        except Exception as e:
            logger.error(f"Retrieve file error: {e}")
            return None
