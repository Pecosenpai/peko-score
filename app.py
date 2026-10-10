import sys
import os
import copy
import queue
import webbrowser
import tkinter as tk
from tkinter import font as tkFont, messagebox, colorchooser
import customtkinter as ctk
from PIL import Image, ImageTk
import ctypes

# WindowsタスクバーにPythonアイコンではなくアプリ固有のアイコンを表示させる
try:
    myappid = "pekopekodo.pekoscore.counter.v1"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

from server import StateHolder, start_server
from detector_service import AutoDetectorService
from hotkey_service import HotkeyService
from config_manager import load_config, save_config
from monitor_helper import get_monitor_choices
from preview_renderer import render_preview
from skin_presets_manager import (
    DEFAULT_SKIN_COLORS, SKIN_COLOR_LABELS,
    normalize_config_colors, get_default_colors
)
import updater

# ぺこぺこ堂カラーパレット (ライト / ダーク両対応)
COLOR_BG_IVORY = ("#F6F7F2", "#181C19")       # 全体背景 (温かみのあるアイボリー / 深いフォレストブラック)
COLOR_SIDEBAR_BG = ("#E9EFEA", "#202622")     # サイドバー背景
COLOR_CARD_WHITE = ("#FFFFFF", "#272E29")     # カード背景
COLOR_CARD_BORDER = ("#E4E8E3", "#37413A")    # カード枠線
COLOR_SAGE_GREEN = "#5F8D75"                  # メインセージグリーン
COLOR_SAGE_LIGHT = ("#E9EFEA", "#2D3630")     # バッジ・選択背景
COLOR_SAGE_HOVER = "#507763"                  # セージのホバー色
COLOR_NAV_HOVER = ("#DFE7E0", "#2D3630")      # ナビボタン非選択時のホバー
COLOR_TEXT_MAIN = ("#2D3732", "#E8EFEA")      # メインテキスト
COLOR_TEXT_MUTED = ("#76867D", "#98A89F")     # 補助テキスト

COLOR_WIN_BTN = ("#5E9C7E", "#4E876B")        # 勝利ボタン (+1)
COLOR_WIN_HOVER = ("#4F856A", "#40735A")
COLOR_LOSS_BTN = ("#D87A6E", "#C7685D")       # 敗北ボタン (+1)
COLOR_LOSS_HOVER = ("#BF695D", "#AE5449")
COLOR_SUB_BTN = ("#8FA89B", "#38433C")        # -1 ボタン等
COLOR_SUB_HOVER = ("#7A9487", "#47544C")
COLOR_RESET_BTN = ("#E59086", "#5C3834")      # リセットボタン
COLOR_RESET_HOVER = ("#D17A70", "#6F423D")
COLOR_UNDO_BTN = ("#7CA5B8", "#384B54")       # Undoボタン
COLOR_UNDO_HOVER = ("#6A91A3", "#465C66")

