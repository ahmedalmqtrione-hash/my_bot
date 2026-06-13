import os
import logging
import asyncio
import urllib.parse
import aiohttp
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from flask import Flask, request

from config import (
    TELEGRAM_BOT_TOKEN, PROJECT_NAME, VERSION, UNIVERSITY,
    DEVELOPER_NAME, DEVELOPER_PHONE, DEPARTMENTS, ADMIN_ID, ADMIN_PASSWORD,
    GEMINI_API_KEY, OPENROUTER_API_KEY, GROQ_API_KEY, TOGETHER_API_KEY, HUGGINGFACE_API_KEY,
    STORAGE_CHANNEL_ID, STORAGE_CHANNEL_LINK, WEBHOOK_URL, PORT
)
from database import db
from memory import memory
from ai_engine import AIEngine
from image_handler import ImageHandler
from voice_handler import VoiceHandler
from file_handler import FileHandler
from channel_storage import ChannelStorage
from admin import AdminPanel
from games import Games

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

ai = AIEngine(GEMINI_API_KEY, OPENROUTER_API_KEY, GROQ_API_KEY, TOGETHER_API_KEY, HUGGINGFACE_API_KEY)
image_handler = ImageHandler(GEMINI_API_KEY)
voice_handler = VoiceHandler(GROQ_API_KEY)
file_handler = FileHandler()
channel_storage = ChannelStorage(STORAGE_CHANNEL_ID)
admin_panel = AdminPanel(ADMIN_ID, ADMIN_PASSWORD)
games = Games()

async def clear_chat(user_id, dept, chat_id, context):
    for msg_id in memory.get_bot_msgs(user_id, dept):
        try:
            await context.bot.delete_message(chat_id, msg_id)
        except: pass
    memory.clear_bot_msgs(user_id, dept)

