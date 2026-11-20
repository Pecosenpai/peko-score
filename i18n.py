"""
国際化 (i18n) 翻訳マネージャー
JSON形式の言語辞書を読み込み、キー指定でローカライズ文字列を返します。
"""
import json
import os
import sys

def get_resource_dir():
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

class I18nManager:
    SUPPORTED_LANGUAGES = {
        "ja": "Japanese / 日本語",
        "en": "English / 英語"
    }

    def __init__(self, current_lang: str = "ja"):
        self.current_lang = current_lang if current_lang in self.SUPPORTED_LANGUAGES else "ja"
        self._translations = {}
        self._load_translations()

    def _load_translations(self):
        res_dir = get_resource_dir()
        locales_dir = os.path.join(res_dir, "locales")
        
        # 開発環境用フォールバック
        if not os.path.exists(locales_dir):
            locales_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locales")

        for lang in self.SUPPORTED_LANGUAGES.keys():
            file_path = os.path.join(locales_dir, f"{lang}.json")
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        self._translations[lang] = json.load(f)
                except Exception as e:
                    print(f"Failed to load translation for {lang}: {e}")
                    self._translations[lang] = {}
            else:
                self._translations[lang] = {}

    def set_language(self, lang: str):
        if lang in self.SUPPORTED_LANGUAGES:
            self.current_lang = lang

    def t(self, key: str, **kwargs) -> str:
        """
        ドット区切りのキー (例: "nav.main", "main.win_plus") から翻訳テキストを取得
        プレースホルダーのフォーマット整形にも対応 (例: score_display="{wins}勝 {losses}敗")
        """
        data = self._translations.get(self.current_lang, {})
        keys = key.split(".")
        val = data
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                # 日本語辞書にフォールバック
                fallback_data = self._translations.get("ja", {})
                fb_val = fallback_data
                for fb_k in keys:
                    if isinstance(fb_val, dict) and fb_k in fb_val:
                        fb_val = fb_val[fb_k]
                    else:
                        return key
                val = fb_val
                break

        if isinstance(val, str) and kwargs:
            try:
                return val.format(**kwargs)
            except Exception:
                return val
        return str(val) if val is not None else key

# グローバルシングルトン
_i18n = I18nManager()

def get_i18n() -> I18nManager:
    return _i18n

def t(key: str, **kwargs) -> str:
    return _i18n.t(key, **kwargs)
