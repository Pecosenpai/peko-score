import keyboard
import threading

class HotkeyService:
    def __init__(self, on_win=None, on_loss=None, on_undo=None, on_reset=None):
        self.on_win = on_win
        self.on_loss = on_loss
        self.on_undo = on_undo
        self.on_reset = on_reset
        
        self.registered_hooks = []
        self.enabled = True
        self.key_map = {
            "win": "f7",
            "loss": "f8",
            "undo": "ctrl+shift+z",
            "reset": "ctrl+shift+r"
        }

    def update_keys(self, key_map, enabled=True):
        self.key_map.update(key_map)
        self.enabled = enabled
        self.rebind_all()

    def rebind_all(self):
        # 既存のフックをすべて解除
        self.unbind_all()

        if not self.enabled:
            return

        # 新しいホットキーを登録
        def safe_add(key_str, callback):
            if not key_str or not key_str.strip():
                return
            try:
                hk = keyboard.add_hotkey(key_str.strip().lower(), callback, suppress=False)
                self.registered_hooks.append(hk)
            except Exception as e:
                print(f"Failed to bind hotkey '{key_str}': {e}")

        if self.on_win:
            safe_add(self.key_map.get("win"), self.on_win)
        if self.on_loss:
            safe_add(self.key_map.get("loss"), self.on_loss)
        if self.on_undo:
            safe_add(self.key_map.get("undo"), self.on_undo)
        if self.on_reset:
            safe_add(self.key_map.get("reset"), self.on_reset)

    def unbind_all(self):
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        self.registered_hooks.clear()

    def stop(self):
        self.unbind_all()
