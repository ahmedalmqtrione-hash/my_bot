import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8724867533:AAE4mVFqmv8CA_FhVaxkdgUvnx4_Nuhk1uI")
PROJECT_NAME = "Moallem Pro"
VERSION = "4.0"
UNIVERSITY = "جامعة تعز - كلية التربية"
DEVELOPER_NAME = "أحمد حمدي أحمد عثمان المقطري"
DEVELOPER_PHONE = "771267564 / 738805009"
ADMIN_ID = int(os.getenv("ADMIN_ID", "7890430043"))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "moallem2026")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")

STORAGE_CHANNEL_ID = os.getenv("STORAGE_CHANNEL_ID", "")
STORAGE_CHANNEL_LINK = os.getenv("STORAGE_CHANNEL_LINK", "https://t.me/+W9mV37pao3cyZmNk")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
PORT = int(os.getenv("PORT", "8080"))

DEPARTMENTS = {
    'psychology': {'name': 'علم النفس التربوي', 'icon': '🧠', 'welcome': 'مرحباً بك في عالم النفس!'},
    'curriculum': {'name': 'المناهج وطرائق التدريس', 'icon': '📚', 'welcome': 'نحن هنا لنطوّر التعليم!'},
    'special_ed': {'name': 'التربية الخاصة', 'icon': '♿', 'welcome': 'كل طفل له حق التعلم!'},
    'childhood': {'name': 'رياض الأطفال', 'icon': '👶', 'welcome': 'مستقبلنا يبدأ هنا!'},
    'technology': {'name': 'تكنولوجيا التعليم', 'icon': '💻', 'welcome': 'التكنولوجيا في خدمة التعليم!'},
    'counseling': {'name': 'الإرشاد النفسي', 'icon': '💙', 'welcome': 'نحن هنا لنستمع ونساعد!'},
    'arabic': {'name': 'اللغة العربية', 'icon': '📖', 'welcome': 'لغة الضاد عزة وإبداع!'},
    'english': {'name': 'اللغة الإنجليزية', 'icon': '🇬🇧', 'welcome': 'English is the key to the world!'},
    'math': {'name': 'الرياضيات', 'icon': '🔢', 'welcome': 'الأرقام لغة الكون!'},
    'physics': {'name': 'الفيزياء', 'icon': '⚛️', 'welcome': 'اكتشف قوانين الطبيعة!'},
    'biology': {'name': 'الأحياء', 'icon': '🧬', 'welcome': 'استكشف عجائب الحياة!'},
    'chemistry': {'name': 'الكيمياء', 'icon': '⚗️', 'welcome': 'الكيمياء هي كل شيء!'},
    'history': {'name': 'التاريخ', 'icon': '🏛️', 'welcome': 'من لا ماضي له لا حاضر له!'},
    'geography': {'name': 'الجغرافيا', 'icon': '🌍', 'welcome': 'العالم بين يديك!'},
    'islamic': {'name': 'الدراسات الإسلامية', 'icon': '🕌', 'welcome': 'نور الهداية!'},
    'science': {'name': 'الدراسات العليا', 'icon': '🔬', 'welcome': 'البحث العلمي ركيزة التقدم!'},
}