async def show_menu(update, context, chat_id=None):
    keyboard = []
    row = []
    for key, dept in DEPARTMENTS.items():
        row.append(InlineKeyboardButton(dept["icon"] + " " + dept["name"], callback_data="dept_" + key))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    text = "🎓 *مُعلّم (Moallem) Pro v" + VERSION + "*\n\n"
    text += "مساعدك الأكاديمي الذكي في *" + UNIVERSITY + "* 🏛️\n\n"
    text += "✨ *الميزات:*\n"
    text += "• 📚 16 وكيل متخصص\n"
    text += "• 🧠 5 محركات AI مع Fallback\n"
    text += "• 🖼️ تحليل الصور + OCR\n"
    text += "• 🎤 تحويل الصوت\n"
    text += "• 📄 تلخيص PDF وWord\n"
    text += "• 📦 خزينة ملفات (قناة تليجرام)\n"
    text += "• 🏆 نظام نقاط ومستويات\n"
    text += "• 🔐 لوحة تحكم المدير\n\n"
    text += "👨‍💻 *المطور:* " + DEVELOPER_NAME + "\n"
    text += "📱 *التواصل:* " + DEVELOPER_PHONE + "\n\n"
    text += "🎯 *اختر قسمك:*"
    target = chat_id or (update.message.chat_id if update.message else update.callback_query.message.chat_id)
    if update.message:
        msg = await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        msg = await context.bot.send_message(target, text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    return msg.message_id

async def start_command(update, context):
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    memory.set_dept(user.id, "general")
    if str(user.id) != str(ADMIN_ID):
        try:
            await context.bot.send_message(ADMIN_ID, "🔔 *مستخدم جديد!*\n\n👤 " + user.first_name + " " + (user.last_name or "") + "\n🆔 `" + str(user.id) + "`\n📛 @" + (user.username or "لا يوجد"), parse_mode="Markdown")
        except: pass
    await show_menu(update, context)

async def help_command(update, context):
    text = "📋 *أوامر مُعلّم Pro:*\n\n"
    text += "/start - بدء البوت\n"
    text += "/help - المساعدة\n"
    text += "/my_stats - إحصائياتي\n"
    text += "/leaderboard - المتصدرين\n"
    text += "/feedback - شكوى أو اقتراح\n"
    text += "/library - استعراض الخزينة\n"
    text += "/search [كلمة] - البحث في الخزينة\n"
    text += "/upload - رفع ملف للقناة\n"
    text += "/summarize - تلخيص ملف PDF/Word\n\n"
    text += "📚 *أوامر الأقسام:*\n"
    text += "/agents - الوكلاء\n"
    text += "/about - عن البوت\n"
    text += "/stats - إحصائيات النظام\n"
    text += "/calc - آلة حاسبة\n"
    text += "/image - تصميم صورة\n"
    text += "/quiz - اختبار سريع\n"
    text += "/daily - تحدي اليوم\n\n"
    text += "🔐 *للمدير:*\n"
    text += "/admin - لوحة التحكم\n"
    text += "/broadcast - إشعار جماعي\n"
    text += "/ban - حظر مستخدم\n"
    text += "/unban - فك الحظر"
    await update.message.reply_text(text, parse_mode="Markdown")

async def my_stats_command(update, context):
    user = update.effective_user
    user_data = db.get_user(user.id)
    points = user_data[5] if user_data else 0
    level = user_data[6] if user_data else 1
    level_title = games.get_level_title(level)
    text = "📊 *إحصائياتك:*\n\n"
    text += "👤 الاسم: " + user.first_name + "\n"
    text += "🆔 ID: `" + str(user.id) + "`\n"
    text += "⭐ النقاط: " + str(points) + "\n"
    text += "🏆 المستوى: " + str(level) + " (" + level_title + ")\n\n"
    text += "💬 ابدأ محادثة في أي قسم لحفظ الإحصائيات."
    await update.message.reply_text(text, parse_mode="Markdown")

async def leaderboard_command(update, context):
    leaders = db.get_leaderboard(10)
    text = "🏆 *لوحة المتصدرين:*\n\n"
    for i, (first, last, username, points, level) in enumerate(leaders, 1):
        name = first or username or "مستخدم"
        title = games.get_level_title(level)
        text += str(i) + ". " + name + " — ⭐ " + str(points) + " (" + title + ")\n"
    if not leaders:
        text += "لا يوجد متصدرون بعد. شارك في الاختبارات!"
    await update.message.reply_text(text, parse_mode="Markdown")

async def feedback_command(update, context):
    if not context.args:
        await update.message.reply_text("💬 استخدم: /feedback [رسالتك]\nمثال: /feedback البوت رائع!", parse_mode="Markdown")
        return
    message = " ".join(context.args)
    db.save_feedback(update.effective_user.id, update.effective_user.username or update.effective_user.first_name, message)
    if str(ADMIN_ID) != str(update.effective_user.id):
        try:
            await context.bot.send_message(ADMIN_ID, "📩 *رسالة جديدة!*\n\n👤 " + update.effective_user.first_name + "\n💬 " + message, parse_mode="Markdown")
        except: pass
    await update.message.reply_text("✅ تم إرسال رسالتك! شكراً لك 💙", parse_mode="Markdown")

async def library_command(update, context):
    categories = {"📚 كتب": "books", "📝 ملفات PDF": "pdfs", "🎬 فيديوهات": "videos", "🎮 ألعاب": "games", "🔗 روابط": "links", "📖 ملخصات": "summaries"}
    keyboard = []
    row = []
    for name, cat in categories.items():
        row.append(InlineKeyboardButton(name, callback_data="lib_" + cat))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    await update.message.reply_text("📦 *خزينة مُعلّم:*\n\nاختر القسم:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def search_library_command(update, context):
    if not context.args:
        await update.message.reply_text("🔍 استخدم: /search [كلمة]\n\nمثال: /search فيزياء", parse_mode="Markdown")
        return
    query = " ".join(context.args)
    dept = memory.get_dept(update.effective_user.id)
    results = db.search_files(query, department=dept if dept != "general" else None)
    if not results:
        await update.message.reply_text("❌ لم يتم العثور على: " + query, parse_mode="Markdown")
        return
    text = "🔍 *نتائج البحث عن: " + query + "*\n\n"
    for i, (file_id, name, ftype, cat, caption, created) in enumerate(results[:10], 1):
        text += str(i) + ". *" + (name or "ملف") + "* (" + cat + ")\n💬 " + (caption[:50] if caption else "لا يوجد وصف") + "\n\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def agents_command(update, context):
    text = "🤖 *الوكلاء المتخصصون:*\n\n📚 16 وكيل — كل قسم وكيل خاص\n🧠 5 محركات AI\n🌍 إجابات عالمية دقيقة\n⚡ Fallback تلقائي"
    await update.message.reply_text(text, parse_mode="Markdown")

async def about_command(update, context):
    text = "🤖 *مُعلّم (Moallem) Pro v" + VERSION + "*\n\n"
    text += "🏛️ *" + UNIVERSITY + "*\n"
    text += "🎯 النظام العالمي متعدد الوكلاء\n\n"
    text += "👨‍💻 *المطور:* " + DEVELOPER_NAME + "\n"
    text += "📱 *التواصل:* " + DEVELOPER_PHONE + "\n"
    text += "🧠 *الذكاء:* Gemini + Groq + OpenRouter + Together + HuggingFace\n"
    text += "📦 *التخزين:* قناة تليجرام (مدى الحياة)\n\n"
    text += "*مشروع تخرج - 2026* 🎓"
    await update.message.reply_text(text, parse_mode="Markdown")

async def stats_command(update, context):
    stats = db.get_statistics()
    text = "📊 *إحصائيات النظام:*\n\n"
    text += "👥 إجمالي: " + str(stats["total_users"]) + "\n"
    text += "👤 جديد اليوم: " + str(stats["new_today"]) + "\n"
    text += "💬 محادثات: " + str(stats["total_messages"]) + "\n"
    text += "📅 نشطين اليوم: " + str(stats["active_today"]) + "\n"
    text += "🏆 أكثر قسم: " + str(stats["top_department"]) + "\n"
    text += "⭐ النقاط: " + str(stats["total_points"]) + "\n"
    text += "📦 الملفات: " + str(stats["total_files"])
    await update.message.reply_text(text, parse_mode="Markdown")

async def calc_command(update, context):
    try:
        if not context.args:
            await update.message.reply_text("🧮 استخدم: /calc 2+2\nأو: /calc sin(90*pi/180)", parse_mode="Markdown")
            return
        expr = " ".join(context.args)
        expr = expr.replace("^", "**").replace("×", "*").replace("÷", "/").replace("π", "pi")
        import math
        safe_dict = {"sin": math.sin, "cos": math.cos, "tan": math.tan, "log": math.log, "sqrt": math.sqrt, "pi": math.pi, "e": math.e, "abs": abs, "round": round, "pow": pow}
        result = eval(expr, {"__builtins__": {}}, safe_dict)
        await update.message.reply_text("🧮 *النتيجة:* `" + str(result) + "`", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ خطأ في الحساب. تحقق من الصيغة.")

async def image_command(update, context):
    if not context.args:
        await update.message.reply_text("🖼️ استخدم: /image طالب يدرس في مكتبة", parse_mode="Markdown")
        return
    prompt = " ".join(context.args)
    await update.message.chat.send_action(action="upload_photo")
    try:
        url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt) + "?width=1024&height=1024&nologo=true"
        path = "./generated_images/img_" + str(abs(hash(prompt)) % 10000000) + ".jpg"
        os.makedirs("./generated_images", exist_ok=True)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(path, "wb") as f:
                        f.write(await response.read())
                    await update.message.reply_photo(photo=open(path, "rb"), caption="🖼️ " + prompt)
                else:
                    await update.message.reply_text("❌ فشل: HTTP " + str(response.status))
    except Exception as e:
        logger.error("Image error: " + str(e))
        await update.message.reply_text("❌ فشل: " + str(e))

async def quiz_command(update, context):
    user = update.effective_user
    dept = memory.get_dept(user.id)
    if dept == "general":
        await update.message.reply_text("❌ اختر قسم أولاً عبر /start", parse_mode="Markdown")
        return
    q = games.get_quiz(dept)
    buttons = []
    for opt in q["options"]:
        buttons.append(InlineKeyboardButton(opt, callback_data="quiz_" + opt + "_" + q["a"]))
    keyboard = InlineKeyboardMarkup([buttons])
    await update.message.reply_text("🏆 *اختبار*\n\n❓ " + q["q"], parse_mode="Markdown", reply_markup=keyboard)

async def daily_command(update, context):
    user = update.effective_user
    dept = memory.get_dept(user.id)
    if dept == "general":
        await update.message.reply_text("❌ اختر قسم أولاً", parse_mode="Markdown")
        return
    q = games.get_quiz(dept)
    buttons = []
    for opt in q["options"]:
        buttons.append(InlineKeyboardButton(opt, callback_data="daily_" + opt + "_" + q["a"]))
    keyboard = InlineKeyboardMarkup([buttons])
    await update.message.reply_text("🎯 *تحدي اليوم*\n\n❓ " + q["q"] + "\n\n💡 +20 نقطة للإجابة الصحيحة!", parse_mode="Markdown", reply_markup=keyboard)

async def admin_command(update, context):
    user = update.effective_user
    if not admin_panel.is_admin(user.id):
        await update.message.reply_text("❌ غير مصرح.", parse_mode="Markdown")
        return
    await update.message.reply_text("🔐 *لوحة تحكم المدير:*\n\nاختر الأداة:", parse_mode="Markdown", reply_markup=admin_panel.get_menu())

async def broadcast_command(update, context):
    user = update.effective_user
    if not admin_panel.is_admin(user.id):
        await update.message.reply_text("❌ غير مصرح.", parse_mode="Markdown")
        return
    if not context.args:
        await update.message.reply_text("📢 استخدم: /broadcast [رسالة]", parse_mode="Markdown")
        return
    message = " ".join(context.args)
    users = db.get_all_users()
    sent = 0
    for u in users:
        try:
            await context.bot.send_message(u[0], "📢 *إشعار:*\n\n" + message, parse_mode="Markdown")
            sent += 1
        except: pass
    await update.message.reply_text("✅ تم الإرسال: " + str(sent) + " مستخدم", parse_mode="Markdown")

async def ban_command(update, context):
    user = update.effective_user
    if not admin_panel.is_admin(user.id):
        await update.message.reply_text("❌ غير مصرح.", parse_mode="Markdown")
        return
    if not context.args:
        await update.message.reply_text("🚫 استخدم: /ban [ID] [سبب]", parse_mode="Markdown")
        return
    target_id = int(context.args[0])
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else ""
    db.ban_user(target_id, reason)
    await update.message.reply_text("🚫 تم حظر المستخدم `" + str(target_id) + "`", parse_mode="Markdown")

async def unban_command(update, context):
    user = update.effective_user
    if not admin_panel.is_admin(user.id):
        await update.message.reply_text("❌ غير مصرح.", parse_mode="Markdown")
        return
    if not context.args:
        await update.message.reply_text("✅ استخدم: /unban [ID]", parse_mode="Markdown")
        return
    db.unban_user(int(context.args[0]))
    await update.message.reply_text("✅ تم فك الحظر.", parse_mode="Markdown")

async def summarize_command(update, context):
    await update.message.reply_text("📄 أرسل لي ملف PDF أو Word (DOCX) وسألخّصه لك.\n\nالحد الأقصى: 50MB", parse_mode="Markdown")

async def upload_command(update, context):
    await update.message.reply_text("📤 أرسل لي ملفاً وسأرفعه إلى قناة التخزين.\n\nالأنواع المدعومة: PDF, DOC, DOCX, PPT, MP4, JPG, PNG\nالحد الأقصى: 50MB", parse_mode="Markdown")

async def handle_message(update, context):
    user = update.effective_user
    message = update.message.text
    if db.is_banned(user.id):
        await update.message.reply_text("🚫 *تم حظرك.*", parse_mode="Markdown")
        return
    if message == "🔙 خروج من القسم":
        dept = memory.get_dept(user.id)
        await clear_chat(user.id, dept, update.message.chat_id, context)
        memory.set_dept(user.id, "general")
        memory.clear_context(user.id)
        await update.message.reply_text("⬅️ تم الخروج.", parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
        await show_menu(update, context)
        return
    if message == "📋 معلومات القسم":
        dept = memory.get_dept(user.id)
        dept_info = DEPARTMENTS.get(dept, {"name": "عام", "icon": "📚", "welcome": "مرحباً!"})
        text = dept_info["icon"] + " *" + dept_info["name"] + "*\n\n"
        text += dept_info["welcome"] + "\n🎯 خبير عالمي\n🌍 إجابات دقيقة\n💡 اكتب سؤالك"
        await update.message.reply_text(text, parse_mode="Markdown")
        return
    if message == "🤖 الوكيل المتخصص":
        dept = memory.get_dept(user.id)
        dept_info = DEPARTMENTS.get(dept, {"name": "عام", "icon": "📚"})
        text = dept_info["icon"] + " *الوكيل: " + dept_info["name"] + "*\n\n✅ جاهز\n💡 اكتب سؤالك"
        await update.message.reply_text(text, parse_mode="Markdown")
        return
    if message == "📤 رفع ملف":
        await update.message.reply_text("📤 أرسل الملف الآن...", parse_mode="Markdown")
        return
    logger.info("Message from " + str(user.id) + ": " + message)
    await update.message.chat.send_action(action="typing")
    dept = memory.get_dept(user.id)
    dept_name = DEPARTMENTS.get(dept, {}).get("name", "") if dept != "general" else ""
    context_history = memory.get_context(user.id)
    context_text = "\n".join([c["role"] + ": " + c["content"] for c in context_history[-5:]]) if context_history else ""
    answer = ai.ask(message, dept_name, context_text if context_text else None)
    db.save_conversation(user.id, message, answer, "ai", dept)
    memory.add_context(user.id, "user", message)
    memory.add_context(user.id, "assistant", answer)
    msg = await update.message.reply_text(answer, parse_mode="Markdown")
    if dept != "general":
        memory.add_bot_msg(user.id, dept, msg.message_id)

async def handle_photo(update, context):
    try:
        user = update.effective_user
        photo = update.message.photo[-1]
        await update.message.chat.send_action(action="typing")
        status = await update.message.reply_text("⏳ جاري تحليل الصورة...", parse_mode="Markdown")
        file = await photo.get_file()
        photo_path = "./temp_images/photo_" + photo.file_id + ".jpg"
        os.makedirs("./temp_images", exist_ok=True)
        await file.download_to_drive(photo_path)
        caption = update.message.caption or ""
        dept = memory.get_dept(user.id)
        dept_name = DEPARTMENTS.get(dept, {}).get("name", "") if dept != "general" else ""
        prompt = "السؤال: " + caption + "\n\nاشرح ما في هذه الصورة بالتفصيل واقرأ أي نص." if caption else "اشرح ما في هذه الصورة بالتفصيل واقرأ أي نص موجود."
        if dept_name:
            prompt = "أنت خبير في " + dept_name + ". " + prompt
        analysis = image_handler.analyze(photo_path, prompt)
        try:
            await status.delete()
        except: pass
        db.save_conversation(user.id, "[صورة] " + caption, analysis, "vision", dept)
        text = "📸 *تحليل الصورة:*\n\n" + analysis
        msg = await update.message.reply_text(text, parse_mode="Markdown")
        if dept != "general":
            memory.add_bot_msg(user.id, dept, msg.message_id)
    except Exception as e:
        logger.error("Photo error: " + str(e))
        await update.message.reply_text("❌ خطأ: " + str(e))

async def handle_voice(update, context):
    try:
        user = update.effective_user
        voice = update.message.voice
        file = await voice.get_file()
        await update.message.chat.send_action(action="typing")
        voice_path = "./temp_voice/voice_" + voice.file_id + ".ogg"
        os.makedirs("./temp_voice", exist_ok=True)
        await file.download_to_drive(voice_path)
        transcribed = voice_handler.transcribe(voice_path)
        if transcribed.startswith("❌"):
            await update.message.reply_text(transcribed, parse_mode="Markdown")
            return
        text = "🎤 *تم تحويل الصوت:*\n\n_" + transcribed + "_"
        msg = await update.message.reply_text(text, parse_mode="Markdown")
        dept = memory.get_dept(user.id)
        if dept != "general":
            memory.add_bot_msg(user.id, dept, msg.message_id)
        await update.message.chat.send_action(action="typing")
        dept_name = DEPARTMENTS.get(dept, {}).get("name", "") if dept != "general" else ""
        answer = ai.ask(transcribed, dept_name)
        msg2 = await update.message.reply_text(answer, parse_mode="Markdown")
        if dept != "general":
            memory.add_bot_msg(user.id, dept, msg2.message_id)
    except Exception as e:
        logger.error("Voice error: " + str(e))
        await update.message.reply_text("❌ خطأ في الصوت")

async def handle_document(update, context):
    try:
        user = update.effective_user
        doc = update.message.document
        file_name = doc.file_name or "unknown"
        ext = os.path.splitext(file_name)[1].lower()
        if memory.get_temp_file(user.id) == "awaiting_upload":
            await update.message.chat.send_action(action="typing")
            status = await update.message.reply_text("⏳ جاري رفع الملف إلى القناة...", parse_mode="Markdown")
            file = await doc.get_file()
            file_path = "./downloads/" + doc.file_id + "_" + file_name
            os.makedirs("./downloads", exist_ok=True)
            await file.download_to_drive(file_path)
            category = "documents"
            if ext in [".pdf"]: category = "pdfs"
            elif ext in [".doc", ".docx"]: category = "books"
            elif ext in [".ppt", ".pptx"]: category = "videos"
            elif ext in [".mp4", ".avi"]: category = "videos"
            elif ext in [".jpg", ".jpeg", ".png"]: category = "images"
            dept = memory.get_dept(user.id)
            file_id, result_msg = await channel_storage.store_file(context.bot, doc, file_name, ext.replace(".", ""), category, dept, update.message.caption, user.id)
            try:
                await status.delete()
            except: pass
            await update.message.reply_text(result_msg, parse_mode="Markdown")
            memory.set_temp_file(user.id, None)
            return
        if ext in [".pdf", ".doc", ".docx", ".txt"]:
            await update.message.chat.send_action(action="typing")
            status = await update.message.reply_text("⏳ جاري قراءة الملف...", parse_mode="Markdown")
            file = await doc.get_file()
            file_path = "./downloads/" + doc.file_id + "_" + file_name
            os.makedirs("./downloads", exist_ok=True)
            await file.download_to_drive(file_path)
            text = file_handler.extract_text(file_path)
            try:
                await status.delete()
            except: pass
            if text and not text.startswith("❌"):
                summary = file_handler.summarize(text, max_sentences=7)
                await update.message.reply_text("📄 *تلخيص الملف:* " + file_name + "\n\n" + summary, parse_mode="Markdown")
            else:
                await update.message.reply_text(text or "❌ لم أتمكن من قراءة الملف.", parse_mode="Markdown")
            return
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 رفع للقناة", callback_data="store_" + doc.file_id)],
            [InlineKeyboardButton("❌ إلغاء", callback_data="store_cancel")]
        ])
        await update.message.reply_text("📁 الملف: " + file_name + "\n\nماذا تريد أن تفعل؟", parse_mode="Markdown", reply_markup=keyboard)
    except Exception as e:
        logger.error("Document error: " + str(e))
        await update.message.reply_text("❌ خطأ: " + str(e))

async def handle_video(update, context):
    try:
        user = update.effective_user
        video = update.message.video
        if memory.get_temp_file(user.id) == "awaiting_upload":
            file_id, result_msg = await channel_storage.store_file(context.bot, video, video.file_name or "video.mp4", "mp4", "videos", memory.get_dept(user.id), update.message.caption, user.id)
            await update.message.reply_text(result_msg, parse_mode="Markdown")
            memory.set_temp_file(user.id, None)
            return
        await update.message.reply_text("🎬 أرسل /upload ثم أرسل الفيديو إذا تريد حفظه.", parse_mode="Markdown")
    except Exception as e:
        logger.error("Video error: " + str(e))

async def handle_callback(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("dept_"):
        dept = data.replace("dept_", "")
        dept_info = DEPARTMENTS.get(dept, {"name": "عام", "icon": "📚", "welcome": "مرحباً!"})
        user_id = query.from_user.id
        chat_id = query.message.chat_id
        db.update_user(user_id, department=dept)
        memory.set_dept(user_id, dept)
        memory.clear_context(user_id)
        try:
            await query.message.delete()
        except: pass
        keyboard = ReplyKeyboardMarkup([
            ["🔙 خروج من القسم"],
            ["📋 معلومات القسم"],
            ["🤖 الوكيل المتخصص"],
            ["📤 رفع ملف"]
        ], resize_keyboard=True, one_time_keyboard=False)
        welcome = "━━━━━━━━━━━━━━━━━━━━\n🚪 *دخول جديد إلى القسم*\n━━━━━━━━━━━━━━━━━━━━\n\n" + dept_info["icon"] + " *قسم: " + dept_info["name"] + "* ✅\n\n" + dept_info["welcome"] + "\n🔒 محادثة منعزلة.\n🌍 إجابات عالمية دقيقة."
        msg1 = await context.bot.send_message(chat_id, welcome, parse_mode="Markdown", reply_markup=keyboard)
        memory.add_bot_msg(user_id, dept, msg1.message_id)
        text = "🎯 أنت في: " + dept_info["icon"] + " *" + dept_info["name"] + "*\n\n💬 اكتب سؤالك."
        msg2 = await context.bot.send_message(chat_id, text, parse_mode="Markdown")
        memory.add_bot_msg(user_id, dept, msg2.message_id)
    elif data.startswith("quiz_"):
        parts = data.split("_")
        selected = parts[1]
        correct = parts[2]
        user_id = query.from_user.id
        if selected == correct:
            db.save_quiz_score(user_id, memory.get_dept(user_id), 10, 10)
            await query.edit_message_text("✅ *إجابة صحيحة!* 🎉\n\n+10 نقاط!", parse_mode="Markdown")
        else:
            await query.edit_message_text("❌ *خطأ!* الإجابة الصحيحة: " + correct, parse_mode="Markdown")
    elif data.startswith("daily_"):
        parts = data.split("_")
        selected = parts[1]
        correct = parts[2]
        user_id = query.from_user.id
        if selected == correct:
            db.save_quiz_score(user_id, memory.get_dept(user_id), 20, 20)
            await query.edit_message_text("🎯 *تحدي اليوم — إجابة صحيحة!* 🎉\n\n+20 نقطة!", parse_mode="Markdown")
        else:
            await query.edit_message_text("❌ *خطأ!* الإجابة: " + correct + "\n\nحاول غداً!", parse_mode="Markdown")
    elif data.startswith("lib_"):
        category = data.replace("lib_", "")
        dept = memory.get_dept(query.from_user.id)
        items = db.get_files_by_category(category, department=dept if dept != "general" else None)
        if not items:
            await query.edit_message_text("❌ لا توجد ملفات في هذا القسم.", parse_mode="Markdown")
            return
        text = "📦 *ملفات القسم:*\n\n"
        for i, (file_id, name, ftype, caption, created) in enumerate(items[:10], 1):
            text += str(i) + ". *" + (name or "ملف") + "*\n💬 " + (caption[:50] if caption else "لا يوجد وصف") + "\n\n"
        await query.edit_message_text(text, parse_mode="Markdown")
    elif data.startswith("store_"):
        if data == "store_cancel":
            await query.edit_message_text("❌ تم الإلغاء.", parse_mode="Markdown")
            return
        file_id = data.replace("store_", "")
        memory.set_temp_file(query.from_user.id, "awaiting_upload")
        await query.edit_message_text("📤 أرسل الملف الآن وسأرفعه للقناة.", parse_mode="Markdown")
    elif data.startswith("admin_"):
        user_id = query.from_user.id
        if not admin_panel.is_admin(user_id):
            await query.answer("❌ غير مصرح!", show_alert=True)
            return
        action = data.replace("admin_", "")
        if action == "stats":
            stats = db.get_statistics()
            await query.edit_message_text(admin_panel.get_stats_text(stats), parse_mode="Markdown")
        elif action == "users":
            users = db.get_all_users(20)
            text = "👥 *المستخدمون (" + str(len(users)) + "):*\n\n"
            for u in users:
                text += "• " + str(u[2]) + " " + (u[3] or "") + " — `" + str(u[0]) + "`\n"
            await query.edit_message_text(text, parse_mode="Markdown")
        elif action == "files":
            await query.edit_message_text("📦 *الملفات:*\n\nاستخدم /search للبحث.", parse_mode="Markdown")
        elif action == "broadcast":
            await query.edit_message_text("📢 استخدم: /broadcast [رسالة]", parse_mode="Markdown")
        elif action == "leaderboard":
            leaders = db.get_leaderboard(10)
            text = "🏆 *المتصدرون:*\n\n"
            for i, (first, last, username, points, level) in enumerate(leaders, 1):
                name = first or username or "مستخدم"
                text += str(i) + ". " + name + " — ⭐ " + str(points) + "\n"
            await query.edit_message_text(text, parse_mode="Markdown")
        elif action == "feedback":
            await query.edit_message_text("📩 استخدم /feedback لعرض التقييمات.", parse_mode="Markdown")
        elif action == "search":
            await query.edit_message_text("🔍 استخدم /search [كلمة] للبحث.", parse_mode="Markdown")
        else:
            await query.edit_message_text("🔧 *قيد التطوير.*", parse_mode="Markdown")

def main():
    logger.info("Starting " + PROJECT_NAME + " Pro v" + VERSION)
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("my_stats", my_stats_command))
    application.add_handler(CommandHandler("leaderboard", leaderboard_command))
    application.add_handler(CommandHandler("feedback", feedback_command))
    application.add_handler(CommandHandler("library", library_command))
    application.add_handler(CommandHandler("search", search_library_command))
    application.add_handler(CommandHandler("upload", upload_command))
    application.add_handler(CommandHandler("summarize", summarize_command))
    application.add_handler(CommandHandler("agents", agents_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("calc", calc_command))
    application.add_handler(CommandHandler("image", image_command))
    application.add_handler(CommandHandler("quiz", quiz_command))
    application.add_handler(CommandHandler("daily", daily_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    logger.info("All handlers added.")
    
    if WEBHOOK_URL:
        logger.info("Using webhook: " + WEBHOOK_URL)
        application.run_polling()
    else:
        logger.info("Using polling mode")
        application.run_polling()

if __name__ == "__main__":
    main()
