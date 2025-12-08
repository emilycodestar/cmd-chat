"""Translation manager for CMD CHAT."""
import json
import os
from pathlib import Path
from typing import Dict

# Translation files directory
TRANSLATIONS_DIR = Path(__file__).parent / "locales"

# Default language
DEFAULT_LANGUAGE = "en"

# Supported languages
SUPPORTED_LANGUAGES = [
    "en", "fr", "es", "zh", "ja", "de", "ru", 
    "et", "pt", "ko", "ca", "eu", "gl"
]


class TranslationManager:
    """Manages translations for the CLI interface."""
    
    def __init__(self, language: str | None = None):
        """Initialize translation manager with specified language."""
        self.language = language or os.getenv("CMD_CHAT_LANGUAGE", DEFAULT_LANGUAGE)
        if self.language not in SUPPORTED_LANGUAGES:
            self.language = DEFAULT_LANGUAGE
        self.translations: Dict[str, str] = {}
        self._load_translations()
    
    def _load_translations(self):
        """Load translations from JSON file."""
        translation_file = TRANSLATIONS_DIR / f"{self.language}.json"
        if translation_file.exists():
            try:
                with open(translation_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
            except Exception:
                # Fallback to English if loading fails
                self._load_fallback()
        else:
            self._load_fallback()
    
    def _load_fallback(self):
        """Load English as fallback."""
        if self.language != DEFAULT_LANGUAGE:
            translation_file = TRANSLATIONS_DIR / f"{DEFAULT_LANGUAGE}.json"
            if translation_file.exists():
                try:
                    with open(translation_file, 'r', encoding='utf-8') as f:
                        self.translations = json.load(f)
                except Exception:
                    self.translations = {}
    
    def get(self, key: str, default: str | None = None) -> str:
        """Get translation for a key."""
        return self.translations.get(key, default or key)
    
    def set_language(self, language: str):
        """Change the language."""
        if language in SUPPORTED_LANGUAGES:
            self.language = language
            self._load_translations()
    
    def get_language(self) -> str:
        """Get current language code."""
        return self.language


# Global translation manager instance
_translation_manager: TranslationManager | None = None


def get_translator() -> TranslationManager:
    """Get the global translation manager instance."""
    global _translation_manager
    if _translation_manager is None:
        _translation_manager = TranslationManager()
    return _translation_manager


def t(key: str, default: str | None = None) -> str:
    """Shortcut function to get translation."""
    return get_translator().get(key, default)