class PekoScoreApp(ctk.CTk):
    def _windows_set_titlebar_color(self, color_mode: str):
        """
        Windowsのタイトルバー色をシームレスに変更。
        CustomTkinter標準の withdraw() -> deiconify() (タスクバーから消える動作) を回避し、
        DWM APIを直接呼ぶことで画面のチラつきやタスクバーアイコンの消失を完全に防止する。
        """
        if not sys.platform.startswith("win"):
            return
        value = 1 if color_mode.lower() == "dark" else 0
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(ctypes.c_int(value)),
                ctypes.sizeof(ctypes.c_int(value))
            ) != 0:
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1,
                    ctypes.byref(ctypes.c_int(value)),
                    ctypes.sizeof(ctypes.c_int(value))
                )
        except Exception:
            pass

    def apply_window_icons(self):
        """
        Windowsタスクバーおよびタイトルバーに公式マスコットアイコンを確実に適用する。
        iconbitmap + iconphoto (複数解像度) + Win32 API (WM_SETICON / SetClassLongPtr) を
        組み合わせることで、タスクバーがTkinter標準の青い羽になるのを防ぎます。
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ico_path = os.path.join(base_dir, "icon.ico")
        png_path = os.path.join(base_dir, "icon.png")

        # 1. Tkinter標準 iconbitmap
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

        # 2. Tkinter iconphoto (現代のWindowsタスクバーに確実反映)
        if os.path.exists(png_path):
            try:
                pil_master = Image.open(png_path)
                self._app_icon_photos = [
                    ImageTk.PhotoImage(pil_master.resize((s, s), Image.Resampling.LANCZOS))
                    for s in [16, 24, 32, 48, 64, 128, 256]
                ]
                self.iconphoto(True, *self._app_icon_photos)
            except Exception:
                pass

        # 3. Win32 API による直接WM_SETICONおよびクラスアイコン設定
        if sys.platform.startswith("win") and os.path.exists(ico_path):
            try:
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
                if not hwnd:
                    hwnd = self.winfo_id()
                IMAGE_ICON = 1
                LR_LOADFROMFILE = 0x00000010
                WM_SETICON = 0x0080
                ICON_SMALL = 0
                ICON_BIG = 1
                GCLP_HICON = -14
                GCLP_HICONSM = -34

                hicon_big = ctypes.windll.user32.LoadImageW(0, ico_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)
                hicon_small = ctypes.windll.user32.LoadImageW(0, ico_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
                if hicon_big:
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)
                    ctypes.windll.user32.SetClassLongPtrW(hwnd, GCLP_HICON, hicon_big)
                if hicon_small:
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)
                    ctypes.windll.user32.SetClassLongPtrW(hwnd, GCLP_HICONSM, hicon_small)
            except Exception:
                pass

    def __init__(self):
        super().__init__()

        # 設定読み込み & 正規化
        self.config = normalize_config_colors(load_config())

        # ウィンドウ初期設定 (サイズ固定)
        self.title("ぺこすこあ")
        self.geometry("780x560")
        self.resizable(False, False)

        # アイコン設定 (初回即時 + タイマー遅延適用で上書き防止)
        self.apply_window_icons()
        self.after(100, self.apply_window_icons)
        self.after(350, self.apply_window_icons)

        # CustomTkinter テーマ設定 (保存された設定を反映: light または dark)
        self.appearance_mode = self.config.get("appearance_mode", "light")
        ctk.set_appearance_mode(self.appearance_mode.capitalize())
        ctk.set_default_color_theme("green")
        self.configure(fg_color=COLOR_BG_IVORY)

        # 状態保持 & サーバー起動
        self.app_state = StateHolder()
        self.app_state.wins = self.config.get("wins", 0)
        self.app_state.losses = self.config.get("losses", 0)
        self.app_state.skin = self.config.get("skin", "glassmorphism")
        self.app_state.skin_colors = self.config.get("skin_colors", {})
        self.app_state.target_monitor = self.config.get("target_monitor", "auto")
        self.app_state.font_family = self.config.get("font_family", "Meiryo UI")
        self.app_state.font_size = self.config.get("font_size", 64)
        self.app_state.animation_enabled = self.config.get("animation_enabled", True)
        self.app_state.auto_detect_enabled = self.config.get("auto_detect_enabled", True)

        self.port = start_server(self.app_state, port=8080)
        self.obs_url = f"http://127.0.0.1:{self.port}/counter"

        # アップデート通知キュー (スレッドセーフ)
        self.update_result_queue = queue.Queue()

        # 自動検知サービス初期化
        base_dir = os.path.dirname(os.path.abspath(__file__))
        templates_dir = os.path.join(base_dir, "samples", "templates")
        self.detector = AutoDetectorService(self.app_state, templates_dir, on_result_callback=self.on_detect_result)
        self.detector.start()

        # ホットキーサービス初期化
        self.hotkey_service = HotkeyService(
            on_win=lambda: self.on_hotkey_action("win"),
            on_loss=lambda: self.on_hotkey_action("loss"),
            on_undo=lambda: self.on_hotkey_action("undo"),
            on_reset=lambda: self.on_hotkey_action("reset")
        )
        self.apply_hotkeys()

        # UI レイアウト構築
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_main_view()
        self.setup_obs_view()
        self.setup_hotkey_view()
        self.setup_settings_view()
        self.setup_help_view()

        # 初期表示はメイン画面
        self.show_view("main")

        # 終了時ハンドラ
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # 定期的なUI同期 (100msごと)
        self.update_ui_loop()

        # 起動時のサイレント・アップデート確認 (2秒後)
        self.after(2000, self.silent_check_for_updates)

    def setup_sidebar(self):
        # 左サイドバー
        self.sidebar_frame = ctk.CTkFrame(self, width=175, corner_radius=0, fg_color=COLOR_SIDEBAR_BG)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        # 行0: ヘッダー, 行1~5: ナビボタン, 行6: 伸縮スペーサー, 行7: 最下部ボタン
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        # アプリアイコン ＋ タイトルヘッダー (縦並び・中央揃え・大きめで可愛い)
        self.header_brand = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.header_brand.grid(row=0, column=0, padx=14, pady=(20, 14), sticky="ew")

        # もう1周り大きい 52x52px の可愛いマスコットアイコン (中央配置)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        png_path = os.path.join(base_dir, "icon.png")
        if os.path.exists(png_path):
            try:
                pil_img = Image.open(png_path)
                self.brand_icon_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(52, 52))
                self.lbl_brand_icon = ctk.CTkLabel(self.header_brand, text="", image=self.brand_icon_img)
                self.lbl_brand_icon.pack(side="top", pady=(0, 6))
            except Exception:
                pass

        # アイコンの下に「ぺこすこあ」 (中央配置)
        self.lbl_brand_title = ctk.CTkLabel(
            self.header_brand, text="ぺこすこあ",
            font=ctk.CTkFont(family="Meiryo UI", size=17, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        )
        self.lbl_brand_title.pack(side="top")

        # ナビゲーション用アイコン読み込み (ライト用・ダーク用・アクティブ用)
        icons_dir = os.path.join(base_dir, "icons")
        self.nav_icons = {}
        for key in ["main", "obs", "hotkey", "settings", "help"]:
            normal_path = os.path.join(icons_dir, f"nav_{key}.png")
            dark_path = os.path.join(icons_dir, f"nav_{key}_darkmode.png")
            active_path = os.path.join(icons_dir, f"nav_{key}_active.png")
            if os.path.exists(normal_path) and os.path.exists(active_path):
                img_norm = Image.open(normal_path)
                img_dark = Image.open(dark_path) if os.path.exists(dark_path) else img_norm
                img_act = Image.open(active_path)
                self.nav_icons[key] = {
                    "normal": ctk.CTkImage(light_image=img_norm, dark_image=img_dark, size=(20, 20)),
                    "active": ctk.CTkImage(light_image=img_act, dark_image=img_act, size=(20, 20))
                }
            else:
                self.nav_icons[key] = None

        # ナビゲーションボタン (ヘッダーの下に配置)
        img_main = self.nav_icons["main"]["active"] if self.nav_icons.get("main") else None
        self.btn_nav_main = ctk.CTkButton(
            self.sidebar_frame, text=" メイン", font=ctk.CTkFont(family="Meiryo UI", size=13, weight="bold"),
            image=img_main, compound="left", anchor="w",
            fg_color=COLOR_SAGE_GREEN, text_color="#FFFFFF", hover_color=COLOR_SAGE_HOVER,
            corner_radius=10, height=38, command=lambda: self.show_view("main")
        )
        self.btn_nav_main.grid(row=1, column=0, padx=14, pady=4, sticky="ew")

        img_obs = self.nav_icons["obs"]["normal"] if self.nav_icons.get("obs") else None
        self.btn_nav_obs = ctk.CTkButton(
            self.sidebar_frame, text=" OBS設定", font=ctk.CTkFont(family="Meiryo UI", size=13),
            image=img_obs, compound="left", anchor="w",
            fg_color="transparent", text_color=COLOR_TEXT_MAIN, hover_color=COLOR_NAV_HOVER,
            corner_radius=10, height=38, command=lambda: self.show_view("obs")
        )
        self.btn_nav_obs.grid(row=2, column=0, padx=14, pady=4, sticky="ew")

        img_hotkey = self.nav_icons["hotkey"]["normal"] if self.nav_icons.get("hotkey") else None
        self.btn_nav_hotkey = ctk.CTkButton(
            self.sidebar_frame, text=" ショートカット", font=ctk.CTkFont(family="Meiryo UI", size=13),
            image=img_hotkey, compound="left", anchor="w",
            fg_color="transparent", text_color=COLOR_TEXT_MAIN, hover_color=COLOR_NAV_HOVER,
            corner_radius=10, height=38, command=lambda: self.show_view("hotkey")
        )
        self.btn_nav_hotkey.grid(row=3, column=0, padx=14, pady=4, sticky="ew")

        img_settings = self.nav_icons["settings"]["normal"] if self.nav_icons.get("settings") else None
        self.btn_nav_settings = ctk.CTkButton(
            self.sidebar_frame, text=" 環境設定", font=ctk.CTkFont(family="Meiryo UI", size=13),
            image=img_settings, compound="left", anchor="w",
            fg_color="transparent", text_color=COLOR_TEXT_MAIN, hover_color=COLOR_NAV_HOVER,
            corner_radius=10, height=38, command=lambda: self.show_view("settings")
        )
        self.btn_nav_settings.grid(row=4, column=0, padx=14, pady=4, sticky="ew")

        img_help = self.nav_icons["help"]["normal"] if self.nav_icons.get("help") else None
        self.btn_nav_help = ctk.CTkButton(
            self.sidebar_frame, text=" ヘルプ", font=ctk.CTkFont(family="Meiryo UI", size=13),
            image=img_help, compound="left", anchor="w",
            fg_color="transparent", text_color=COLOR_TEXT_MAIN, hover_color=COLOR_NAV_HOVER,
            corner_radius=10, height=38, command=lambda: self.show_view("help")
        )
        self.btn_nav_help.grid(row=5, column=0, padx=14, pady=4, sticky="ew")

        # 最下部に常に密着するブラウザソースURLコピーボタン
        self.btn_copy_url = ctk.CTkButton(
            self.sidebar_frame, text="ブラウザソース用URLコピー", font=ctk.CTkFont(family="Meiryo UI", size=11),
            fg_color=("#FFFFFF", "#272E29"), text_color=COLOR_SAGE_GREEN, hover_color=("#F0F4F1", "#333C36"),
            corner_radius=8, height=36, border_width=1, border_color=COLOR_SAGE_GREEN,
            command=self.copy_obs_url
        )
        self.btn_copy_url.grid(row=7, column=0, padx=12, pady=16, sticky="sew")

    def setup_main_view(self):
        # メイン画面フレーム
        self.view_main = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.view_main.grid_columnconfigure(0, weight=1)
        self.view_main.grid_rowconfigure(1, weight=1)

        # ヘッダー (ステータス表示のみ)
        self.header_frame = ctk.CTkFrame(self.view_main, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=24, pady=(18, 0), sticky="ew")

        self.status_pill = ctk.CTkLabel(
            self.header_frame, text="● 自動検知中 (ゲーム待機中)",
            font=ctk.CTkFont(family="Meiryo UI", size=11, weight="bold"),
            text_color=COLOR_SAGE_GREEN, fg_color=COLOR_SAGE_LIGHT,
            corner_radius=12, padx=12, pady=4
        )
        self.status_pill.pack(side="right")

        # 中央カード (スコア表示 & ボタン群)
        self.center_card = ctk.CTkFrame(
            self.view_main, corner_radius=16, fg_color=COLOR_CARD_WHITE,
            border_width=1, border_color=COLOR_CARD_BORDER
        )
        self.center_card.grid(row=1, column=0, padx=24, pady=16, sticky="nsew")
        self.center_card.grid_columnconfigure((0, 1), weight=1)
        self.center_card.grid_rowconfigure(0, weight=1)

        # 大きなスコア表示: 「5勝 2敗」
        self.score_display = ctk.CTkLabel(
            self.center_card, text="0勝 0敗",
            font=ctk.CTkFont(family="Meiryo UI", size=54, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        )
        self.score_display.grid(row=0, column=0, columnspan=2, pady=(16, 6))

        # 手動操作ボタン群 (上段: +1勝, -1勝 / 下段: +1敗, -1敗)
        self.btn_win_plus = ctk.CTkButton(
            self.center_card, text="+1 勝", font=ctk.CTkFont(family="Meiryo UI", size=15, weight="bold"),
            fg_color=COLOR_WIN_BTN, hover_color=COLOR_WIN_HOVER, height=44, corner_radius=12,
            command=lambda: self.on_manual_modify(win_delta=1)
        )
        self.btn_win_plus.grid(row=1, column=0, padx=(24, 8), pady=5, sticky="ew")

        self.btn_win_minus = ctk.CTkButton(
            self.center_card, text="-1 勝", font=ctk.CTkFont(family="Meiryo UI", size=13),
            fg_color=COLOR_SUB_BTN, hover_color=COLOR_SUB_HOVER, height=44, corner_radius=12,
            command=lambda: self.on_manual_modify(win_delta=-1)
        )
        self.btn_win_minus.grid(row=1, column=1, padx=(8, 24), pady=5, sticky="ew")

        self.btn_loss_plus = ctk.CTkButton(
            self.center_card, text="+1 敗", font=ctk.CTkFont(family="Meiryo UI", size=15, weight="bold"),
            fg_color=COLOR_LOSS_BTN, hover_color=COLOR_LOSS_HOVER, height=44, corner_radius=12,
            command=lambda: self.on_manual_modify(loss_delta=1)
        )
        self.btn_loss_plus.grid(row=2, column=0, padx=(24, 8), pady=5, sticky="ew")

        self.btn_loss_minus = ctk.CTkButton(
            self.center_card, text="-1 敗", font=ctk.CTkFont(family="Meiryo UI", size=13),
            fg_color=COLOR_SUB_BTN, hover_color=COLOR_SUB_HOVER, height=44, corner_radius=12,
            command=lambda: self.on_manual_modify(loss_delta=-1)
        )
        self.btn_loss_minus.grid(row=2, column=1, padx=(8, 24), pady=5, sticky="ew")

        # 補助ボタン群 (取り消し & リセット)
        self.bottom_btn_frame = ctk.CTkFrame(self.center_card, fg_color="transparent")
        self.bottom_btn_frame.grid(row=3, column=0, columnspan=2, pady=(12, 18))

        self.btn_undo = ctk.CTkButton(
            self.bottom_btn_frame, text="↩ 取り消し (Undo)", font=ctk.CTkFont(family="Meiryo UI", size=12),
            fg_color=COLOR_UNDO_BTN, hover_color=COLOR_UNDO_HOVER, height=32, width=130, corner_radius=8,
            command=self.on_undo
        )
        self.btn_undo.pack(side="left", padx=8)

        self.btn_reset = ctk.CTkButton(
            self.bottom_btn_frame, text="🔄 リセット", font=ctk.CTkFont(family="Meiryo UI", size=12),
            fg_color=COLOR_RESET_BTN, hover_color=COLOR_RESET_HOVER, height=32, width=110, corner_radius=8,
            command=self.confirm_reset
        )
        self.btn_reset.pack(side="left", padx=8)

        # 直近ログ (最下部)
        self.log_label = ctk.CTkLabel(
            self.view_main, text="ログ: アプリを起動しました",
            font=ctk.CTkFont(family="Meiryo UI", size=11), text_color=COLOR_TEXT_MUTED
        )
        self.log_label.grid(row=2, column=0, padx=24, pady=(0, 14), sticky="w")

    def setup_obs_view(self):
        # OBS設定画面
        self.view_obs = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.view_obs.grid_columnconfigure(0, weight=1)

        obs_title = ctk.CTkLabel(
            self.view_obs, text="OBSブラウザソース設定",
            font=ctk.CTkFont(family="Meiryo UI", size=20, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        )
        obs_title.pack(anchor="w", padx=24, pady=(20, 10))

        obs_card = ctk.CTkScrollableFrame(self.view_obs, corner_radius=16, fg_color=COLOR_CARD_WHITE, border_width=1, border_color=COLOR_CARD_BORDER)
        obs_card.pack(fill="both", expand=True, padx=24, pady=10)

        # URL案内
        url_label = ctk.CTkLabel(obs_card, text=f"ブラウザソースURL: {self.obs_url}", font=ctk.CTkFont(family="Meiryo UI", size=13, weight="bold"), text_color=COLOR_SAGE_GREEN)
        url_label.pack(anchor="w", padx=20, pady=(16, 4))
        
        url_sub = ctk.CTkLabel(obs_card, text="※OBSの「ブラウザソース」に追加し、幅500×高さ200等に設定してください。", font=ctk.CTkFont(family="Meiryo UI", size=11), text_color=COLOR_TEXT_MUTED)
        url_sub.pack(anchor="w", padx=20, pady=(0, 10))

        # プレビュー表示エリア (スキン選択の上)
        self.preview_container = ctk.CTkFrame(obs_card, fg_color="#1A2027", corner_radius=12)
        self.preview_container.pack(fill="x", padx=20, pady=(0, 12))

        self.lbl_obs_preview = ctk.CTkLabel(self.preview_container, text="", fg_color="transparent")
        self.lbl_obs_preview.pack(padx=4, pady=4)

        # スキン/テーマ選択
        skin_frame = ctk.CTkFrame(obs_card, fg_color="transparent")
        skin_frame.pack(fill="x", padx=20, pady=6)

        ctk.CTkLabel(skin_frame, text="スキン / テーマ:", font=ctk.CTkFont(family="Meiryo UI", size=13), text_color=COLOR_TEXT_MAIN).pack(side="left", padx=(0, 12))
        
        self.skin_map = {
            "グラスモーフィズム HUD": "glassmorphism",
            "ピルバッジ": "badge",
            "レトロチケット": "ticket",
            "シンプル文字のみ": "simple"
        }
        self.skin_reverse_map = {v: k for k, v in self.skin_map.items()}

        current_skin_key = self.skin_reverse_map.get(self.app_state.skin, "グラスモーフィズム HUD")
        self.skin_combo = ctk.CTkComboBox(
            skin_frame, values=list(self.skin_map.keys()), width=240,
            font=ctk.CTkFont(family="Meiryo UI", size=12),
            dropdown_font=ctk.CTkFont(family="Meiryo UI", size=12),
            state="readonly",
            command=self.on_skin_change
        )
        self.skin_combo.set(current_skin_key)
        self.skin_combo.pack(side="left")

        # カラーカスタマイズ & プリセット管理枠
        self.color_custom_box = ctk.CTkFrame(obs_card, fg_color=("#F5F8F6", "#212823"), corner_radius=12)
        self.color_custom_box.pack(fill="x", padx=20, pady=(6, 12))

        # プリセット行 (プリセット選択、保存、リセット、削除)
        preset_row = ctk.CTkFrame(self.color_custom_box, fg_color="transparent")
        preset_row.pack(fill="x", padx=12, pady=(10, 6))

        ctk.CTkLabel(preset_row, text="配色プリセット:", font=ctk.CTkFont(family="Meiryo UI", size=12, weight="bold"), text_color=COLOR_TEXT_MAIN).pack(side="left", padx=(0, 8))

        self.preset_combo = ctk.CTkComboBox(
            preset_row, values=["デフォルト"], width=140,
            font=ctk.CTkFont(family="Meiryo UI", size=11),
            dropdown_font=ctk.CTkFont(family="Meiryo UI", size=11),
            state="readonly",
            command=self.on_preset_select
        )
        self.preset_combo.pack(side="left", padx=(0, 8))

        self.btn_save_preset = ctk.CTkButton(
            preset_row, text="保存", width=50, height=28,
            font=ctk.CTkFont(family="Meiryo UI", size=11, weight="bold"),
            fg_color=COLOR_SAGE_GREEN, hover_color=COLOR_SAGE_HOVER,
            command=self.on_save_preset
        )
        self.btn_save_preset.pack(side="left", padx=(0, 6))

        self.btn_reset_preset = ctk.CTkButton(
            preset_row, text="リセット", width=62, height=28,
            font=ctk.CTkFont(family="Meiryo UI", size=11),
            fg_color=("#E0E6E2", "#353F38"), hover_color=("#D0DAD3", "#434F47"),
            text_color=COLOR_TEXT_MAIN,
            command=self.on_reset_preset
        )
        self.btn_reset_preset.pack(side="left", padx=(0, 6))

        self.btn_delete_preset = ctk.CTkButton(
            preset_row, text="削除", width=48, height=28,
            font=ctk.CTkFont(family="Meiryo UI", size=11),
            fg_color=("#F2DFDC", "#4D3432"), hover_color=("#E8CCC8", "#5E3E3B"),
            text_color=("#C45B50", "#EFA8A0"),
            command=self.on_delete_preset
        )
        self.btn_delete_preset.pack(side="left")

        # カラー選択タイル表示枠
        self.color_tiles_frame = ctk.CTkFrame(self.color_custom_box, fg_color="transparent")
        self.color_tiles_frame.pack(fill="x", padx=12, pady=(4, 10))

        # フォント選択
        font_frame = ctk.CTkFrame(obs_card, fg_color="transparent")
        font_frame.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(font_frame, text="フォント選択:", font=ctk.CTkFont(family="Meiryo UI", size=13), text_color=COLOR_TEXT_MAIN).pack(side="left", padx=(0, 12))
        
        font_candidates = ["Meiryo UI", "Yu Gothic UI", "MS Gothic", "Arial", "Impact", "Consolas"]
        self.font_combo = ctk.CTkComboBox(
            font_frame, values=font_candidates, width=180,
            font=ctk.CTkFont(family="Meiryo UI", size=12),
            dropdown_font=ctk.CTkFont(family="Meiryo UI", size=12),
            state="readonly",
            command=self.on_font_change
        )
        self.font_combo.set(self.app_state.font_family)
        self.font_combo.pack(side="left")

        # 文字サイズ
        size_frame = ctk.CTkFrame(obs_card, fg_color="transparent")
        size_frame.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(size_frame, text="文字サイズ (px):", font=ctk.CTkFont(family="Meiryo UI", size=13), text_color=COLOR_TEXT_MAIN).pack(side="left", padx=(0, 12))
        self.size_slider = ctk.CTkSlider(size_frame, from_=32, to=120, number_of_steps=22, width=180, command=self.on_size_change)
        self.size_slider.set(self.app_state.font_size)
        self.size_slider.pack(side="left", padx=(0, 12))
        self.lbl_size_val = ctk.CTkLabel(size_frame, text=f"{self.app_state.font_size}px", font=ctk.CTkFont(family="Meiryo UI", size=12), text_color=COLOR_TEXT_MAIN)
        self.lbl_size_val.pack(side="left")

        # アニメーション切り替え
        self.switch_anim = ctk.CTkSwitch(
            obs_card, text="カウント時に弾むアニメーション (Pop)", font=ctk.CTkFont(family="Meiryo UI", size=13),
            progress_color=COLOR_SAGE_GREEN, command=self.on_anim_toggle
        )
        self.switch_anim.select() if self.app_state.animation_enabled else self.switch_anim.deselect()
        self.switch_anim.pack(anchor="w", padx=20, pady=(12, 16))

        # 初期カラーコントロール & プレビュー描画
        self.rebuild_color_controls()
        self.update_obs_preview()

    def setup_hotkey_view(self):
        # ショートカットキー設定画面
        self.view_hotkey = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.view_hotkey.grid_columnconfigure(0, weight=1)

        # 現在キー割り当て待ちの状態管理
        self.binding_action = None  # "win", "loss", "undo", "reset"
        self.pressed_keys_record = set()

        hk_title = ctk.CTkLabel(
            self.view_hotkey, text="ショートカットキー設定",
            font=ctk.CTkFont(family="Meiryo UI", size=20, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        )
        hk_title.pack(anchor="w", padx=24, pady=(20, 10))

        hk_card = ctk.CTkFrame(self.view_hotkey, corner_radius=16, fg_color=COLOR_CARD_WHITE, border_width=1, border_color=COLOR_CARD_BORDER)
        hk_card.pack(fill="both", expand=True, padx=24, pady=10)

        # ホットキー有効化スイッチ
        self.switch_hk_enable = ctk.CTkSwitch(
            hk_card, text="グローバルショートカットキーを有効化", font=ctk.CTkFont(family="Meiryo UI", size=13, weight="bold"),
            progress_color=COLOR_SAGE_GREEN, command=self.on_hotkey_toggle
        )
        self.switch_hk_enable.select() if self.config.get("hotkeys_enabled", True) else self.switch_hk_enable.deselect()
        self.switch_hk_enable.pack(anchor="w", padx=20, pady=(18, 8))

        desc_label = ctk.CTkLabel(
            hk_card, 
            text="ボタンをクリック後、設定したいキーを押すだけで割り当てられます（ESCでキャンセル）。\nゲームプレイ中（画面が最前面）でもキー入力で手動介入できます。",
            font=ctk.CTkFont(family="Meiryo UI", size=11), text_color=COLOR_TEXT_MUTED, justify="left"
        )
        desc_label.pack(anchor="w", padx=20, pady=(0, 14))

        # キーバインドリスト
        list_frame = ctk.CTkFrame(hk_card, fg_color="transparent")
        list_frame.pack(fill="x", padx=20, pady=6)
        list_frame.grid_columnconfigure(0, weight=1)

        self.hk_action_labels = {
            "win": "勝利 (+1)",
            "loss": "敗北 (+1)",
            "undo": "取り消し (Undo)",
            "reset": "リセット"
        }
        self.hk_buttons = {}

        row_idx = 0
        for act_id, act_name in self.hk_action_labels.items():
            row_frame = ctk.CTkFrame(list_frame, fg_color=("#F8FAF7", "#2F3731"), corner_radius=10, height=44)
            row_frame.grid(row=row_idx, column=0, pady=5, sticky="ew")
            row_frame.grid_columnconfigure(0, weight=1)

            lbl = ctk.CTkLabel(
                row_frame, text=act_name,
                font=ctk.CTkFont(family="Meiryo UI", size=13, weight="bold"),
                text_color=COLOR_TEXT_MAIN
            )
            lbl.grid(row=0, column=0, padx=16, pady=8, sticky="w")

            key_text = self.config.get(f"hotkey_{act_id}", "未設定").upper()
            btn = ctk.CTkButton(
                row_frame, text=key_text,
                font=ctk.CTkFont(family="Meiryo UI", size=12, weight="bold"),
                fg_color=COLOR_SAGE_GREEN, hover_color=COLOR_SAGE_HOVER,
                text_color="#FFFFFF", corner_radius=8, width=150, height=32,
                command=lambda a=act_id: self.start_key_binding(a)
            )
            btn.grid(row=0, column=1, padx=16, pady=6, sticky="e")
            self.hk_buttons[act_id] = btn
            row_idx += 1

        # キー割り当て中のステータス表示枠
        self.binding_status_frame = ctk.CTkFrame(hk_card, fg_color=("#EEF5F0", "#2D3831"), corner_radius=10)
        self.binding_status_lbl = ctk.CTkLabel(
            self.binding_status_frame, 
            text="キーを押してください (ESCでキャンセル)",
            font=ctk.CTkFont(family="Meiryo UI", size=13, weight="bold"),
            text_color=COLOR_SAGE_GREEN
        )
        self.binding_status_lbl.pack(pady=10)

    def setup_settings_view(self):
        # 環境設定画面
        self.view_settings = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.view_settings.grid_columnconfigure(0, weight=1)

        set_title = ctk.CTkLabel(
            self.view_settings, text="環境 & 検知設定",
            font=ctk.CTkFont(family="Meiryo UI", size=20, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        )
        set_title.pack(anchor="w", padx=24, pady=(20, 10))

        set_card = ctk.CTkFrame(self.view_settings, corner_radius=16, fg_color=COLOR_CARD_WHITE, border_width=1, border_color=COLOR_CARD_BORDER)
        set_card.pack(fill="both", expand=True, padx=24, pady=10)

        # 外観テーマ選択 (ライトモード / ダークモード)
        theme_frame = ctk.CTkFrame(set_card, fg_color="transparent")
        theme_frame.pack(fill="x", padx=20, pady=(20, 8))

        ctk.CTkLabel(theme_frame, text="外観テーマ:", font=ctk.CTkFont(family="Meiryo UI", size=13), text_color=COLOR_TEXT_MAIN).pack(side="left", padx=(0, 12))

        self.theme_segment = ctk.CTkSegmentedButton(
            theme_frame, values=["ライトモード", "ダークモード"],
            font=ctk.CTkFont(family="Meiryo UI", size=12),
            selected_color=COLOR_SAGE_GREEN, selected_hover_color=COLOR_SAGE_HOVER,
            command=self.on_theme_change
        )
        current_theme_str = "ダークモード" if getattr(self, "appearance_mode", "light").lower() == "dark" else "ライトモード"
        self.theme_segment.set(current_theme_str)
        self.theme_segment.pack(side="left")

        # 自動検知の有効化
        self.switch_auto = ctk.CTkSwitch(
            set_card, text="ゲーム自動勝敗検知を有効化", font=ctk.CTkFont(family="Meiryo UI", size=13, weight="bold"),
            progress_color=COLOR_SAGE_GREEN, command=self.on_auto_detect_toggle
        )
        self.switch_auto.select() if self.app_state.auto_detect_enabled else self.switch_auto.deselect()
        self.switch_auto.pack(anchor="w", padx=20, pady=(12, 12))

        # モニター選択
        mon_frame = ctk.CTkFrame(set_card, fg_color="transparent")
        mon_frame.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(mon_frame, text="監視モニター:", font=ctk.CTkFont(family="Meiryo UI", size=13), text_color=COLOR_TEXT_MAIN).pack(side="left", padx=(0, 12))

        # モニター一覧の取得 (実機の型番検出 & 絵文字なし)
        self.monitor_options = get_monitor_choices()
        self.monitor_reverse_map = {v: k for k, v in self.monitor_options.items()}
        current_mon_key = self.monitor_reverse_map.get(self.app_state.target_monitor, "自動追従 (ゲーム画面があるモニター)")

        self.mon_combo = ctk.CTkComboBox(
            mon_frame, values=list(self.monitor_options.keys()), width=290,
            font=ctk.CTkFont(family="Meiryo UI", size=12),
            dropdown_font=ctk.CTkFont(family="Meiryo UI", size=12),
            state="readonly",
            command=self.on_monitor_change
        )
        self.mon_combo.set(current_mon_key)
        self.mon_combo.pack(side="left")

        lbl_desc = ctk.CTkLabel(
            set_card, 
            text="・【外観テーマ】作業環境やお好みに応じてライト／ダークを瞬時に切り替えられます。\n・【自動追従】ゲーム画面がサブモニターにあっても自動で判定します。\n・色覚サポートやカスタムUIカラー変更でも高精度に自動判定可能です。\n・多重カウント防止のため、検知後は25秒間のクールダウンが入ります。",
            font=ctk.CTkFont(family="Meiryo UI", size=12), text_color=COLOR_TEXT_MUTED, justify="left"
        )
        lbl_desc.pack(anchor="w", padx=20, pady=(16, 20))

    def load_help_content(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "help_content.json")
        default_content = {
            "app_info": {
                "version": "Ver 1.0.0",
                "subtitle": "配信者向け対戦ゲーム専用\n勝敗自動カウントツール",
                "credit": "Presented by ぺこぺこ堂\n(PekoPeko-Do)",
                "contact_button_text": "お問い合わせ・ご要望",
                "contact_url": "https://forms.gle/dummy",
                "contact_hint": "※Googleフォームが開きます"
            },
            "faqs": [
                {
                    "q": "勝敗が自動でカウントされない",
                    "a": "ゲームの画面設定が「ボーダーレス・ウィンドウ」または「ウィンドウ」になっているかご確認ください。全画面排他モードや他アプリの被りがあると検知できない場合があります。"
                },
                {
                    "q": "検知後に連続してカウントされない",
                    "a": "多重カウントを防止するため、検知成功後は25秒間のクールダウン（待機時間）が入ります。終了後に次戦の自動検知が可能になります。"
                },
                {
                    "q": "OBSにカウンター画面が映らない",
                    "a": "ブラウザソースURLが「http://127.0.0.1:8080/counter」になっているか、セキュリティソフト等で遮断されていないかご確認ください。"
                }
            ],
            "legal_text": "【権利表記】 Overwatch® は Blizzard Entertainment, Inc. の商標または登録商標です。本ツールは個人が制作した非公式のファンメイドツールであり、Blizzard Entertainment との提携・公認関係等にはありません。\n\n【免責事項】 本ツールの使用により生じたいかなるトラブル・損害も制作者は責任を負いかねます。各配信プラットフォーム等の規約を遵守してご利用ください。\n\n【フォント・UI】 Zen Maru Gothic (SIL OFL 1.1) / © 2026 ぺこぺこ堂"
        }
        if os.path.exists(path):
            try:
                import json
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._cached_help_data = data
                    return data
            except Exception as e:
                print(f"Error loading help_content.json: {e}")
                if hasattr(self, "_cached_help_data"):
                    return self._cached_help_data
        return default_content

    def open_feedback_form(self):
        help_data = self.load_help_content()
        url = help_data.get("app_info", {}).get("contact_url", "https://forms.gle/dummy")
        try:
            webbrowser.open(url)
            self.log(f"お問い合わせフォームを開きました: {url}")
        except Exception as e:
            self.log(f"フォームを開けませんでした: {e}")

    def on_check_update_clicked(self):
        if hasattr(self, "btn_check_update") and self.btn_check_update.winfo_exists():
            self.btn_check_update.configure(text="確認中...", state="disabled")
        if hasattr(self, "lbl_update_status") and self.lbl_update_status.winfo_exists():
            self.lbl_update_status.configure(text="")

        updater.check_for_updates_async(lambda res: self.update_result_queue.put((res, True)))

    def silent_check_for_updates(self):
        updater.check_for_updates_async(lambda res: self.update_result_queue.put((res, False)))

    def on_update_result_received(self, res, user_initiated=True):
        if hasattr(self, "btn_check_update") and self.btn_check_update.winfo_exists():
            self.btn_check_update.configure(text="アップデートを確認", state="normal")

        if not res.get("success"):
            if user_initiated:
                if hasattr(self, "lbl_update_status") and self.lbl_update_status.winfo_exists():
                    self.lbl_update_status.configure(text="確認に失敗しました", text_color=COLOR_TEXT_MUTED)
                self.log(f"アップデート確認エラー: {res.get('error')}")
            return

        if res.get("has_update"):
            latest_v = res.get("latest_version")
            if hasattr(self, "lbl_update_status") and self.lbl_update_status.winfo_exists():
                self.lbl_update_status.configure(text=f"🎉 {latest_v} が利用可能！", text_color=COLOR_SAGE_GREEN)
            self.log(f"新バージョンが見つかりました: {latest_v}")
            if hasattr(self, "btn_nav_help") and self.btn_nav_help.winfo_exists():
                self.btn_nav_help.configure(text=" ヘルプ ●")
            if user_initiated:
                self.show_update_modal(res)
        else:
            if user_initiated:
                if hasattr(self, "lbl_update_status") and self.lbl_update_status.winfo_exists():
                    self.lbl_update_status.configure(text="最新バージョンです", text_color=COLOR_TEXT_MUTED)
                self.log("アプリは最新バージョンです")

    def show_update_modal(self, res):
        dlg = ctk.CTkToplevel(self)
        dlg.title("ぺこすこあ アップデート")
        dlg.geometry("440x370")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()

        # ヘッダー
        ctk.CTkLabel(
            dlg, text="🎉 新しいバージョンが見つかりました！",
            font=ctk.CTkFont(family="Meiryo UI", size=15, weight="bold"),
            text_color=COLOR_SAGE_GREEN
        ).pack(pady=(18, 4))

        latest_v = res.get("latest_version", "")
        cur_v = res.get("current_version", updater.CURRENT_VERSION)
        ctk.CTkLabel(
            dlg, text=f"現在: {cur_v}  ➜  最新: {latest_v}",
            font=ctk.CTkFont(family="Meiryo UI", size=12, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        ).pack(pady=(0, 10))

        # 更新内容テキストボックス
        notes_box = ctk.CTkTextbox(dlg, width=380, height=130, font=ctk.CTkFont(family="Meiryo UI", size=11))
        notes_box.pack(padx=20, pady=(0, 10))
        notes_box.insert("1.0", res.get("release_notes", "更新内容はありません。"))
        notes_box.configure(state="disabled")

        # プログレスバー & ステータス
        lbl_prog = ctk.CTkLabel(dlg, text="", font=ctk.CTkFont(family="Meiryo UI", size=11), text_color=COLOR_TEXT_MUTED)
        prog_bar = ctk.CTkProgressBar(dlg, width=380, progress_color=COLOR_SAGE_GREEN)
        prog_bar.set(0)

        btn_frame = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(6, 16))

        def start_download():
            dl_url = res.get("download_url")
            if not dl_url:
                webbrowser.open(res.get("html_url", ""))
                dlg.destroy()
                return

            btn_update.configure(state="disabled")
            btn_browser.configure(state="disabled")
            lbl_prog.pack(pady=(0, 4))
            prog_bar.pack(pady=(0, 8))
            lbl_prog.configure(text="最新版をダウンロード中...")

            base_dir = os.path.dirname(os.path.abspath(__file__))

            prog_queue = queue.Queue()
            def on_progress(p):
                prog_queue.put((p, None))
            def on_err(err_msg):
                prog_queue.put((None, err_msg))

            updater.download_and_install_update(dl_url, base_dir, on_progress, on_err)

            def poll_progress():
                try:
                    while not prog_queue.empty():
                        p, err = prog_queue.get_nowait()
                        if err:
                            lbl_prog.configure(text=f"エラー: {err}", text_color="#D9534F")
                            btn_browser.configure(state="normal")
                        elif p is not None:
                            prog_bar.set(p)
                            pct = int(p * 100)
                            lbl_prog.configure(text=f"ダウンロード中... {pct}%" if p < 1.0 else "更新を適用して再起動します...")
                except Exception:
                    pass
                if dlg.winfo_exists():
                    dlg.after(100, poll_progress)

            dlg.after(100, poll_progress)

        btn_update = ctk.CTkButton(
            btn_frame, text="今すぐ自動更新",
            font=ctk.CTkFont(family="Meiryo UI", size=12, weight="bold"),
            fg_color=COLOR_SAGE_GREEN, hover_color=COLOR_SAGE_HOVER,
            command=start_download
        )
        btn_update.pack(side="left", expand=True, fill="x", padx=(0, 6))

        btn_browser = ctk.CTkButton(
            btn_frame, text="GitHubで確認",
            font=ctk.CTkFont(family="Meiryo UI", size=11),
            fg_color="transparent", text_color=COLOR_TEXT_MAIN,
            border_width=1, border_color=COLOR_CARD_BORDER,
            command=lambda: webbrowser.open(res.get("html_url", ""))
        )
        btn_browser.pack(side="left", padx=(0, 6))

        btn_close = ctk.CTkButton(
            btn_frame, text="閉じる",
            font=ctk.CTkFont(family="Meiryo UI", size=11),
            fg_color="transparent", text_color=COLOR_TEXT_MUTED,
            width=60, command=dlg.destroy
        )
        btn_close.pack(side="left")

    def setup_help_view(self):
        # ヘルプ & アプリ情報 画面
        self.view_help = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.view_help.grid_columnconfigure(0, weight=1)
        self.view_help.grid_rowconfigure(1, weight=1)

        help_title = ctk.CTkLabel(
            self.view_help, text="ヘルプ & アプリ情報",
            font=ctk.CTkFont(family="Meiryo UI", size=18, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        )
        help_title.grid(row=0, column=0, sticky="w", padx=20, pady=(14, 8))

        # 左右2カラムのコンテナフレーム
        self.help_container = ctk.CTkFrame(self.view_help, fg_color="transparent")
        self.help_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 14))
        self.help_container.grid_columnconfigure(0, weight=0, minsize=190)  # 左: 幅固定 (190px)
        self.help_container.grid_columnconfigure(1, weight=1)              # 右: 残り全幅を広く確保 (~350px+)
        self.help_container.grid_rowconfigure(0, weight=1)

        # 初期mtimeの記録
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "help_content.json")
        if os.path.exists(path):
            self.last_help_mtime = os.path.getmtime(path)
        else:
            self.last_help_mtime = 0

        self.rebuild_help_view_content()

    def rebuild_help_view_content(self):
        if not hasattr(self, "help_container") or not self.help_container.winfo_exists():
            return

        for child in self.help_container.winfo_children():
            child.destroy()

        help_data = self.load_help_content()
        app_info = help_data.get("app_info", {})

        # ----------------------------------------------------
        # 左カラム: アプリ情報カード
        # ----------------------------------------------------
        card_left = ctk.CTkFrame(
            self.help_container, width=190, corner_radius=14,
            fg_color=COLOR_CARD_WHITE, border_width=1, border_color=COLOR_CARD_BORDER
        )
        card_left.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        card_left.pack_propagate(False)

        # マスコットアイコン (コンパクトな48x48)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        png_path = os.path.join(base_dir, "icon.png")
        if os.path.exists(png_path):
            try:
                pil_icon = Image.open(png_path)
                self.help_mascot_img = ctk.CTkImage(light_image=pil_icon, dark_image=pil_icon, size=(48, 48))
                lbl_icon = ctk.CTkLabel(card_left, text="", image=self.help_mascot_img)
                lbl_icon.pack(pady=(16, 4))
            except Exception:
                pass

        # アプリ名
        lbl_name = ctk.CTkLabel(
            card_left, text="ぺこすこあ",
            font=ctk.CTkFont(family="Meiryo UI", size=17, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        )
        lbl_name.pack(pady=(0, 2))

        # バージョンバッジ
        version_pill = ctk.CTkLabel(
            card_left, text=app_info.get("version", "Ver 1.0.0"),
            font=ctk.CTkFont(family="Meiryo UI", size=10, weight="bold"),
            text_color=COLOR_SAGE_GREEN,
            fg_color=COLOR_SAGE_LIGHT,
            corner_radius=10,
            padx=8, pady=1
        )
        version_pill.pack(pady=(0, 6))

        # サブ説明
        lbl_sub = ctk.CTkLabel(
            card_left, text=app_info.get("subtitle", "Overwatch 2 専用\n勝敗自動カウントツール"),
            font=ctk.CTkFont(family="Meiryo UI", size=12),
            text_color=COLOR_TEXT_MAIN,
            justify="center"
        )
        lbl_sub.pack(pady=(0, 10))

        # 区切り線
        div_left = ctk.CTkFrame(card_left, height=1, fg_color=COLOR_CARD_BORDER)
        div_left.pack(fill="x", padx=16, pady=(0, 10))

        # クレジット
        lbl_credit = ctk.CTkLabel(
            card_left, text=app_info.get("credit", "Presented by ぺこぺこ堂\n(PekoPeko-Do)"),
            font=ctk.CTkFont(family="Meiryo UI", size=11, weight="bold"),
            text_color=COLOR_TEXT_MAIN,
            justify="center"
        )
        lbl_credit.pack(pady=(0, 14))

        # お問い合わせボタン
        btn_form = ctk.CTkButton(
            card_left,
            text=app_info.get("contact_button_text", "お問い合わせ・ご要望"),
            font=ctk.CTkFont(family="Meiryo UI", size=11, weight="bold"),
            fg_color=COLOR_SAGE_GREEN,
            hover_color=COLOR_SAGE_HOVER,
            height=34,
            corner_radius=8,
            command=self.open_feedback_form
        )
        btn_form.pack(fill="x", padx=14, pady=(0, 4))

        lbl_form_hint = ctk.CTkLabel(
            card_left,
            text=app_info.get("contact_hint", "※Googleフォームが開きます"),
            font=ctk.CTkFont(family="Meiryo UI", size=11),
            text_color=COLOR_TEXT_MUTED
        )
        lbl_form_hint.pack(pady=(0, 8))

        # アップデート確認ボタン & ステータス
        self.btn_check_update = ctk.CTkButton(
            card_left,
            text="アップデートを確認",
            font=ctk.CTkFont(family="Meiryo UI", size=11),
            fg_color=("#E5ECE7", "#323B34"),
            text_color=COLOR_TEXT_MAIN,
            hover_color=COLOR_NAV_HOVER,
            height=30,
            corner_radius=8,
            command=self.on_check_update_clicked
        )
        self.btn_check_update.pack(fill="x", padx=14, pady=(0, 2))

        self.lbl_update_status = ctk.CTkLabel(
            card_left,
            text="",
            font=ctk.CTkFont(family="Meiryo UI", size=10),
            text_color=COLOR_TEXT_MUTED
        )
        self.lbl_update_status.pack(pady=(0, 6))

        # ----------------------------------------------------
        # 右カラム: FAQ & 権利表記 (横幅を広く確保 + 動的自動折り返し)
        # ----------------------------------------------------
        card_right = ctk.CTkScrollableFrame(
            self.help_container, corner_radius=14,
            fg_color=COLOR_CARD_WHITE, border_width=1, border_color=COLOR_CARD_BORDER
        )
        card_right.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)

        # FAQ 見出し
        lbl_faq_head = ctk.CTkLabel(
            card_right, text="よくある質問・トラブルシューティング",
            font=ctk.CTkFont(family="Meiryo UI", size=14, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        )
        lbl_faq_head.pack(anchor="w", padx=12, pady=(10, 6))

        faqs = help_data.get("faqs", [])

        self.help_wrap_labels = []
        for item in faqs:
            q = item.get("q", "")
            a = item.get("a", "")
            q_box = ctk.CTkFrame(card_right, fg_color=COLOR_SAGE_LIGHT, corner_radius=8)
            q_box.pack(fill="x", padx=10, pady=4)

            lbl_q = ctk.CTkLabel(
                q_box, text=f"Q. {q}",
                font=ctk.CTkFont(family="Meiryo UI", size=12, weight="bold"),
                text_color=COLOR_TEXT_MAIN, justify="left", anchor="w"
            )
            lbl_q.pack(anchor="w", padx=10, pady=(5, 2))

            lbl_a = ctk.CTkLabel(
                q_box, text=a,
                font=ctk.CTkFont(family="Meiryo UI", size=12),
                text_color=("#37453E", "#D8E6DD"), justify="left", anchor="w"
            )
            lbl_a.pack(anchor="w", padx=10, pady=(0, 6))
            self.help_wrap_labels.append(lbl_a)

        # 区切り線
        div_right = ctk.CTkFrame(card_right, height=1, fg_color=COLOR_CARD_BORDER)
        div_right.pack(fill="x", padx=10, pady=8)

        # 権利表記 & 免責事項 見出し
        lbl_legal_head = ctk.CTkLabel(
            card_right, text="権利表記 & 免責事項",
            font=ctk.CTkFont(family="Meiryo UI", size=13, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        )
        lbl_legal_head.pack(anchor="w", padx=12, pady=(0, 4))

        legal_text = help_data.get("legal_text", "")
        lbl_legal = ctk.CTkLabel(
            card_right, text=legal_text,
            font=ctk.CTkFont(family="Meiryo UI", size=11),
            text_color=("#45524B", "#C2D4C9"),
            justify="left", anchor="w"
        )
        lbl_legal.pack(anchor="w", padx=12, pady=(0, 12))
        self.help_wrap_labels.append(lbl_legal)

        # 右カードの幅変化に応じて折り返し幅とスクロール領域を自動再計算 (文字欠け・見切れ防止 & スクロール機能維持)
        def on_right_card_resize(event=None):
            w = event.width if event else card_right.winfo_width()
            wrap_w = max(220, w - 48) if w > 50 else 320
            for lbl in self.help_wrap_labels:
                if lbl.winfo_exists():
                    lbl.configure(wraplength=wrap_w)
            card_right.update_idletasks()
            # スクロール領域 (scrollregion) を最新のコンテンツ高さに合わせて明示的に更新
            card_right._parent_canvas.configure(scrollregion=card_right._parent_canvas.bbox("all"))

        # add="+" を指定して CTkScrollableFrame 内部のバインドを上書きせず保持
        card_right.bind("<Configure>", on_right_card_resize, add="+")
        self.after(50, on_right_card_resize)

    def check_help_content_reload(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "help_content.json")
        if os.path.exists(path):
            try:
                mtime = os.path.getmtime(path)
                if not hasattr(self, "last_help_mtime"):
                    self.last_help_mtime = mtime
                elif mtime != self.last_help_mtime:
                    self.last_help_mtime = mtime
                    self.rebuild_help_view_content()
                    self.log("ヘルプ内容を自動リロードしました")
            except Exception as e:
                pass


    def show_view(self, name):
        self.current_view_name = name
        # 画面切り替え
        self.view_main.grid_forget()
        self.view_obs.grid_forget()
        self.view_hotkey.grid_forget()
        self.view_settings.grid_forget()
        self.view_help.grid_forget()

        # ナビゲーションのスタイル & アイコン更新
        nav_buttons = {
            "main": self.btn_nav_main,
            "obs": self.btn_nav_obs,
            "hotkey": self.btn_nav_hotkey,
            "settings": self.btn_nav_settings,
            "help": self.btn_nav_help,
        }
        for view_key, btn in nav_buttons.items():
            is_active = (view_key == name)
            fg = COLOR_SAGE_GREEN if is_active else "transparent"
            tc = "#FFFFFF" if is_active else COLOR_TEXT_MAIN
            fw = "bold" if is_active else "normal"
            img = None
            if self.nav_icons.get(view_key):
                img = self.nav_icons[view_key]["active" if is_active else "normal"]
            btn.configure(
                fg_color=fg, 
                text_color=tc, 
                font=ctk.CTkFont(family="Meiryo UI", size=13, weight=fw),
                image=img
            )

        if name == "main":
            self.view_main.grid(row=0, column=1, sticky="nsew")
        elif name == "obs":
            self.view_obs.grid(row=0, column=1, sticky="nsew")
        elif name == "hotkey":
            self.view_hotkey.grid(row=0, column=1, sticky="nsew")
        elif name == "settings":
            self.view_settings.grid(row=0, column=1, sticky="nsew")
        elif name == "help":
            self.view_help.grid(row=0, column=1, sticky="nsew")

    def apply_hotkeys(self):
        key_map = {
            "win": self.config.get("hotkey_win", "f7"),
            "loss": self.config.get("hotkey_loss", "f8"),
            "undo": self.config.get("hotkey_undo", "ctrl+shift+z"),
            "reset": self.config.get("hotkey_reset", "ctrl+shift+r")
        }
        enabled = self.config.get("hotkeys_enabled", True)
        self.hotkey_service.update_keys(key_map, enabled=enabled)

    def start_key_binding(self, action_id):
        # 既に割り当て中のものがあれば元に戻す
        if self.binding_action:
            self.cancel_key_binding()

        self.binding_action = action_id
        action_name = self.hk_action_labels.get(action_id, "")
        
        # ボタンの見た目を「キー入力待ち」に変更
        target_btn = self.hk_buttons.get(action_id)
        if target_btn:
            target_btn.configure(
                text="入力待ち...", fg_color="#D87A6E", hover_color="#C06357"
            )

        # ステータス案内を表示
        self.binding_status_lbl.configure(text=f'"{action_name}" を割り当て中... キーを押してください (ESCでキャンセル)')
        self.binding_status_frame.pack(fill="x", padx=20, pady=(10, 16))

        # 一時的にホットキーサービスを停止してキー衝突を防ぐ
        self.hotkey_service.stop()

        # Tkinterのキーイベントをバインド
        self.bind("<KeyPress>", self.on_key_press_detect)

    def cancel_key_binding(self):
        if not self.binding_action:
            return
        act_id = self.binding_action
        self.binding_action = None

        # ボタンを元のテキストに戻す
        target_btn = self.hk_buttons.get(act_id)
        if target_btn:
            cur_key = self.config.get(f"hotkey_{act_id}", "未設定").upper()
            target_btn.configure(
                text=cur_key, fg_color=COLOR_SAGE_GREEN, hover_color=COLOR_SAGE_HOVER
            )

        self.binding_status_frame.pack_forget()
        self.unbind("<KeyPress>")
        self.apply_hotkeys()

    def on_key_press_detect(self, event):
        if not self.binding_action:
            return

        key_sym = event.keysym.lower()
        # ESCでキャンセル
        if key_sym in ["escape", "esc"]:
            self.cancel_key_binding()
            self.log("キー割り当てをキャンセルしました")
            return

        # 修飾キー単体（Shift, Control, Alt）の時は決定せず待つ
        if key_sym in ["shift_l", "shift_r", "control_l", "control_r", "alt_l", "alt_r"]:
            return

        # 修飾キーの組み合わせ判定
        mods = []
        if event.state & 0x0004:  # Control
            mods.append("ctrl")
        if event.state & 0x0001:  # Shift
            mods.append("shift")
        if event.state & 0x20000 or event.state & 0x0008:  # Alt
            mods.append("alt")

        # キー名の正規化
        key_name = key_sym
        if key_name in ["prior"]: key_name = "pageup"
        elif key_name in ["next"]: key_name = "pagedown"
        elif key_name in ["return"]: key_name = "enter"
        
        # 組み合わせ
        if key_name not in mods:
            mods.append(key_name)
        
        final_hotkey = "+".join(mods)
        act_id = self.binding_action
        self.binding_action = None

        # 設定に反映して保存
        self.config[f"hotkey_{act_id}"] = final_hotkey
        save_config(self.config)

        # ボタンのテキストを更新
        target_btn = self.hk_buttons.get(act_id)
        if target_btn:
            target_btn.configure(
                text=final_hotkey.upper(), fg_color=COLOR_SAGE_GREEN, hover_color=COLOR_SAGE_HOVER
            )

        self.binding_status_frame.pack_forget()
        self.unbind("<KeyPress>")
        self.apply_hotkeys()
        
        action_name = self.hk_action_labels.get(act_id, "")
        self.log(f'"{action_name}" に "{final_hotkey.upper()}" を割り当てました！')

    def on_hotkey_toggle(self):
        self.config["hotkeys_enabled"] = self.switch_hk_enable.get() == 1
        self.apply_hotkeys()
        save_config(self.config)

    def on_hotkey_action(self, action):
        # スレッドセーフにTkinterメインループで実行
        if action == "win":
            self.after(0, lambda: self.on_manual_modify(win_delta=1, source="ショートカット"))
        elif action == "loss":
            self.after(0, lambda: self.on_manual_modify(loss_delta=1, source="ショートカット"))
        elif action == "undo":
            self.after(0, self.on_undo)
        elif action == "reset":
            self.after(0, self.confirm_reset)

    def on_manual_modify(self, win_delta=0, loss_delta=0, source="手動入力"):
        self.app_state.modify(win_delta=win_delta, loss_delta=loss_delta)
        if win_delta > 0:
            self.log(f"{source}: 勝利 (+1)")
        elif win_delta < 0:
            self.log(f"{source}: 勝利 (-1)")
        elif loss_delta > 0:
            self.log(f"{source}: 敗北 (+1)")
        elif loss_delta < 0:
            self.log(f"{source}: 敗北 (-1)")

    def on_undo(self):
        if self.app_state.undo():
            self.log("直前の操作を取り消しました")
        else:
            self.log("取り消せる履歴がありません")

    def confirm_reset(self):
        ans = messagebox.askyesno("リセットの確認", "勝敗カウントを「0勝0敗」にリセットしますか？")
        if ans:
            self.app_state.reset()
            self.log("カウントをリセットしました (0勝0敗)")

    def on_skin_change(self, choice):
        skin_id = self.skin_map.get(choice, "glassmorphism")
        self.app_state.skin = skin_id
        self.config["skin"] = skin_id
        save_config(self.config)
        self.log(f"OBSスキンを変更: {choice}")
        self.rebuild_color_controls()
        self.update_obs_preview()

    def rebuild_color_controls(self):
        skin = getattr(self.app_state, "skin", "glassmorphism")
        if not hasattr(self, "color_tiles_frame") or not hasattr(self, "preset_combo"):
            return

        # プリセットコンボボックスの更新
        skin_presets = self.config.get("skin_presets", {}).get(skin, {"デフォルト": {}})
        preset_names = list(skin_presets.keys())
        self.preset_combo.configure(values=preset_names)
        cur_preset = self.config.get("current_preset", {}).get(skin, "デフォルト")
        if cur_preset in preset_names:
            self.preset_combo.set(cur_preset)
        else:
            self.preset_combo.set("デフォルト")

        # タイル枠のクリア
        for child in self.color_tiles_frame.winfo_children():
            child.destroy()

        labels = SKIN_COLOR_LABELS.get(skin, [])
        cur_colors = self.config.get("skin_colors", {}).get(skin, {})

        # 2列グリッドで整列配置
        self.color_tiles_frame.grid_columnconfigure((0, 1), weight=1)
        for idx, (color_key, color_label) in enumerate(labels):
            row_idx = idx // 2
            col_idx = idx % 2

            item_frame = ctk.CTkFrame(self.color_tiles_frame, fg_color="transparent")
            item_frame.grid(row=row_idx, column=col_idx, padx=6, pady=4, sticky="w")

            ctk.CTkLabel(
                item_frame, text=f"{color_label}:",
                font=ctk.CTkFont(family="Meiryo UI", size=11),
                text_color=COLOR_TEXT_MAIN, width=82, anchor="w"
            ).pack(side="left")

            val_hex = cur_colors.get(color_key, "#FFFFFF")

            # 色プレビュー四角形ボタン
            btn = ctk.CTkButton(
                item_frame, text="", width=32, height=22, corner_radius=5,
                fg_color=val_hex, hover_color=val_hex,
                border_width=1, border_color=("#B0B8B2", "#505852"),
                command=lambda k=color_key, l=color_label: self.on_pick_color(k, l)
            )
            btn.pack(side="left", padx=(0, 6))

            lbl_hex = ctk.CTkLabel(
                item_frame, text=val_hex.upper(),
                font=ctk.CTkFont(family="Consolas", size=11),
                text_color=COLOR_TEXT_MUTED
            )
            lbl_hex.pack(side="left")

    def on_pick_color(self, key, label):
        skin = getattr(self.app_state, "skin", "glassmorphism")
        cur_hex = self.config.get("skin_colors", {}).get(skin, {}).get(key, "#FFFFFF")
        
        # Windowsカラーピッカーダイアログ
        color = colorchooser.askcolor(color=cur_hex, title=f"[{label}] の色を選択")
        if color and color[1]:
            chosen_hex = color[1].upper()
            if skin not in self.config["skin_colors"]:
                self.config["skin_colors"][skin] = {}
            self.config["skin_colors"][skin][key] = chosen_hex
            if "current_preset" not in self.config:
                self.config["current_preset"] = {}
            self.config["current_preset"][skin] = "カスタム"
            save_config(self.config)

            self.app_state.skin_colors = self.config["skin_colors"]
            self.rebuild_color_controls()
            self.update_obs_preview()
            self.log(f"カラー変更 [{label}]: {chosen_hex}")

    def on_save_preset(self):
        skin = getattr(self.app_state, "skin", "glassmorphism")
        dialog = ctk.CTkInputDialog(text="保存するプリセット名を入力してください:", title="プリセット保存")
        name = dialog.get_input()
        if not name:
            return
        name = name.strip()
        if not name or name == "デフォルト":
            messagebox.showwarning("プリセット保存", "「デフォルト」以外の有効な名前を入力してください。")
            return

        cur_colors = copy.deepcopy(self.config.get("skin_colors", {}).get(skin, {}))
        if "skin_presets" not in self.config:
            self.config["skin_presets"] = {}
        if skin not in self.config["skin_presets"]:
            self.config["skin_presets"][skin] = {}

        self.config["skin_presets"][skin][name] = cur_colors
        if "current_preset" not in self.config:
            self.config["current_preset"] = {}
        self.config["current_preset"][skin] = name
        save_config(self.config)

        self.rebuild_color_controls()
        self.log(f"プリセットを保存しました: {name}")
        messagebox.showinfo("プリセット保存", f"プリセット「{name}」を保存しました！")

    def on_preset_select(self, choice):
        skin = getattr(self.app_state, "skin", "glassmorphism")
        presets = self.config.get("skin_presets", {}).get(skin, {})
        if choice in presets:
            self.config["skin_colors"][skin] = copy.deepcopy(presets[choice])
            if "current_preset" not in self.config:
                self.config["current_preset"] = {}
            self.config["current_preset"][skin] = choice
            save_config(self.config)

            self.app_state.skin_colors = self.config["skin_colors"]
            self.rebuild_color_controls()
            self.update_obs_preview()
            self.log(f"プリセット適用: {choice}")

    def on_reset_preset(self):
        skin = getattr(self.app_state, "skin", "glassmorphism")
        defaults = get_default_colors(skin)
        self.config["skin_colors"][skin] = copy.deepcopy(defaults)
        if "current_preset" not in self.config:
            self.config["current_preset"] = {}
        self.config["current_preset"][skin] = "デフォルト"
        save_config(self.config)

        self.app_state.skin_colors = self.config["skin_colors"]
        self.rebuild_color_controls()
        self.update_obs_preview()
        self.log("配色をデフォルトに戻しました")

    def on_delete_preset(self):
        skin = getattr(self.app_state, "skin", "glassmorphism")
        cur_preset = self.preset_combo.get()
        if cur_preset == "デフォルト" or cur_preset == "カスタム":
            messagebox.showwarning("プリセット削除", "「デフォルト」は削除できません。")
            return
        ans = messagebox.askyesno("プリセット削除", f"プリセット「{cur_preset}」を削除しますか？")
        if ans:
            if cur_preset in self.config.get("skin_presets", {}).get(skin, {}):
                del self.config["skin_presets"][skin][cur_preset]
                self.config["current_preset"][skin] = "デフォルト"
                self.config["skin_colors"][skin] = copy.deepcopy(get_default_colors(skin))
                save_config(self.config)
                self.app_state.skin_colors = self.config["skin_colors"]
                self.rebuild_color_controls()
                self.update_obs_preview()
                self.log(f"プリセットを削除しました: {cur_preset}")

    def on_font_change(self, choice):
        self.app_state.font_family = choice
        self.config["font_family"] = choice
        save_config(self.config)
        self.log(f"OBSフォントを変更: {choice}")
        self.update_obs_preview()

    def on_size_change(self, value):
        val_int = int(value)
        self.app_state.font_size = val_int
        self.lbl_size_val.configure(text=f"{val_int}px")
        self.config["font_size"] = val_int
        save_config(self.config)
        self.update_obs_preview()

    def update_obs_preview(self):
        try:
            skin = getattr(self.app_state, "skin", "glassmorphism")
            wins = getattr(self.app_state, "wins", 0)
            losses = getattr(self.app_state, "losses", 0)
            font_family = getattr(self.app_state, "font_family", "Meiryo UI")
            font_size = getattr(self.app_state, "font_size", 58)
            cur_colors = self.config.get("skin_colors", {}).get(skin, {})

            pil_img = render_preview(
                skin=skin,
                wins=wins,
                losses=losses,
                font_family=font_family,
                font_size=font_size,
                width=480,
                height=110,
                colors=cur_colors
            )
            self.preview_ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(480, 110))
            if hasattr(self, "lbl_obs_preview"):
                self.lbl_obs_preview.configure(image=self.preview_ctk_img)
        except Exception as e:
            print(f"Preview render error: {e}")

    def on_theme_change(self, value):
        mode = "Dark" if "ダーク" in value else "Light"
        self.appearance_mode = mode.lower()
        ctk.set_appearance_mode(mode)
        self.config["appearance_mode"] = self.appearance_mode
        save_config(self.config)
        self.show_view(getattr(self, "current_view_name", "settings"))
        self.log(f"外観テーマを変更: {value}")

    def on_anim_toggle(self):
        self.app_state.animation_enabled = self.switch_anim.get() == 1
        self.config["animation_enabled"] = self.app_state.animation_enabled
        save_config(self.config)

    def on_auto_detect_toggle(self):
        self.app_state.auto_detect_enabled = self.switch_auto.get() == 1
        self.config["auto_detect_enabled"] = self.app_state.auto_detect_enabled
        save_config(self.config)
        self.log(f"自動検知: {'有効' if self.app_state.auto_detect_enabled else '無効'}")

    def on_monitor_change(self, choice):
        val = self.monitor_options.get(choice, "auto")
        self.app_state.target_monitor = val
        self.config["target_monitor"] = val
        save_config(self.config)
        self.log(f"監視モニターを変更: {choice}")

    def copy_obs_url(self):
        self.clipboard_clear()
        self.clipboard_append(self.obs_url)
        messagebox.showinfo("コピー完了", f"OBS用URLをクリップボードにコピーしました！\n{self.obs_url}")

    def on_detect_result(self, result_type, msg):
        self.after(0, lambda: self.log(msg))

    def log(self, text):
        self.log_label.configure(text=f"ログ: {text}")

    def update_ui_loop(self):
        # スコア反映
        score_text = f"{self.app_state.wins}勝 {self.app_state.losses}敗"
        if self.score_display.cget("text") != score_text:
            self.score_display.configure(text=score_text)
            self.update_obs_preview()

        # ステータス反映
        self.status_pill.configure(text=f"● {self.app_state.status_text}")

        # ヘルプファイルのホットリロード監視
        self.check_help_content_reload()

        # アップデート確認結果の反映 (スレッドセーフ)
        while hasattr(self, "update_result_queue") and not self.update_result_queue.empty():
            try:
                res, user_init = self.update_result_queue.get_nowait()
                self.on_update_result_received(res, user_initiated=user_init)
            except Exception:
                break

        self.after(100, self.update_ui_loop)

    def on_close(self):
        # 設定保存して安全に終了
        self.config["wins"] = self.app_state.wins
        self.config["losses"] = self.app_state.losses
        self.config["appearance_mode"] = getattr(self, "appearance_mode", "light")
        save_config(self.config)
        self.hotkey_service.stop()
        self.detector.stop()
        self.destroy()

if __name__ == "__main__":
    app = PekoScoreApp()
    app.mainloop()
