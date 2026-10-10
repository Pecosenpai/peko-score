import copy

DEFAULT_SKIN_COLORS = {
    "glassmorphism": {
        "bg": "#16211B",
        "border": "#84C4A0",
        "win": "#72EAA5",
        "loss": "#FFA599"
    },
    "badge": {
        "top_bg": "#6B9E83",
        "bot_bg": "#FFFFFF",
        "top_text": "#FFFFFF",
        "bot_text": "#D47A70"
    },
    "ticket": {
        "bg": "#F8FAF6",
        "border": "#7A9E88",
        "win": "#5F9175",
        "loss": "#C9685E"
    },
    "simple": {
        "win": "#72EAA5",
        "loss": "#FFA599",
        "unit": "#FFFFFF",
        "shadow": "#222222"
    }
}

SKIN_COLOR_LABELS = {
    "glassmorphism": [
        ("bg", "背景カラー"),
        ("border", "枠線 & 光彩"),
        ("win", "勝利数字"),
        ("loss", "敗北数字")
    ],
    "badge": [
        ("top_bg", "上段背景"),
        ("bot_bg", "下段背景"),
        ("top_text", "上段文字"),
        ("bot_text", "下段文字")
    ],
    "ticket": [
        ("bg", "カード背景"),
        ("border", "破線 & 枠"),
        ("win", "勝利数字"),
        ("loss", "敗北数字")
    ],
    "simple": [
        ("win", "勝利数字"),
        ("loss", "敗北数字"),
        ("unit", "単位文字"),
        ("shadow", "枠線 & 影")
    ]
}

def get_default_colors(skin):
    return copy.deepcopy(DEFAULT_SKIN_COLORS.get(skin, {}))

def normalize_config_colors(config):
    """config内のskin_colorsとskin_presetsを初期化・正規化"""
    if "skin_colors" not in config or not isinstance(config["skin_colors"], dict):
        config["skin_colors"] = {}
    if "skin_presets" not in config or not isinstance(config["skin_presets"], dict):
        config["skin_presets"] = {}
    if "current_preset" not in config or not isinstance(config["current_preset"], dict):
        config["current_preset"] = {}

    for skin, defaults in DEFAULT_SKIN_COLORS.items():
        if skin not in config["skin_colors"] or not isinstance(config["skin_colors"][skin], dict):
            config["skin_colors"][skin] = copy.deepcopy(defaults)
        else:
            # 欠けているキーを補完
            for k, v in defaults.items():
                if k not in config["skin_colors"][skin]:
                    config["skin_colors"][skin][k] = v

        if skin not in config["skin_presets"] or not isinstance(config["skin_presets"][skin], dict):
            config["skin_presets"][skin] = {
                "デフォルト": copy.deepcopy(defaults)
            }
        else:
            if "デフォルト" not in config["skin_presets"][skin]:
                config["skin_presets"][skin]["デフォルト"] = copy.deepcopy(defaults)

        if skin not in config["current_preset"]:
            config["current_preset"][skin] = "デフォルト"

    return config
