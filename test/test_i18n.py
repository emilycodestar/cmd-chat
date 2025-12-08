"""Tests for i18n translation system."""
import os
import json
from pathlib import Path
from cmd_chat.client.i18n.translations import TranslationManager, SUPPORTED_LANGUAGES

def test_translation_manager():
    """Test translation manager functionality."""
    print("\n" + "="*60)
    print("  I18N TRANSLATION SYSTEM TEST")
    print("="*60)
    
    # Test default language
    tm = TranslationManager()
    assert tm.get_language() == "en", "Default language should be English"
    print("✅ Default language: English")
    
    # Test all supported languages
    print("\nTesting all supported languages:")
    for lang in SUPPORTED_LANGUAGES:
        tm.set_language(lang)
        assert tm.get_language() == lang, f"Language should be {lang}"
        
        # Check that translations file exists
        translation_file = Path(__file__).parent.parent / "cmd_chat" / "client" / "i18n" / "locales" / f"{lang}.json"
        assert translation_file.exists(), f"Translation file for {lang} should exist"
        
        # Load and verify all keys exist
        with open(translation_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)
        
        # Check that all required keys exist
        required_keys = [
            "input_prompt", "reconnecting", "reconnected", "connection_failed",
            "message_too_long", "server_error", "unknown_error", "cant_establish_channel",
            "message_too_large", "connection_lost", "users_in_chat", "quit_hint",
            "no_messages", "command_help", "command_nick_changed", "command_nick_usage",
            "command_room_switched", "command_room_usage", "command_quit",
            "rate_limit_exceeded", "error_processing"
        ]
        
        missing_keys = [key for key in required_keys if key not in translations]
        if missing_keys:
            print(f"❌ {lang}: Missing keys: {missing_keys}")
            return False
        
        # Verify English has all keys (reference)
        if lang == "en":
            en_keys = set(translations.keys())
            for other_lang in SUPPORTED_LANGUAGES:
                if other_lang != "en":
                    other_file = Path(__file__).parent.parent / "cmd_chat" / "client" / "i18n" / "locales" / f"{other_lang}.json"
                    if other_file.exists():
                        with open(other_file, 'r', encoding='utf-8') as f2:
                            other_translations = json.load(f2)
                        other_keys = set(other_translations.keys())
                        if en_keys != other_keys:
                            missing = en_keys - other_keys
                            extra = other_keys - en_keys
                            if missing or extra:
                                print(f"❌ {other_lang}: Key mismatch with English")
                                if missing:
                                    print(f"   Missing: {missing}")
                                if extra:
                                    print(f"   Extra: {extra}")
                                return False
        
        print(f"✅ {lang}: All keys present ({len(translations)} keys)")
    
    print("\n✅ All languages have complete translations")
    return True

def test_translation_fallback():
    """Test translation fallback to English."""
    print("\nTesting translation fallback...")
    
    # Test invalid language falls back to English
    tm = TranslationManager("invalid")
    assert tm.get_language() == "en", "Invalid language should fallback to English"
    print("✅ Invalid language falls back to English")
    
    # Test translation retrieval
    translation = tm.get("input_prompt")
    assert translation and translation != "input_prompt", "Should return translation, not key"
    print(f"✅ Translation retrieved: {translation[:30]}...")
    
    return True

if __name__ == "__main__":
    test_translation_manager()
    test_translation_fallback()
    print("\n" + "="*60)
    print("  I18N tests completed!")
    print("="*60)

