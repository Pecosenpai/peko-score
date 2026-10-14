"""
SE（効果音）再生サービス
pygame.mixer による非同期・音量調整付きの再生を提供。
万一 pygame が利用できない場合でも winsound に安全にフォールバックします。
"""
import os
import sys
import threading
from typing import Optional

def get_resource_dir():
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

# pygame.mixer 初期化 (遅延初期化で高速起動)
_mixer_initialized = False
_mixer_failed = False

def _init_mixer():
    global _mixer_initialized, _mixer_failed
    if _mixer_initialized or _mixer_failed:
        return
    try:
        import pygame
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        _mixer_initialized = True
    except Exception as e:
        print(f"pygame.mixer init failed: {e}")
        _mixer_failed = True

def get_default_sound_path(sound_type: str) -> str:
    """
    sound_type: 'victory', 'defeat', 'notify'
    """
    res_dir = get_resource_dir()
    candidate = os.path.join(res_dir, "sounds", f"{sound_type}.wav")
    if os.path.exists(candidate):
        return candidate
    local_candidate = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds", f"{sound_type}.wav")
    if os.path.exists(local_candidate):
        return local_candidate
    return ""

def play_sound(file_path: Optional[str] = None, sound_type: str = "notify", volume: float = 0.7):
    """
    指定の音声ファイルを再生。file_path がない場合は sound_type のデフォルト音を使用。
    volume: 0.0 〜 1.0
    別スレッドで非同期に実行されるためメインUIを止めません。
    """
    def _worker():
        target_path = file_path
        if not target_path or not os.path.exists(target_path):
            target_path = get_default_sound_path(sound_type)
            
        if not target_path or not os.path.exists(target_path):
            return

        clamped_volume = max(0.0, min(1.0, float(volume)))

        # 1. pygame.mixer で再生を試みる
        _init_mixer()
        if _mixer_initialized:
            try:
                import pygame
                sound = pygame.mixer.Sound(target_path)
                sound.set_volume(clamped_volume)
                sound.play()
                return
            except Exception as e:
                print(f"pygame playback failed: {e}")

        # 2. フォールバック: winsound (Windows標準, 音量変更は不可だが確実に鳴る)
        try:
            import winsound
            winsound.PlaySound(target_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as e:
            print(f"winsound fallback failed: {e}")

    threading.Thread(target=_worker, daemon=True).start()
