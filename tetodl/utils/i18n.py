"""
Internationalization (i18n) utilities
"""
import os
import locale
import json
from typing import Dict, Any

_current_lang = 'id'
_translations: Dict[str, Any] = {}
_locales_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")


def load_language(lang_code: str = "id") -> bool:
    """Load language file"""
    global _translations, _current_lang
    
    lang_file = os.path.join(_locales_path, f"{lang_code}.json")
    
    try:
        with open(lang_file, "r", encoding="utf-8") as f:
            _translations = json.load(f)
        _current_lang = lang_code
        return True
    except FileNotFoundError:
        if lang_code != "id":
            return load_language('id')
        return False
    except Exception:
        return False


def get_text(key: str, **kwargs) -> str:
    """
    Get translated text by key with optional formatting
    
    Args:
        key: Translation key (dot notation supported, example: "menu.main.title")
        **kwargs: Format arguments for string formatting
    
    Returns:
        Translated text or key if not found
    """
    global _translations
    
    keys = key.split('.')
    value = _translations
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return key
    
    if isinstance(value, str) and kwargs:
        try:
            return value.format(**kwargs)
        except (KeyError, ValueError):
            return value
    
    return value if isinstance(value, str) else key


def get_available_languages() -> list:
    """
    Get list of available language codes based on json files in locales folder.
    Returns: ['en', 'id', 'es', ...]
    """
    try:
        files = os.listdir(_locales_path)
        return [f.replace('.json', '') for f in files if f.endswith('.json')]
    except Exception:
        return ["id", "en"]


def detect_system_language() -> str:
    """
    Detect system locale and return language code.
    """
    supported_langs = get_available_languages()
    detected_code = None

    try:
        env_vars = ['LC_ALL', 'LC_MESSAGES', 'LANG']
        for var in env_vars:
            val = os.environ.get(var)
            if val:
                detected_code = val.split('.')[0].split('_')[0].lower()
                break
        
        if not detected_code:
            loc_tuple = locale.getlocale()
            if loc_tuple and loc_tuple[0]:
                detected_code = loc_tuple[0].split('_')[0].lower()

    except Exception:
        pass

    # Validation
    if detected_code and detected_code in supported_langs:
        return detected_code
    
    return "en"

def get_language_display_name(code: str) -> str:
    """Get native display name for a language code"""
    names = {
        "id": "Bahasa Indonesia",
        "en": "English",
        "es": "Español",
        "pt": "Português",
        "ru": "Русский",
        "hi": "हिन्दी",
        "zh": "简体中文",
        "ja": "日本語",
        "de": "Deutsch"
    }
    return names.get(code, code.upper())

def get_current_language() -> str:
    """Get current language code"""
    return _current_lang


def set_language(lang_code: str) -> bool:
    """Set current language"""
    return load_language(lang_code)


_ = get_text
load_language(detect_system_language())