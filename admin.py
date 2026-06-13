from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class AdminPanel:
    def __init__(self, admin_id, password):
        self.admin_id = int(admin_id)
        self.password = password

    def is_admin(self, user_id):
        return int(user_id) == self.admin_id

    def get_menu(self):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 إحصائيات", callback_data="admin_stats"), InlineKeyboardButton("👥 المستخدمون", callback_data="admin_users")],
            [InlineKeyboardButton("📦 الملفات", callback_data="admin_files"), InlineKeyboardButton("📢 إشعار", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🚫 المحظورون", callback_data="admin_banned"), InlineKeyboardButton("🏆 المتصدرون", callback_data="admin_leaderboard")],
            [InlineKeyboardButton("📩 التقييمات", callback_data="admin_feedback"), InlineKeyboardButton("🔍 بحث ملف", callback_data="admin_search")]
        ])

    def get_stats_text(self, stats):
        text = "📊 *إحصائيات النظام:*\n\n"
        text += "👥 إجمالي المستخدمين: " + str(stats["total_users"]) + "\n"
        text += "👤 جديد اليوم: " + str(stats["new_today"]) + "\n"
        text += "💬 إجمالي المحادثات: " + str(stats["total_messages"]) + "\n"
        text += "📅 نشطين اليوم: " + str(stats["active_today"]) + "\n"
        text += "🏆 أكثر قسم: " + str(stats["top_department"]) + "\n"
        text += "⭐ إجمالي النقاط: " + str(stats["total_points"]) + "\n"
        text += "📦 إجمالي الملفات: " + str(stats["total_files"])
        return text
