import time
import threading
import cv2
import numpy as np
import os
import mss
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

MONITOR_DEFAULTTONEAREST = 2

class RECT(ctypes.Structure):
    _fields_ = [
        ('left', ctypes.c_long),
        ('top', ctypes.c_long),
        ('right', ctypes.c_long),
        ('bottom', ctypes.c_long)
    ]

class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ('cbSize', wintypes.DWORD),
        ('rcMonitor', RECT),
        ('rcWork', RECT),
        ('dwFlags', wintypes.DWORD)
    ]

def get_overwatch_window():
    """Overwatchのウィンドウハンドルを取得"""
    hwnd = user32.FindWindowW("TankWindowClass", None)
    if hwnd:
        return hwnd
    hwnd = user32.FindWindowW(None, "Overwatch")
    if hwnd:
        return hwnd
    return None

def is_overwatch_running():
    return get_overwatch_window() is not None

def get_overwatch_monitor_rect():
    """Overwatchが存在するモニターの矩形 (left, top, width, height) を取得"""
    hwnd = get_overwatch_window()
    if not hwnd:
        return None

    hmonitor = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
    if not hmonitor:
        return None

    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(MONITORINFO)
    if user32.GetMonitorInfoW(hmonitor, ctypes.byref(mi)):
        left = mi.rcMonitor.left
        top = mi.rcMonitor.top
        width = mi.rcMonitor.right - mi.rcMonitor.left
        height = mi.rcMonitor.bottom - mi.rcMonitor.top
        return {"left": left, "top": top, "width": width, "height": height}
    return None

class AutoDetectorService:
    def __init__(self, state_holder, templates_dir, on_result_callback=None):
        self.state = state_holder
        self.templates_dir = templates_dir
        self.on_result = on_result_callback
        self.running = False
        self.thread = None
        
        # テンプレート読み込み
        vic_path = os.path.join(templates_dir, "bright_VICTORY.png")
        def_path = os.path.join(templates_dir, "bright_DEFEAT.png")
        
        self.vic_template = cv2.imread(vic_path, cv2.IMREAD_GRAYSCALE)
        self.def_template = cv2.imread(def_path, cv2.IMREAD_GRAYSCALE)
        self.ref_h, self.ref_w = 173, 999
        
        # クールダウン管理 (秒)
        self.cooldown_seconds = 25.0
        self.last_detected_time = 0.0

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _loop(self):
        with mss.mss() as sct:
            while self.running:
                try:
                    if not self.state.auto_detect_enabled:
                        self.state.status_text = "自動検知: 一時停止中"
                        time.sleep(1.0)
                        continue

                    # 1. Overwatch起動チェック
                    if not is_overwatch_running():
                        self.state.status_text = "ゲーム未起動 (待機中)"
                        time.sleep(1.5)
                        continue

                    # 2. クールダウン中か判定
                    elapsed = time.time() - self.last_detected_time
                    if elapsed < self.cooldown_seconds:
                        remain = int(self.cooldown_seconds - elapsed)
                        self.state.status_text = f"クールダウン中 ({remain}s)"
                        time.sleep(0.5)
                        continue

                    self.state.status_text = "監視中 (Overwatch 2)"

                    # 3. キャプチャ対象モニターの矩形を特定
                    # target_monitor: "auto", 1, 2, ...
                    target_mode = getattr(self.state, "target_monitor", "auto")
                    mon_rect = None

                    if target_mode == "auto":
                        mon_rect = get_overwatch_monitor_rect()
                    elif isinstance(target_mode, int) and 1 <= target_mode < len(sct.monitors):
                        mon = sct.monitors[target_mode]
                        mon_rect = {"left": mon["left"], "top": mon["top"], "width": mon["width"], "height": mon["height"]}

                    # フォールバック (取得できない場合はプライマリモニター)
                    if not mon_rect and len(sct.monitors) > 1:
                        mon = sct.monitors[1]
                        mon_rect = {"left": mon["left"], "top": mon["top"], "width": mon["width"], "height": mon["height"]}

                    if not mon_rect:
                        time.sleep(1.0)
                        continue

                    # ROI (画面中央帯 Y: 42%~58%, X: 24%~76%)
                    y1 = int(mon_rect["top"] + mon_rect["height"] * 0.42)
                    y2 = int(mon_rect["top"] + mon_rect["height"] * 0.58)
                    x1 = int(mon_rect["left"] + mon_rect["width"] * 0.24)
                    x2 = int(mon_rect["left"] + mon_rect["width"] * 0.76)

                    bbox = {"top": y1, "left": x1, "width": x2 - x1, "height": y2 - y1}
                    sct_img = sct.grab(bbox)
                    img = np.array(sct_img)  # BGRA
                    img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                    # 4. 判定
                    res = self._check_frame(img_bgr)
                    if res in ["VICTORY", "DEFEAT"]:
                        self.last_detected_time = time.time()
                        if res == "VICTORY":
                            self.state.modify(win_delta=1)
                            msg = "勝利 (VICTORY) を自動検知！(+1)"
                        else:
                            self.state.modify(loss_delta=1)
                            msg = "敗北 (DEFEAT) を自動検知！(+1)"

                        if self.on_result:
                            self.on_result(res, msg)

                    time.sleep(0.5)

                except Exception as e:
                    time.sleep(1.0)

    def _check_frame(self, img_bgr):
        roi_resized = cv2.resize(img_bgr, (self.ref_w, self.ref_h))
        gray = cv2.cvtColor(roi_resized, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 170, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        mask_clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        res_vic = cv2.matchTemplate(mask_clean, self.vic_template, cv2.TM_CCOEFF_NORMED)
        res_def = cv2.matchTemplate(mask_clean, self.def_template, cv2.TM_CCOEFF_NORMED)

        score_vic = float(np.max(res_vic))
        score_def = float(np.max(res_def))

        THRESHOLD = 0.75
        if score_vic >= THRESHOLD and score_vic > (score_def + 0.15):
            return "VICTORY"
        elif score_def >= THRESHOLD and score_def > (score_vic + 0.15):
            return "DEFEAT"
        return "NONE"
