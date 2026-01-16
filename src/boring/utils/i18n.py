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
    # Hooks
    "hooks_status_not_repo": {
        "en": "Not a Git repository",
        "zh": "這不是一個 Git 儲存庫",
        "es": "No es un repositorio Git",
        "hi": "गिट रिपॉजिटरी नहीं है",
        "ar": "ليس مستودع Git",
    },
    "hooks_status_header": {
        "en": "Git Hooks Status:",
        "zh": "Git Hooks 狀態:",
        "es": "Estado de Git Hooks:",
        "hi": "गिट हुक्स स्थिति:",
        "ar": "حالة Git Hooks:",
    },
    "hooks_status_active": {
        "en": "[green]✓ {hook_name}: Active (Boring)[/green]",
        "zh": "[green]✓ {hook_name}: 已啟用 (Boring)[/green]",
        "es": "[green]✓ {hook_name}: Activo (Boring)[/green]",
        "hi": "[green]✓ {hook_name}: सक्रिय (Boring)[/green]",
        "ar": "[green]✓ {hook_name}: نشط (Boring)[/green]",
    },
    "hooks_status_custom": {
        "en": "[yellow]! {hook_name}: Active (Custom)[/yellow]",
        "zh": "[yellow]! {hook_name}: 已啟用 (自定義)[/yellow]",
        "es": "[yellow]! {hook_name}: Activo (Personalizado)[/yellow]",
        "hi": "[yellow]! {hook_name}: सक्रिय (कस्टम)[/yellow]",
        "ar": "[yellow]! {hook_name}: نشط (مخصص)[/yellow]",
    },
    "hooks_status_missing": {
        "en": "[dim]- {hook_name}: Not installed[/dim]",
        "zh": "[dim]- {hook_name}: 未安裝[/dim]",
        "es": "[dim]- {hook_name}: No instalado[/dim]",
        "hi": "[dim]- {hook_name}: स्थापित नहीं[/dim]",
        "ar": "[dim]- {hook_name}: غير مثبت[/dim]",
    },
    "hooks_install_success": {
        "en": "Hooks installed successfully!",
        "zh": "Hooks 安裝成功！",
        "es": "¡Ganchos instalados con éxito!",
        "hi": "हुक सफलतापूर्वक स्थापित!",
        "ar": "تم تثبيت الخطافات بنجاح!",
    },
    "hooks_install_message": {
        "en": "{message}",
        "zh": "{message}",
        "es": "{message}",
        "hi": "{message}",
        "ar": "{message}",
    },
    "hooks_install_hint": {
        "en": "Boring will now verify code quality before commits.",
        "zh": "Boring 現在會在提交代碼前檢查代碼品質。",
        "es": "Boring ahora verificará la calidad del código antes de los commits.",
        "hi": "Boring अब कमिट से पहले कोड गुणवत्ता को सत्यापित करेगा।",
        "ar": "سوف يتحقق Boring الآن من جودة الكود قبل الالتزامات.",
    },
    "hooks_install_failed": {
        "en": "Failed to install hooks: {message}",
        "zh": "安裝 Hooks 失敗: {message}",
        "es": "No se pudieron instalar los ganchos: {message}",
        "hi": "हुक स्थापित करने में विफल: {message}",
        "ar": "فشل تثبيت الخطافات: {message}",
    },
    "hooks_removed": {
        "en": "Hooks removed successfully.",
        "zh": "Hooks 已移除。",
        "es": "Ganchos eliminados con éxito.",
        "hi": "हुक सफलतापूर्वक हटा दिए गए।",
        "ar": "تمت إزالة الخطافات بنجاح.",
    },
    "hooks_uninstall_message": {
        "en": "{message}",
        "zh": "{message}",
        "es": "{message}",
        "hi": "{message}",
        "ar": "{message}",
    },
    "hooks_uninstall_failed": {
        "en": "Failed to remove hooks: {message}",
        "zh": "移除 Hooks 失敗: {message}",
        "es": "Error al eliminar los ganchos: {message}",
        "hi": "हुक हटाने में विफल: {message}",
        "ar": "فشل إزالة الخطافات: {message}",
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
        "zh": "已取消.",
        "es": "Cancelado.",
        "hi": "रद्द किया गया.",
        "ar": "تم الإلغاء.",
    },
    "status_header": {
        "en": "✨ Vibe Coder Status ✨",
        "zh": "✨ Vibe Coder 狀態 ✨",
        "es": "✨ Estado de Vibe Coder ✨",
        "hi": "✨ Vibe Coder स्थिति ✨",
        "ar": "✨ حالة Vibe Coder ✨",
    },
    "status_project": {
        "en": "Project: {project}",
        "zh": "專案: {project}",
        "es": "Proyecto: {project}",
        "hi": "परियोजना: {project}",
        "ar": "مشروع: {project}",
    },
    "status_unknown_project": {
        "en": "Unknown",
        "zh": "未知",
        "es": "Desconocido",
        "hi": "अज्ञात",
        "ar": "مجهول",
    },
    "status_total_loops": {
        "en": "Total Loops: {count}",
        "zh": "總循環數: {count}",
        "es": "Bucles totales: {count}",
        "hi": "कुल लूप: {count}",
        "ar": "مجموع الحلقات: {count}",
    },
    "status_success_failed": {
        "en": "Success: {success} / Failed: {failed}",
        "zh": "成功: {success} / 失敗: {failed}",
        "es": "Éxito: {success} / Fallido: {failed}",
        "hi": "सफलता: {success} / विफल: {failed}",
        "ar": "نجاح: {success} / فشل: {failed}",
    },
    "status_last_activity": {
        "en": "Last Activity: {last_activity}",
        "zh": "最後活動: {last_activity}",
        "es": "Última actividad: {last_activity}",
        "hi": "अंतिम गतिविधि: {last_activity}",
        "ar": "آخر نشاط: {last_activity}",
    },
    "status_never": {
        "en": "Never",
        "zh": "從未",
        "es": "Nunca",
        "hi": "कभी नहीँ",
        "ar": "أبدا",
    },
    "status_recent_loops": {
        "en": "\nRecent Loops:",
        "zh": "\n最近的循環:",
        "es": "\nBucles recientes:",
        "hi": "\nहाल के लूप:",
        "ar": "\nحلقات حديثة:",
    },
    "status_loop_entry": {
        "en": "{icon} Loop #{loop_id}: {status}",
        "zh": "{icon} 循環 #{loop_id}: {status}",
        "es": "{icon} Bucle #{loop_id}: {status}",
        "hi": "{icon} लूप #{loop_id}: {status}",
        "ar": "{icon} حلقة #{loop_id}: {status}",
    },
    # Clean / Maintenance
    "clean_migration_success": {
        "en": "Migrated {old_name} -> {new_sub}",
        "zh": "已遷移 {old_name} -> {new_sub}",
        "es": "Migrado {old_name} -> {new_sub}",
        "hi": "{old_name} -> {new_sub} माइग्रेट किया गया",
        "ar": "تم الترحيل {old_name} -> {new_sub}",
    },
    "clean_migration_failed": {
        "en": "Failed to migrate {old_name}: {error}",
        "zh": "遷移 {old_name} 失敗: {error}",
        "es": "Error al migrar {old_name}: {error}",
        "hi": "{old_name} को माइग्रेट करने में विफल: {error}",
        "ar": "فشل ترحيل {old_name}: {error}",
    },
    "clean_migration_summary": {
        "en": "Migrated {count} legacy files.",
        "zh": "已遷移 {count} 個舊檔案。",
        "es": "Se migraron {count} archivos heredados.",
        "hi": "{count} लीगेसी फ़ाइलें माइग्रेट की गईं।",
        "ar": "تم ترحيل {count} ملفات قديمة.",
    },
    "clean_migration_none": {
        "en": "No legacy state files found to migrate.",
        "zh": "未發現需遷移的舊狀態檔案。",
        "es": "No se encontraron archivos de estado heredados para migrar.",
        "hi": "माइग्रेट करने के लिए कोई लीगेसी स्थिति फ़ाइल नहीं मिली।",
        "ar": "لم يتم العثور على ملفات حالة قديمة للترحيل.",
    },
    "clean_no_targets": {
        "en": "No cleanup targets found.",
        "zh": "未發現需清理的目標。",
        "es": "No se encontraron objetivos de limpieza.",
        "hi": "कोई सफाई लक्ष्य नहीं मिला।",
        "ar": "لم يتم العثور على أهداف للتنظيف.",
    },
    "clean_targets_found": {
        "en": "Found {count} cleanup targets:",
        "zh": "發現 {count} 個需清理目標:",
        "es": "Se encontraron {count} objetivos de limpieza:",
        "hi": "{count} सफाई लक्ष्य मिले:",
        "ar": "تم العثور على {count} أهداف للتنظيف:",
    },
    "clean_target_item": {
        "en": "- {name}",
        "zh": "- {name}",
        "es": "- {name}",
        "hi": "- {name}",
        "ar": "- {name}",
    },
    "clean_aborted": {
        "en": "Cleanup aborted.",
        "zh": "清理已中止。",
        "es": "Limpieza abortada.",
        "hi": "सफाई रद्द की गई।",
        "ar": "تم إحباط التنظيف.",
    },
    "clean_delete_failed": {
        "en": "Failed to delete {name}: {error}",
        "zh": "刪除 {name} 失敗: {error}",
        "es": "Error al eliminar {name}: {error}",
        "hi": "{name} को हटाने में विफल: {error}",
        "ar": "فشل حذف {name}: {error}",
    },
    "clean_complete": {
        "en": "Cleanup complete. Removed {count} items.",
        "zh": "清理完成。移除了 {count} 個項目。",
        "es": "Limpieza completa. Se eliminaron {count} elementos.",
        "hi": "सफाई पूरी हुई। {count} आइटम हटाए गए।",
        "ar": "اكتمل التنظيف. تمت إزالة {count} عناصر.",
    },
    # Version Info
    "version_info_header": {
        "en": "Boring for Gemini v{version}",
        "zh": "Boring for Gemini v{version}",
        "es": "Boring for Gemini v{version}",
        "hi": "Boring for Gemini v{version}",
        "ar": "Boring for Gemini v{version}",
    },
    "version_info_model": {
        "en": "Default Model: {model}",
        "zh": "預設模型: {model}",
        "es": "Modelo predeterminado: {model}",
        "hi": "डिफ़ॉल्ट मॉडल: {model}",
        "ar": "النموذج الافتراضي: {model}",
    },
    "version_info_project": {
        "en": "Project Root: {project}",
        "zh": "專案根目錄: {project}",
        "es": "Raíz del proyecto: {project}",
        "hi": "प्रोजेक्ट रूट: {project}",
        "ar": "جذر المشروع: {project}",
    },
    "version_simple": {
        "en": "Boring for Gemini v{version}",
        "zh": "Boring for Gemini v{version}",
        "es": "Boring for Gemini v{version}",
        "hi": "Boring for Gemini v{version}",
        "ar": "Boring for Gemini v{version}",
    },
    "version_check_start": {
        "en": "Verifying version consistency...",
        "zh": "正在驗證版本一致性...",
        "es": "Verificando la coherencia de la versión...",
        "hi": "संस्करण स्थिरता सत्यापित की जा रही है...",
        "ar": "التحقق من اتساق الإصدار...",
    },
    "version_check_failed": {
        "en": "Version check failed (ImportError).",
        "zh": "版本檢查失敗 (ImportError)。",
        "es": "Verificación de versión fallida (ImportError).",
        "hi": "संस्करण जाँच विफल (ImportError).",
        "ar": "فشل التحقق من الإصدار (ImportError).",
    },
    # Auto Fix
    "auto_fix_success": {
        "en": "Optimized successfully ({iterations} iterations)",
        "zh": "優化成功 (經過 {iterations} 次迭代)",
        "es": "Optimizado con éxito ({iterations} iteraciones)",
        "hi": "सफलतापूर्वक अनुकूलित ({iterations} पुनरावृत्तियों)",
        "ar": "تم التحسين بنجاح ({iterations} تكرارات)",
    },
    "auto_fix_failed": {
        "en": "Could not fix: {message}",
        "zh": "無法修復: {message}",
        "es": "No se pudo arreglar: {message}",
        "hi": "ठीक नहीं किया जा सका: {message}",
        "ar": "تعذر الإصلاح: {message}",
    },
    "auto_fix_error": {
        "en": "Auto-fix error: {error}",
        "zh": "自動修復錯誤: {error}",
        "es": "Error de corrección automática: {error}",
        "hi": "स्वत: सुधार त्रुटि: {error}",
        "ar": "خطأ في الإصلاح التلقائي: {error}",
    },
    # Learn
    "learn_start": {
        "en": "Analyzing project history...",
        "zh": "正在分析專案歷史紀錄...",
        "es": "Analizando el historial del proyecto...",
        "hi": "प्रोजेक्ट इतिहास का विश्लेषण किया जा रहा है...",
        "ar": "جارٍ تحليل سجل المشروع...",
    },
    "learn_new_patterns": {
        "en": "Learned {count} new patterns.",
        "zh": "學習了 {count} 個新模式。",
        "es": "Se aprendieron {count} nuevos patrones.",
        "hi": "{count} नए पैटर्न सीखे।",
        "ar": "تم تعلم {count} أنماط جديدة.",
    },
    "learn_no_patterns": {
        "en": "No new patterns found.",
        "zh": "沒有發現新模式。",
        "es": "No se encontraron nuevos patrones.",
        "hi": "कोई नए पैटर्न नहीं मिले।",
        "ar": "لم يتم العثور على أنماط جديدة.",
    },
    "learn_total_patterns": {
        "en": "Total patterns in brain: {total}",
        "zh": "大腦中的總模式數: {total}",
        "es": "Patrones totales en el cerebro: {total}",
        "hi": "मस्तिष्क में कुल पैटर्न: {total}",
        "ar": "إجمالي الأنماط في الدماغ: {total}",
    },
    "learn_failed": {
        "en": "Learning failed: {error}",
        "zh": "學習失敗: {error}",
        "es": "El aprendizaje falló: {error}",
        "hi": "सीखना विफल रहा: {error}",
        "ar": "فشل التعلم: {error}",
    },
    # RAG
    "rag_index_start": {
        "en": "Indexing codebase at {root}...",
        "zh": "正在索引程式碼庫 ({root})...",
        "es": "Indexando base de código en {root}...",
        "hi": "{root} पर कोडबेस अनुक्रमण...",
        "ar": "فهرسة قاعدة التعليمات البرمجية في {root}...",
    },
    "rag_deps_missing": {
        "en": "RAG dependencies missing.",
        "zh": "缺少 RAG 依賴項。",
        "es": "Faltan dependencias de RAG.",
        "hi": "RAG निर्भरताएँ गायब हैं।",
        "ar": "تبعية RAG مفقودة.",
    },
    "rag_index_ready": {
        "en": "RAG Index {status}",
        "zh": "RAG 索引 {status}",
        "es": "Índice RAG {status}",
        "hi": "RAG इंडेक्स {status}",
        "ar": "مؤشر RAG {status}",
    },
    "rag_index_files": {
        "en": "- Files indexed: {count}",
        "zh": "- 已索引檔案: {count}",
        "es": "- Archivos indexados: {count}",
        "hi": "- अनुक्रमित फ़ाइलें: {count}",
        "ar": "- الملفات المفهرسة: {count}",
    },
    "rag_index_chunks": {
        "en": "- Total chunks: {count}",
        "zh": "- 總區塊數: {count}",
        "es": "- Fragmentos totales: {count}",
        "hi": "- कुल टुकड़े: {count}",
        "ar": "- إجمالي القطع: {count}",
    },
    # CLI Messages
    "cli_start_deprecated_redirect": {
        "en": "Warning: 'start' is deprecated. Redirecting to 'flow'...",
        "zh": "警告: 'start' 已棄用。正在重新導向至 'flow'...",
        "es": "Advertencia: 'start' está en desuso. Redirigiendo a 'flow'...",
        "hi": "चेतावनी: 'start' पदावनत है। 'flow' पर पुनर्निर्देशित किया जा रहा है...",
        "ar": "تحذير: 'start' مهمل. إعادة التوجيه إلى 'flow'...",
    },
    "cli_invalid_backend": {
        "en": "Invalid backend: {backend}",
        "zh": "無效的後端: {backend}",
        "es": "Backend no válido: {backend}",
        "hi": "अमान्य बैकएंड: {backend}",
        "ar": "الواجهة الخلفية غير صالحة: {backend}",
    },
    "cli_valid_backend_options": {
        "en": "Valid options: 'api' or 'cli'",
        "zh": "有效選項: 'api' 或 'cli'",
        "es": "Opciones válidas: 'api' o 'cli'",
        "hi": "मान्य विकल्प: 'api' या 'cli'",
        "ar": "خيارات صالحة: 'api' أو 'cli'",
    },
    "cli_privacy_mode": {
        "en": "Privacy Mode: Using local Gemini CLI",
        "zh": "隱私模式: 使用本地 Gemini CLI",
        "es": "Modo de privacidad: usando Gemini CLI local",
        "hi": "गोपनीयता मोड: स्थानीय मिथुन सीएलआई का उपयोग करना",
        "ar": "وضع الخصوصية: استخدام Gemini CLI المحلي",
    },
    "cli_privacy_mode_hint": {
        "en": "No data sent to Google API directly.",
        "zh": "資料不會直接傳送到 Google API。",
        "es": "No se envían datos a la API de Google directamente.",
        "hi": "Google API को सीधे कोई डेटा नहीं भेजा गया।",
        "ar": "لم يتم إرسال أي بيانات إلى Google API مباشرة.",
    },
    "cli_api_mode": {
        "en": "API Mode: Using Gemini SDK",
        "zh": "API 模式: 使用 Gemini SDK",
        "es": "Modo API: usando el SDK de Gemini",
        "hi": "एपीआई मोड: जेमिनी एसडीके का उपयोग करना",
        "ar": "وضع API: استخدام Gemini SDK",
    },
    "cli_self_heal_enabled_verbose": {
        "en": "Self-Healing Enabled",
        "zh": "已啟用自我修復",
        "es": "Autocuración habilitada",
        "hi": "स्व-उपचार सक्षम",
        "ar": "تم تمكين الشفاء الذاتي",
    },
    "cli_fatal_error": {
        "en": "Fatal Error: {error}",
        "zh": "致命錯誤: {error}",
        "es": "Error fatal: {error}",
        "hi": "घातक त्रुटि: {error}",
        "ar": "خطأ فادح: {error}",
    },
    "cli_debugger_heal_failed": {
        "en": "Debugger failed to heal",
        "zh": "偵錯程式修復失敗",
        "es": "El depurador no pudo sanar",
        "hi": "डीबगर ठीक करने में विफल रहा",
        "ar": "فشل المصحح في الشفاء",
    },
    "cli_self_heal_tip": {
        "en": "Tip: Try running with --self-heal to attempt auto-repair.",
        "zh": "提示: 嘗試使用 --self-heal 執行以嘗試自動修復。",
        "es": "Consejo: intente ejecutar con --self-heal para intentar la reparación automática.",
        "hi": "युक्ति: ऑटो-मरम्मत का प्रयास करने के लिए --self-heal के साथ चलाने का प्रयास करें।",
        "ar": "نصيحة: حاول التشغيل باستخدام --self-heal لمحاولة الإصلاح التلقائي.",
    },
    "cli_fix_think_help": {
        "en": "Enable System 2 Thinking (Reasoning Engine)",
        "zh": "啟用系統 2 思考 (推理引擎)",
        "es": "Habilitar el pensamiento del Sistema 2 (motor de razonamiento)",
        "hi": "सिस्टम 2 थिंकिंग सक्षम करें (तर्क इंजन)",
        "ar": "تمكين التفكير في النظام 2 (محرك الاستدلال)",
    },
    "cli_check_think_help": {
        "en": "Enable System 2 Thinking (Reasoning Engine)",
        "zh": "啟用系統 2 思考 (推理引擎)",
        "es": "Habilitar el pensamiento del Sistema 2 (motor de razonamiento)",
        "hi": "सिस्टम 2 थिंकिंग सक्षम करें (तर्क इंजन)",
        "ar": "تمكين التفكير في النظام 2 (محرك الاستدلال)",
    },
    "cli_save_think_help": {
        "en": "Enable System 2 Thinking (Reasoning Engine)",
        "zh": "啟用系統 2 思考 (推理引擎)",
        "es": "Habilitar el pensamiento del Sistema 2 (motor de razonamiento)",
        "hi": "सिस्टम 2 थिंकिंग सक्षम करें (तर्क इंजन)",
        "ar": "تمكين التفكير في النظام 2 (محرك الاستدلال)",
    },
    "cli_use_profile_help": {
        "en": "Profile name (e.g. 'standard', 'lite', 'full', 'custom')",
        "zh": "設定檔名稱 (例如 'standard', 'lite', 'full', 'custom')",
        "es": "Nombre del perfil (por ejemplo, 'estándar', 'lite', 'completo', 'personalizado')",
        "hi": "प्रोफ़ाइल नाम (जैसे 'मानक', 'लाइट', 'पूर्ण', 'कस्टम')",
        "ar": "اسم الملف الشخصي (مثل 'قياسي' ، 'لايت' ، 'كامل' ، 'مخصص')",
    },
    "profile_switch_success": {
        "en": "Switched to profile: {profile}",
        "zh": "已切換至設定檔: {profile}",
        "es": "Cambiado al perfil: {profile}",
        "hi": "प्रोफ़ाइल पर स्विच किया गया: {profile}",
        "ar": "تم التبديل إلى الملف الشخصي: {profile}",
    },
    "profile_switch_restart_hint": {
        "en": "Restarting loops...",
        "zh": "正在重新啟動循環...",
        "es": "Reiniciando bucles...",
        "hi": "लूप फिर से शुरू हो रहे हैं...",
        "ar": "إعادة تشغيل الحلقات...",
    },
    "profile_switch_failed": {
        "en": "Failed to switch profile.",
        "zh": "切換設定檔失敗。",
        "es": "Error al cambiar de perfil.",
        "hi": "प्रोफ़ाइल स्विच करने में विफल।",
        "ar": "فشل تبديل الملف الشخصي.",
    },
    "guide_prompt_ask_anything": {
        "en": "Ask anything (or type 'exit'):",
        "zh": "隨便問 (或輸入 'exit'):",
        "es": "Pregunta cualquier cosa (o escribe 'exit'):",
        "hi": "कुछ भी पूछें (या 'exit' टाइप करें):",
        "ar": "اسأل أي شيء (أو اكتب 'exit'):",
    },
    "cli_evolve_goal_help": {
        "en": "Goal to achieve",
        "zh": "要達成的目標",
        "es": "Meta a alcanzar",
        "hi": "प्राप्त करने का लक्ष्य",
        "ar": "الهدف المراد تحقيقه",
    },
    "cli_evolve_verify_help": {
        "en": "Verification command (default: pytest)",
        "zh": "驗證指令 (預設: pytest)",
        "es": "Comando de verificación (predeterminado: pytest)",
        "hi": "सत्यापन आदेश (डिफ़ॉल्ट: pytest)",
        "ar": "أمر التحقق (الافتراضي: pytest)",
    },
    "cli_evolve_steps_help": {
        "en": "Max evolution steps",
        "zh": "最大進化步驟數",
        "es": "Pasos máximos de evolución",
        "hi": "अधिकतम विकास के चरण",
        "ar": "أقصى خطوات التطور",
    },
    "cli_flow_auto_help": {
        "en": "Run automatically (no prompts)",
        "zh": "自動執行 (無提示)",
        "es": "Ejecutar automáticamente (sin indicaciones)",
        "hi": "स्वचालित रूप से चलाएं (कोई संकेत नहीं)",
        "ar": "تشغيل تلقائيًا (بدون مطالبات)",
    },
    "rag_index_functions": {
        "en": "- Functions: {count}",
        "zh": "- 函數: {count}",
        "es": "- Funciones: {count}",
        "hi": "- कार्य: {count}",
        "ar": "- الوظائف: {count}",
    },
    "rag_index_classes": {
        "en": "- Classes: {count}",
        "zh": "- 類別: {count}",
        "es": "- Clases: {count}",
        "hi": "- कक्षाएं: {count}",
        "ar": "- الفئات: {count}",
    },
    "rag_index_script_chunks": {
        "en": "- Script chunks: {count}",
        "zh": "- 腳本區塊: {count}",
        "es": "- Fragmentos de script: {count}",
        "hi": "- स्क्रिप्ट टुकड़े: {count}",
        "ar": "- قطع البرنامج النصي: {count}",
    },
    "rag_index_built": {
        "en": "RAG Index ready with {count} chunks",
        "zh": "RAG 索引就緒，共有 {count} 個區塊",
        "es": "Índice RAG listo con {count} fragmentos",
        "hi": "{count} टुकड़ों के साथ RAG इंडेक्स तैयार",
        "ar": "مؤشر RAG جاهز بـ {count} قطعة",
    },
    "rag_not_initialized": {
        "en": "RAG not initialized. Run `boring rag index` first.",
        "zh": "RAG 尚未初始化。請先執行 `boring rag index`。",
        "es": "RAG no inicializado. Ejecute `boring rag index` primero.",
        "hi": "RAG प्रारंभ नहीं हुआ। पहले `boring rag index` चलाएँ।",
        "ar": "RAG غير مهيأ. قم بتشغيل `boring rag index` أولاً.",
    },
    "rag_no_results": {
        "en": "No results found for '{query}'.",
        "zh": "找不到 '{query}' 的結果。",
        "es": "No se encontraron resultados para '{query}'.",
        "hi": "'{query}' के लिए कोई परिणाम नहीं मिला।",
        "ar": "لم يتم العثور على نتائج لـ '{query}'.",
    },
    "rag_results_header": {
        "en": "Search Results for '{query}':",
        "zh": "'{query}' 的搜尋結果:",
        "es": "Resultados de búsqueda para '{query}':",
        "hi": "'{query}' के लिए खोज परिणाम:",
        "ar": "نتائج البحث عن '{query}':",
    },
    "rag_result_item": {
        "en": "{index}. {name} (Score: {score:.2f}) - {file_path}",
        "zh": "{index}. {name} (分數: {score:.2f}) - {file_path}",
        "es": "{index}. {name} (Puntuación: {score:.2f}) - {file_path}",
        "hi": "{index}. {name} (स्कोर: {score:.2f}) - {file_path}",
        "ar": "{index}. {name} (النتيجة: {score:.2f}) - {file_path}",
    },
    "rag_result_snippet": {
        "en": "   Snippet: {snippet}...",
        "zh": "   摘要: {snippet}...",
        "es": "   Fragmento: {snippet}...",
        "hi": "   स्निपेट: {snippet}...",
        "ar": "   مقتطف: {snippet}...",
    },
    # Workspace
    "workspace_empty": {
        "en": "Workspace is empty.",
        "zh": "工作區是空的。",
        "es": "El espacio de trabajo está vacío.",
        "hi": "कार्यक्षेत्र खाली है।",
        "ar": "مساحة العمل فارغة.",
    },
    "workspace_list_header": {
        "en": "Workspace Projects ({count}):",
        "zh": "工作區專案 ({count}):",
        "es": "Proyectos del espacio de trabajo ({count}):",
        "hi": "कार्यक्षेत्र परियोजनाएं ({count}):",
        "ar": "مشاريع مساحة العمل ({count}):",
    },

    "workspace_list_item": {
        "en": "{marker} [{style}]{name}[/{style}] ({path})",
        "zh": "{marker} [{style}]{name}[/{style}] ({path})",
    },
    "workspace_list_description": {
        "en": "   {description}",
        "zh": "   {description}",
    },
    "workspace_add_success": {
        "en": "Project '{name}' added to workspace.",
        "zh": "專案 '{name}' 已加入工作區。",
    },
    "workspace_add_failed": {
        "en": "Failed to add project: {message}",
        "zh": "加入專案失敗: {message}",
    },
    "workspace_remove_success": {
        "en": "Project '{name}' removed from workspace.",
        "zh": "專案 '{name}' 已從工作區移除。",
    },
    "workspace_remove_failed": {
        "en": "Failed to remove project: {message}",
        "zh": "移除專案失敗: {message}",
    },
    "workspace_switch_success": {
        "en": "Switched to project '{name}'.",
        "zh": "已切換到專案 '{name}'。",
    },
    "workspace_switch_path": {
        "en": "Active Path: {path}",
        "zh": "目前路徑: {path}",
    },
    "workspace_switch_failed": {
        "en": "Failed to switch project: {message}",
        "zh": "切換專案失敗: {message}",
    },
    # Predict
    "predict_header": {
        "en": "🔮 Predictive Error Detection",
        "zh": "🔮 預測性錯誤偵測",
        "es": "🔮 Detección predictiva de errores",
        "hi": "🔮 भविष्य कहनेवाला त्रुटि का पता लगाना",
        "ar": "🔮 الكشف التنبؤي عن الأخطاء",
    },
    "predict_tui_predictions_title": {
        "en": "Predicted Risks",
        "zh": "預測風險",
        "es": "Riesgos previstos",
        "hi": "अनुमानित जोखिम",
        "ar": "المخاطر المتوقعة",
    },
    "predict_tui_col_rank": {
        "en": "Rank",
        "zh": "排名",
        "es": "Rango",
        "hi": "पद",
        "ar": "رتبة",
    },
    "predict_tui_col_type": {
        "en": "Type",
        "zh": "類型",
        "es": "Tipo",
        "hi": "प्रकार",
        "ar": "اكتب",
    },
    "predict_tui_col_confidence": {
        "en": "Confidence",
        "zh": "信心度",
        "es": "Confianza",
        "hi": "आत्मविश्वास",
        "ar": "ثقة",
    },
    "predict_tui_col_tip": {
        "en": "Prevention Tip",
        "zh": "預防建議",
        "es": "Consejo de prevención",
        "hi": "रोकथाम युक्ति",
        "ar": "نصيحة الوقاية",
    },
    "predict_tui_static_title": {
        "en": "Static Code Issues",
        "zh": "靜態程式碼問題",
        "es": "Problemas de código estático",
        "hi": "स्थिर कोड मुद्दे",
        "ar": "مشاكل التعليمات البرمجية الثابتة",
    },
    "predict_tui_col_severity": {
        "en": "Severity",
        "zh": "嚴重性",
        "es": "Gravedad",
        "hi": "गंभीरता",
        "ar": "الخطورة",
    },
    "predict_tui_col_category": {
        "en": "Category",
        "zh": "類別",
        "es": "Categoría",
        "hi": "श्रेणी",
        "ar": "فئة",
    },
    "predict_tui_col_line": {
        "en": "Line",
        "zh": "行號",
        "es": "Línea",
        "hi": "रेखा",
        "ar": "خط",
    },
    "predict_tui_col_message": {
        "en": "Message",
        "zh": "訊息",
        "es": "Mensaje",
        "hi": "संदेश",
        "ar": "رسالة",
    },
    "predict_tui_col_fix": {
        "en": "Suggested Fix",
        "zh": "建議修復",
        "es": "Solución sugerida",
        "hi": "सुझाया गया फिक्स",
        "ar": "الإصلاح المقترح",
    },
    "predict_result": {
        "en": "{result}",
        "zh": "{result}",
        "es": "{result}",
        "hi": "{result}",
        "ar": "{result}",
    },
    "predict_failed": {
        "en": "Prediction failed: {error}",
        "zh": "預測失敗: {error}",
        "es": "La predicción falló: {error}",
        "hi": "भविष्यवाणी विफल: {error}",
        "ar": "فشل التنبؤ: {error}",
    },
    # Bisect
    "bisect_header": {
        "en": "🔍 AI Git Bisect",
        "zh": "🔍 AI Git 二分搜尋",
        "es": "🔍 AI Git Bisect",
        "hi": "🔍 एआई गिट बाइसेक्ट",
        "ar": "🔍 منظمة العفو الدولية جيت بيسكت",
    },
    "bisect_tracing": {
        "en": "Tracing error: {error}",
        "zh": "正在追蹤錯誤: {error}",
        "es": "Error de rastreo: {error}",
        "hi": "ट्रेसिंग त्रुटि: {error}",
        "ar": "تتبع الخطأ: {error}",
    },
    "bisect_suspects_header": {
        "en": "Suspect Commits:",
        "zh": "可疑的提交:",
        "es": "Commits sospechosos:",
        "hi": "संदिग्ध कमिट:",
        "ar": "المشتبه بهم يرتكبون:",
    },
    "bisect_suspect_item": {
        "en": "[red]Authorization Score: {score:.2f}[/red] {sha} - {message}",
        "zh": "[red]權限分數: {score:.2f}[/red] {sha} - {message}",
        "es": "[red]Puntuación de autorización: {score:.2f}[/red] {sha} - {message}",
        "hi": "[red]प्राधिकरण स्कोर: {score:.2f}[/red] {sha} - {message}",
        "ar": "[red]درجة التفويض: {score:.2f}[/red] {sha} - {message}",
    },
    "bisect_no_suspects": {
        "en": "No clear suspects found.",
        "zh": "未發現明顯的可疑提交。",
        "es": "No se encontraron sospechosos claros.",
        "hi": "कोई स्पष्ट संदिग्ध नहीं मिला।",
        "ar": "لم يتم العثور على مشتبه بهم واضحين.",
    },
    "bisect_recommendation": {
        "en": "Recommendation: {recommendation}",
        "zh": "建議: {recommendation}",
        "es": "Recomendación: {recommendation}",
        "hi": "सिफारिश: {recommendation}",
        "ar": "التوصية: {recommendation}",
    },
    "bisect_failed": {
        "en": "Bisect failed: {error}",
        "zh": "二分搜尋失敗: {error}",
        "es": "Bisect falló: {error}",
        "hi": "द्विभाजन विफल: {error}",
        "ar": "فشل التنصيف: {error}",
    },
    # Diagnostic
    "diagnostic_header": {
        "en": "🩺 Deep Diagnostic",
        "zh": "🩺 深度診斷",
        "es": "🩺 Diagnóstico profundo",
        "hi": "🩺 गहरा निदान",
        "ar": "🩺 التشخيص العميق",
    },
    "diagnostic_comparing": {
        "en": "Comparing with: {commit}",
        "zh": "正在與 {commit} 進行比較",
        "es": "Comparando con: {commit}",
        "hi": "{commit} के साथ तुलना:",
        "ar": "مقارنة مع: {commit}",
    },
    "diagnostic_risk_score": {
        "en": "Risk Score: {score}",
        "zh": "風險分數: {score}",
        "es": "Puntuación de riesgo: {score}",
        "hi": "जोखिम स्कोर: {score}",
        "ar": "درجة المخاطر: {score}",
    },
    "diagnostic_issues_header": {
        "en": "Issues Found:",
        "zh": "發現的問題:",
        "es": "Problemas encontrados:",
        "hi": "मुद्दे मिले:",
        "ar": "المشاكل التي تم العثور عليها:",
    },
    "diagnostic_issue_item": {
        "en": "- {issue}",
        "zh": "- {issue}",
        "es": "- {issue}",
        "hi": "- {issue}",
        "ar": "- {issue}",
    },
    "diagnostic_patterns_header": {
        "en": "Related Patterns:",
        "zh": "相關模式:",
        "es": "Patrones relacionados:",
        "hi": "संबंधित पैटर्न:",
        "ar": "الأنماط ذات الصلة:",
    },
    "diagnostic_pattern_item": {
        "en": "- {pattern}",
        "zh": "- {pattern}",
        "es": "- {pattern}",
        "hi": "- {pattern}",
        "ar": "- {pattern}",
    },
    "diagnostic_failed": {
        "en": "Diagnostic failed: {error}",
        "zh": "診斷失敗: {error}",
        "es": "El diagnóstico falló: {error}",
        "hi": "निदान विफल: {error}",
        "ar": "فشل التشخيص: {error}",
    },
    # Verify
    "verify_start": {
        "en": "Verifying project at {level} level...",
        "zh": "正在執行 {level} 層級的專案驗證...",
        "es": "Verificando proyecto a nivel {level}...",
        "hi": "{level} स्तर पर परियोजना का सत्यापन...",
        "ar": "التحقق من المشروع على مستوى {level}...",
    },
    "verify_passed": {
        "en": "✨ Verification Passed!",
        "zh": "✨ 驗證通過！",
        "es": "✨ ¡Verificación aprobada!",
        "hi": "✨ सत्यापन उत्तीर्ण!",
        "ar": "✨ تم اجتياز التحقق!",
    },
    "verify_message": {
        "en": "{message}",
        "zh": "{message}",
        "es": "{message}",
        "hi": "{message}",
        "ar": "{message}",
    },
    "verify_failed": {
        "en": "❌ Verification Failed.",
        "zh": "❌ 驗證失敗。",
        "es": "❌ Verificación fallida.",
        "hi": "❌ सत्यापन विफल।",
        "ar": "❌ فشل التحقق.",
    },

    # Auto Fix (Target Not Found supplement)
    "auto_fix_target_not_found": {
        "en": "Error: Target '{target}' not found",
        "zh": "錯誤: 找不到目標 '{target}'",
        "es": "Error: objetivo '{target}' no encontrado",
        "hi": "त्रुटि: लक्ष्य '{target}' नहीं मिला",
        "ar": "خطأ: الهدف '{target}' غير موجود",
    },

    # Evaluate
    "evaluate_backend_cli": {
        "en": "Using Backend: Local CLI",
        "zh": "使用後端: 本地 CLI",
        "es": "Uso de backend: CLI local",
        "hi": "बैकएंड का उपयोग करना: स्थानीय CLI",
        "ar": "باستخدام الخلفية: CLI المحلي",
    },
    "evaluate_backend_api": {
        "en": "Using Backend: Gemini API SDK",
        "zh": "使用後端: Gemini API SDK",
        "es": "Uso de backend: Gemini API SDK",
        "hi": "बैकएंड का उपयोग करना: Gemini API SDK",
        "ar": "باستخدام الخلفية: Gemini API SDK",
    },
    "evaluate_api_key_missing": {
        "en": "Error: API Key not found. Please set GOOGLE_API_KEY.",
        "zh": "錯誤: 找不到 API Key。請設定 GOOGLE_API_KEY。",
        "es": "Error: no se encontró la clave API. Configure GOOGLE_API_KEY.",
        "hi": "त्रुटि: एपीआई कुंजी नहीं मिली। कृपया GOOGLE_API_KEY सेट करें।",
        "ar": "خطأ: مفتاح API غير موجود. يرجى تعيين GOOGLE_API_KEY.",
    },
    "evaluate_pairwise_requires_two": {
        "en": "Error: PAIRWISE evaluation requires exactly 2 files.",
        "zh": "錯誤: PAIRWISE 評估需要正好 2 個檔案。",
        "es": "Error: la evaluación PAIRWISE requiere exactamente 2 archivos.",
        "hi": "त्रुटि: PAIRWISE मूल्यांकन के लिए ठीक 2 फ़ाइलों की आवश्यकता है।",
        "ar": "خطأ: يتطلب تقييم PAIRWISE ملفين بالضبط.",
    },
    "evaluate_files_not_found": {
        "en": "Error: One or both input files not found.",
        "zh": "錯誤: 找不到一個或兩個輸入檔案。",
        "es": "Error: no se encontraron uno o ambos archivos de entrada.",
        "hi": "त्रुटि: एक या दोनों इनपुट फ़ाइलें नहीं मिलीं।",
        "ar": "خطأ: لم يتم العثور على أحد ملفي الإدخال أو كليهما.",
    },
    "evaluate_pairwise_comparing": {
        "en": "Comparing: {file_a} vs {file_b}",
        "zh": "正在比較: {file_a} vs {file_b}",
        "es": "Comparando: {file_a} vs {file_b}",
        "hi": "तुलना: {file_a} बनाम {file_b}",
        "ar": "المقارنة: {file_a} مقابل {file_b}",
    },
    "evaluate_pairwise_winner": {
        "en": "[{color}]Winner: {winner} (Confidence: {confidence:.2f})[/{color}]",
        "zh": "[{color}]優勝者: {winner} (信心度: {confidence:.2f})[/{color}]",
        "es": "[{color}]Ganador: {winner} (Confianza: {confidence:.2f})[/{color}]",
        "hi": "[{color}]विजेता: {winner} (आत्मविश्वास: {confidence:.2f})[/{color}]",
        "ar": "[{color}]الفائز: {winner} (الثقة: {confidence:.2f})[/{color}]",
    },
    "evaluate_pairwise_reasoning": {
        "en": "Reasoning: {reasoning}",
        "zh": "理由: {reasoning}",
        "es": "Razonamiento: {reasoning}",
        "hi": "तर्क: {reasoning}",
        "ar": "الاستدلال: {reasoning}",
    },
    "evaluate_target_not_found": {
        "en": "Error: Target '{target}' not found",
        "zh": "錯誤: 找不到目標 '{target}'",
        "es": "Error: objetivo '{target}' no encontrado",
        "hi": "त्रुटि: लक्ष्य '{target}' नहीं मिला",
        "ar": "خطأ: الهدف '{target}' غير موجود",
    },
    "evaluate_target_start": {
        "en": "Evaluating {target}...",
        "zh": "正在評估 {target}...",
        "es": "Evaluando {target}...",
        "hi": "{target} का मूल्यांकन किया जा रहा है...",
        "ar": "تقييم {target}...",
    },
    "evaluate_breakdown_header": {
        "en": "\nScore Breakdown:",
        "zh": "\n分數細項:",
        "es": "\nDesglose de puntuación:",
        "hi": "\nस्कोर का विश्लेषण:",
        "ar": "\nتوزيع النتيجة:",
    },
    "evaluate_breakdown_item": {
        "en": "- {dimension}: [{color}]{score}/5[/{color}] - {comment}",
        "zh": "- {dimension}: [{color}]{score}/5[/{color}] - {comment}",
        "es": "- {dimension}: [{color}]{score}/5[/{color}] - {comment}",
        "hi": "- {dimension}: [{color}]{score}/5[/{color}] - {comment}",
        "ar": "- {dimension}: [{color}]{score}/5[/{color}] - {comment}",
    },
    "evaluate_overall_score": {
        "en": "\n{emoji} [bold]Overall Score: {score}/5[/bold]",
        "zh": "\n{emoji} [bold]總分: {score}/5[/bold]",
        "es": "\n{emoji} [bold]Puntuación general: {score}/5[/bold]",
        "hi": "\n{emoji} [bold]कुल स्कोर: {score}/5[/bold]",
        "ar": "\n{emoji} [bold]النتيجة الإجمالية: {score}/5[/bold]",
    },
    "evaluate_summary": {
        "en": "[italic]{summary}[/italic]",
        "zh": "[italic]{summary}[/italic]",
        "es": "[italic]{summary}[/italic]",
        "hi": "[italic]{summary}[/italic]",
        "ar": "[italic]{summary}[/italic]",
    },
    "evaluate_suggestions_header": {
        "en": "\n[bold cyan]Suggestions:[/bold cyan]",
        "zh": "\n[bold cyan]建議:[/bold cyan]",
        "es": "\n[bold cyan]Sugerencias:[/bold cyan]",
        "hi": "\n[bold cyan]सुझाव:[/bold cyan]",
        "ar": "\n[bold cyan]اقتراحات:[/bold cyan]",
    },
    "evaluate_suggestion_item": {
        "en": "- {suggestion}",
        "zh": "- {suggestion}",
        "es": "- {suggestion}",
        "hi": "- {suggestion}",
        "ar": "- {suggestion}",
    },
    "evaluate_failed": {
        "en": "Evaluation failed: {error}",
        "zh": "評估失敗: {error}",
        "es": "Evaluación fallida: {error}",
        "hi": "मूल्यांकन विफल: {error}",
        "ar": "فشل التقييم: {error}",
    },
    # Dashboard
    "dashboard_deps_missing": {
        "en": "[bold red]Error: Dashboard requirements not found.[/bold red]",
        "zh": "[bold red]錯誤: 找不到儀表板需求。[/bold red]",
        "es": "[bold red]Error: no se encontraron los requisitos del panel.[/bold red]",
        "hi": "[bold red]त्रुटि: डैशबोर्ड आवश्यकताएँ नहीं मिलीं।[/bold red]",
        "ar": "[bold red]خطأ: لم يتم العثور على متطلبات لوحة المعلومات.[/bold red]",
    },
    "dashboard_deps_hint": {
        "en": "Please install the GUI optional dependencies:",
        "zh": "請安裝 GUI 選用依賴項:",
        "es": "Instale las dependencias opcionales de GUI:",
        "hi": "कृपया GUI वैकल्पिक निर्भरताएँ स्थापित करें:",
        "ar": "يرجى تثبيت التبعيات الاختيارية لواجهة المستخدم الرسومية:",
    },
    "dashboard_deps_install": {
        "en": '  [bold]pip install "boring-aicoding[gui]"[/bold]\n',
        "zh": '  [bold]pip install "boring-aicoding[gui]"[/bold]\n',
        "es": '  [bold]pip install "boring-aicoding[gui]"[/bold]\n',
        "hi": '  [bold]pip install "boring-aicoding[gui]"[/bold]\n',
        "ar": '  [bold]pip install "boring-aicoding[gui]"[/bold]\n',
    },
    "dashboard_launching": {
        "en": "[bold green]Launching Dashboard...[/bold green]",
        "zh": "[bold green]正在啟動儀表板...[/bold green]",
        "es": "[bold green]Iniciando panel...[/bold green]",
        "hi": "[bold green]डैशबोर्ड लॉन्च किया जा रहा है...[/bold green]",
        "ar": "[bold green]إطلاق لوحة المعلومات...[/bold green]",
    },
    "dashboard_stop_hint": {
        "en": "Press Ctrl+C to stop.",
        "zh": "按 Ctrl+C 停止。",
        "es": "Presione Ctrl+C para detener.",
        "hi": "रोकने के लिए Ctrl+C दबाएं।",
        "ar": "اضغط على Ctrl+C للتوقف.",
    },
    "dashboard_stopped": {
        "en": "\nDashboard stopped.",
        "zh": "\n儀表板已停止。",
        "es": "\nTablero detenido.",
        "hi": "\nडैशबोर्ड रुक गया।",
        "ar": "\nتوقفت لوحة القيادة.",
    },
    "dashboard_launch_failed": {
        "en": "Failed to launch dashboard: {error}",
        "zh": "啟動儀表板失敗: {error}",
        "es": "Error al iniciar el panel: {error}",
        "hi": "डैशबोर्ड लॉन्च करने में विफल: {error}",
        "ar": "فشل تشغيل لوحة المعلومات: {error}",
    },
    # Workflow
    "workflow_list_header": {
        "en": "Local Workflows:",
        "zh": "本地工作流程:",
        "es": "Flujos de trabajo locales:",
        "hi": "स्थानीय कार्यप्रवाह:",
        "ar": "سير العمل المحلي:",
    },
    "workflow_list_empty": {
        "en": "No workflows found.",
        "zh": "找不到工作流程。",
        "es": "No se encontraron flujos de trabajo.",
        "hi": "कार्यप्रवाह नहीं मिला।",
        "ar": "لم يتم العثور على مهام سير عمل.",
    },
    "workflow_list_item": {
        "en": "- {name}",
        "zh": "- {name}",
        "es": "- {name}",
        "hi": "- {name}",
        "ar": "- {name}",
    },
    "workflow_export_success": {
        "en": "Workflow exported to '{path}'",
        "zh": "工作流程已匯出至 '{path}'",
        "es": "Flujo de trabajo exportado a '{path}'",
        "hi": "कार्यप्रवाह '{path}' पर निर्यात किया गया",
        "ar": "تم تصدير سير العمل إلى '{path}'",
    },
    "workflow_export_failed": {
        "en": "Export failed: {message}",
        "zh": "匯出失敗: {message}",
        "es": "Error de exportación: {message}",
        "hi": "निर्यात विफल: {message}",
        "ar": "فشل التصدير: {message}",
    },
    "workflow_publish_token_missing": {
        "en": "Error: GitHub Token not found.",
        "zh": "錯誤: 找不到 GitHub Token。",
        "es": "Error: no se encontró el token de GitHub.",
        "hi": "त्रुटि: गिटहब टोकन नहीं मिला।",
        "ar": "خطأ: رمز GitHub المميز غير موجود.",
    },
    "workflow_publish_token_hint": {
        "en": "Please provide --token or set GITHUB_TOKEN env var.",
        "zh": "請提供 --token 或設定 GITHUB_TOKEN 環境變數。",
        "es": "Proporcione --token o configure la variable de entorno GITHUB_TOKEN.",
        "hi": "कृपया --token प्रदान करें या GITHUB_TOKEN env var सेट करें।",
        "ar": "يرجى توفير --token أو تعيين متغير env GITHUB_TOKEN.",
    },
    "workflow_publish_token_url": {
        "en": "Get one at: https://github.com/settings/tokens (Scope: gist)",
        "zh": "取得 Token: https://github.com/settings/tokens (權限: gist)",
        "es": "Obtenga uno en: https://github.com/settings/tokens (Alcance: esencia)",
        "hi": "एक यहाँ प्राप्त करें: https://github.com/settings/tokens (स्कोप: सारांश)",
        "ar": "احصل على واحدة على: https://github.com/settings/tokens (النطاق: جوهر)",
    },
    "workflow_publish_success": {
        "en": "Workflow published successfully!",
        "zh": "工作流程發佈成功！",
        "es": "¡Flujo de trabajo publicado con éxito!",
        "hi": "कार्यप्रवाह सफलतापूर्वक प्रकाशित!",
        "ar": "تم نشر سير العمل بنجاح!",
    },
    "workflow_publish_success_message": {
        "en": "{message}",
        "zh": "{message}",
        "es": "{message}",
        "hi": "{message}",
        "ar": "{message}",
    },
    "workflow_publish_failed": {
        "en": "Publish failed: {message}",
        "zh": "發佈失敗: {message}",
        "es": "Publicación fallida: {message}",
        "hi": "प्रकाशन विफल: {message}",
        "ar": "فشل النشر: {message}",
    },
    "workflow_install_success": {
        "en": "Workflow installed successfully! {message}",
        "zh": "工作流程安裝成功！ {message}",
        "es": "¡Flujo de trabajo instalado correctamente! {message}",
        "hi": "कार्यप्रवाह सफलतापूर्वक स्थापित! {message}",
        "ar": "تم تثبيت سير العمل بنجاح! {message}",
    },
    "workflow_install_failed": {
        "en": "Installation failed: {message}",
        "zh": "安裝失敗: {message}",
        "es": "Instalación fallida: {message}",
        "hi": "स्थापना विफल: {message}",
        "ar": "فشل التثبيت: {message}",
    },

    # Tutorial
    "tutorial_note_created": {
        "en": "[green]Learning note created successfully![/green]",
        "zh": "[green]學習筆記建立成功！[/green]",
        "es": "[green]¡Nota de aprendizaje creada con éxito![/green]",
        "hi": "[green]सीखने का नोट सफलतापूर्वक बनाया गया![/green]",
        "ar": "[green]تم إنشاء مذكرة تعليمية بنجاح![/green]",
    },
    "tutorial_note_path": {
        "en": "Path: {path}",
        "zh": "路徑: {path}",
        "es": "Ruta: {path}",
        "hi": "पथ: {path}",
        "ar": "المسار: {path}",
    },
    "tutorial_note_hint": {
        "en": "Review it to solidify your understanding.",
        "zh": "請檢閱它以鞏固您的理解。",
        "es": "Revísalo para solidificar tu comprensión.",
        "hi": "अपनी समझ को मजबूत करने के लिए इसकी समीक्षा करें।",
        "ar": "قم بمراجعتها لترسيخ فهمك.",
    },
    # LSP
    "lsp_starting": {
        "en": "Starting Boring LSP Server on {host}:{port}...",
        "zh": "正在 {host}:{port} 啟動 Boring LSP 伺服器...",
        "es": "Iniciando el servidor LSP aburrido en {host}:{port}...",
        "hi": "{host}:{port} पर बोरिंग LSP सर्वर शुरू हो रहा है...",
        "ar": "بدء خادم LSP الممل على {host}:{port}...",
    },
    # Suggestion
    "suggestion_did_you_mean": {
        "en": "Did you mean '{correction}'?",
        "zh": "您是指 '{correction}' 嗎？",
        "es": "¿Quisiste decir '{correction}'?",
        "hi": "क्या आपका मतलब '{correction}' था?",
        "ar": "هل تقصد '{correction}'؟",
    },
    "suggestion_no_match": {
        "en": "No suggestion found for '{typo}'",
        "zh": "找不到 '{typo}' 的建議",
        "es": "No se encontraron sugerencias para '{typo}'",
        "hi": "'{typo}' के लिए कोई सुझाव नहीं मिला",
        "ar": "لم يتم العثور على اقتراح لـ '{typo}'",
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
set_language = i18n.set_language
