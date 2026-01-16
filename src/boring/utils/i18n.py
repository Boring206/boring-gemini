# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Internationalization (i18n) support for Boring CLI.
Supports: English, Chinese (Traditional), Spanish, Hindi, Arabic.
"""

import locale
from rich.console import Console


# Supported Languages
# Code -> Native Name
SUPPORTED_LANGUAGES = {
    "en": "English",
    "zh": "繁體中文 (Traditional Chinese)",
    "es": "Español (Spanish)",
    "hi": "हिन्दी (Hindi)",
    "ar": "العربية (Arabic)",
}

# Translation Dictionary
# key -> { lang_code -> translation }
_TRANSLATIONS = {
    # Meta / Wizard
    "select_language": {
        "en": "Select your language",
        "zh": "請選擇您的語言",
        "es": "Selecciona tu idioma",
        "hi": "अपनी भाषा चुनें",
        "ar": "اختر لغتك",
    },
    "welcome_wizard": {
        "en": "Welcome to Boring for Gemini Setup Wizard",
        "zh": "歡迎使用 Boring for Gemini 設定精靈",
        "es": "Bienvenido al Asistente de Configuración de Boring for Gemini",
        "hi": "Boring for Gemini सेटअप विजार्ड में आपका स्वागत है",
        "ar": "مرحبًا بكم في معالج إعداد Boring for Gemini",
    },
    "current_settings": {
        "en": "Current Settings",
        "zh": "目前設定",
        "es": "Configuración actual",
        "hi": "वर्तमान सेटिंग्स",
        "ar": "الإعدادات الحالية",
    },
    # Menus
    "menu_main_title": {
        "en": "Main Menu",
        "zh": "主選單",
        "es": "Menú Principal",
        "hi": "मुख्य मेनू",
        "ar": "القائمة الرئيسية",
    },
    "menu_configure_llm": {
        "en": "Configure LLM (Provider, Model)",
        "zh": "設定 LLM (供應商、模型)",
        "es": "Configurar LLM (Proveedor, Modelo)",
        "hi": "LLM कॉन्फ़िगर करें (प्रदाता, मॉडल)",
        "ar": "تكوين LLM (المزود، النموذج)",
    },
    "menu_configure_tools": {
        "en": "Configure Tool Profiles",
        "zh": "設定工具設定檔 (Profiles)",
        "es": "Configurar Perfiles de Herramientas",
        "hi": "टूल प्रोफ़ाइल कॉन्फ़िगर करें",
        "ar": "تكوين ملفات تعريف الأدوات",
    },
    "menu_configure_notifications": {
        "en": "Configure Notifications",
        "zh": "設定通知 (Slack, Discord)",
        "es": "Configurar Notificaciones",
        "hi": "सूचनाएं कॉन्फ़िगर करें",
        "ar": "تكوين الإشعارات",
    },
    "menu_configure_offline": {
        "en": "Configure Offline Mode / Local LLM",
        "zh": "設定離線模式 / 本地 LLM",
        "es": "Configurar Modo Offline / LLM Local",
        "hi": "ऑफ़लाइन मोड / स्थानीय LLM कॉन्फ़िगर करें",
        "ar": "تكوين الوضع غير المتصل / LLM المحلي",
    },
    "menu_configure_advanced": {
        "en": "Advanced Settings (Timeout, etc.)",
        "zh": "進階設定 (超時等)",
        "es": "Configuración Avanzada",
        "hi": "उन्नत सेटिंग्स",
        "ar": "إعدادات متقدمة",
    },
    "menu_install_mcp": {
        "en": "Install MCP Server to Editor",
        "zh": "安裝 MCP 伺服器到編輯器",
        "es": "Instalar Servidor MCP en el Editor",
        "hi": "संपादक में MCP सर्वर स्थापित करें",
        "ar": "تثبيت خادم MCP في المحرر",
    },
    "menu_return": {
        "en": "Return / Back",
        "zh": "返回",
        "es": "Volver",
        "hi": "वापस",
        "ar": "عودة",
    },
    "menu_exit": {
        "en": "Exit",
        "zh": "離開",
        "es": "Salir",
        "hi": "बाहर निकलें",
        "ar": "خروج",
    },
    # Prompts
    "prompt_google_api_key": {
        "en": "Enter your Google API Key (Enter to skip)",
        "zh": "請輸入您的 Google API Key (按 Enter 跳過)",
        "es": "Ingrese su clave API de Google (Enter para omitir)",
        "hi": "अपनी Google API कुंजी दर्ज करें (छोड़ने के लिए Enter दबाएं)",
        "ar": "أدخل مفتاح Google API الخاص بك (اضغط Enter للتخطي)",
    },
    "prompt_select_profile": {
        "en": "Select a Tool Profile",
        "zh": "選擇工具設定檔",
        "es": "Seleccione un Perfil de Herramienta",
        "hi": "एक टूल प्रोफ़ाइल चुनें",
        "ar": "حدد ملف تعريف الأداة",
    },
    "prompt_offline_enable": {
        "en": "Enable Offline Mode?",
        "zh": "啟用離線模式？",
        "es": "¿Habilitar Modo Offline?",
        "hi": "ऑफ़लाइन मोड सक्षम करें?",
        "ar": "تمكين الوضع غير المتصل؟",
    },
    "prompt_local_model": {
        "en": "Local Model Path/Name (GGUF)",
        "zh": "本地模型路徑或名稱 (GGUF)",
        "es": "Ruta/Nombre del Modelo Local (GGUF)",
        "hi": "स्थानीय मॉडल पथ / नाम (GGUF)",
        "ar": "مسار / اسم النموذج المحلي (GGUF)",
    },
    "prompt_timeout": {
        "en": "Loop Timeout (minutes)",
        "zh": "循環超時時間 (分鐘)",
        "es": "Tiempo de espera del bucle (minutos)",
        "hi": "लूप टाइमआउट (मिनट)",
        "ar": "مهلة الحلقة (دقائق)",
    },
    "prompt_discord": {
        "en": "Discord Webhook URL (Enter to skip)",
        "zh": "Discord Webhook 網址 (按 Enter 跳過)",
        "es": "URL de Webhook de Discord",
        "hi": "Discord Webhook URL",
        "ar": "Discord Webhook URL",
    },
    "prompt_save_confirm": {
        "en": "Save these settings?",
        "zh": "是否儲存這些設定？",
        "es": "¿Guardar esta configuración?",
        "hi": "क्या आप इन सेटिंग्स को सहेजना चाहते हैं?",
        "ar": "هل تريد حفظ هذه الإعدادات؟",
    },
    # Status
    "success_saved": {
        "en": "Settings saved successfully!",
        "zh": "設定已成功儲存！",
        "es": "¡Configuración guardada exitosamente!",
        "hi": "सेटिंग्स सफलतापूर्वक सहेजी गईं!",
        "ar": "تم حفظ الإعدادات بنجاح!",
    },
    "cancelled": {
        "en": "Cancelled.",
        "zh": "已取消。",
        "es": "Cancelado.",
        "hi": "रद्द किया गया।",
        "ar": "تم الإلغاء.",
    },
}



class LocalizedConsole(Console):
    """Console that supports localized output."""
    pass

class I18nManager:
    """Simple i18n manager for Boring CLI."""

    def __init__(self, language: str | None = None):
        self.language = language or "en"
        if not language:
            self._detect_language()

    def _detect_language(self):
        """Try to detect system language."""
        try:
            sys_lang, _ = locale.getdefaultlocale()
            if sys_lang:
                if sys_lang.startswith("zh"):
                    self.language = "zh"
                elif sys_lang.startswith("es"):
                    self.language = "es"
                elif sys_lang.startswith("hi"):
                    self.language = "hi"
                elif sys_lang.startswith("ar"):
                    self.language = "ar"
                else:
                    self.language = "en"
        except Exception:
            self.language = "en"

    def set_language(self, lang_code: str):
        """Set the active language."""
        if lang_code in SUPPORTED_LANGUAGES:
            self.language = lang_code

    def t(self, key: str, default: str | None = None, **kwargs) -> str:
        """Get translation for key."""
        translations = _TRANSLATIONS.get(key)
        if not translations:
            text = default or key
        else:
            text = translations.get(self.language, translations.get("en", default or key))
        
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

    def get_supported_languages(self) -> dict[str, str]:
        return SUPPORTED_LANGUAGES


# Global instance
i18n = I18nManager()
T = i18n.t

