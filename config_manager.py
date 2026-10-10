import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG = {
    "wins": 0,
    "losses": 0,
    "draws": 0,
    "font_family": "Meiryo UI",
    "font_size": 64,
    "text_color": "#FFFFFF",
    "outline_color": "#222222",
    "animation_enabled": True,
    "auto_detect_enabled": True,
    "skin": "glassmorphism",
    "hotkey_win": "f7",
    "hotkey_loss": "f8",
    "hotkey_undo": "ctrl+shift+z",
    "hotkey_reset": "ctrl+shift+r",
    "hotkeys_enabled": True
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                config = DEFAULT_CONFIG.copy()
                config.update(data)
                return config
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Failed to save config: {e}")
