"""
PekoScore (ぺこすこあ) - 自動アップデート管理モジュール
GitHub Releases API を使用して最新バージョンの検出、ダウンロード、バトンタッチ再起動を行います。
"""

import os
import sys
import json
import time
import zipfile
import threading
import urllib.request
import subprocess
from typing import Callable, Optional, Dict, Any

CURRENT_VERSION = "1.0.1"
GITHUB_REPO = "Pecosenpai/peko-score"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

def parse_version(ver_str: str) -> tuple:
    """バージョン文字列 ('v1.0.1' や '1.0.0') を比較可能な数値タプルに変換"""
    clean_ver = ver_str.strip().lstrip("vV")
    parts = []
    for p in clean_ver.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)

def is_newer_version(latest_ver_str: str, current_ver_str: str = CURRENT_VERSION) -> bool:
    """latest が current より新しいバージョンかどうかを判定"""
    return parse_version(latest_ver_str) > parse_version(current_ver_str)

def check_for_updates_sync() -> Dict[str, Any]:
    """GitHub APIから同期的に最新リリース情報を取得"""
    req = urllib.request.Request(
        API_URL,
        headers={
            "User-Agent": "PekoScore-App",
            "Accept": "application/vnd.github.v3+json"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                tag_name = data.get("tag_name", "")
                release_name = data.get("name", tag_name)
                body = data.get("body", "更新内容はありません。")
                html_url = data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases")
                
                # zipアセットを探す (zipball_url をフォールバック)
                download_url = None
                for asset in data.get("assets", []):
                    if asset.get("name", "").endswith(".zip"):
                        download_url = asset.get("browser_download_url")
                        break
                
                if not download_url:
                    download_url = data.get("zipball_url")

                has_update = is_newer_version(tag_name, CURRENT_VERSION)
                return {
                    "success": True,
                    "has_update": has_update,
                    "current_version": CURRENT_VERSION,
                    "latest_version": tag_name,
                    "release_name": release_name,
                    "release_notes": body,
                    "download_url": download_url,
                    "html_url": html_url
                }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # リリースがまだ1件も作成されていない状態
            return {
                "success": True,
                "has_update": False,
                "current_version": CURRENT_VERSION,
                "latest_version": CURRENT_VERSION,
                "message": "最新のリリースはまだ登録されていません"
            }
        return {"success": False, "error": f"HTTPエラー: {e.code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_for_updates_async(callback: Callable[[Dict[str, Any]], None]):
    """バックグラウンドスレッドでアップデートを確認し、コールバックを呼ぶ"""
    def _worker():
        result = check_for_updates_sync()
        callback(result)
    
    t = threading.Thread(target=_worker, daemon=True)
    t.start()

def execute_baton_pass_update(zip_path: str, base_dir: str):
    """
    バトンタッチ用バッチファイルを作成し、自身を終了してファイルを置換・再起動する
    """
    temp_extract_dir = os.path.join(base_dir, "_update_extracted")
    os.makedirs(temp_extract_dir, exist_ok=True)
    
    # zip解凍
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # GitHubのzipballは最上位にリポジトリ名フォルダを含む場合があるため検出
        namelist = zip_ref.namelist()
        top_dirs = set(n.split('/')[0] for n in namelist if '/' in n)
        
        zip_ref.extractall(temp_extract_dir)

    # もし単一のルートフォルダに展開されていたら、その中身を昇格
    src_dir = temp_extract_dir
    sub_items = os.listdir(temp_extract_dir)
    if len(sub_items) == 1 and os.path.isdir(os.path.join(temp_extract_dir, sub_items[0])):
        src_dir = os.path.join(temp_extract_dir, sub_items[0])

    # config.json (ユーザー個人設定) は上書き除外
    user_config_in_src = os.path.join(src_dir, "config.json")
    if os.path.exists(user_config_in_src):
        try:
            os.remove(user_config_in_src)
        except Exception:
            pass

    # 起動コマンドの判定 (exeかpythonスクリプトか)
    is_frozen = getattr(sys, 'frozen', False)
    if is_frozen:
        exe_path = sys.executable
        relaunch_cmd = f'start "" "{exe_path}"'
    else:
        py_exe = sys.executable
        main_script = os.path.join(base_dir, "app.py")
        relaunch_cmd = f'start "" "{py_exe}" "{main_script}"'

    bat_path = os.path.join(base_dir, "_apply_update.bat")
    bat_content = f"""@echo off
chcp 65001 >nul
echo ぺこすこあ をアップデート中...
timeout /t 1 /nobreak >nul

:: ファイル置換 (config.json等は保護)
robocopy "{src_dir}" "{base_dir}" /E /XF config.json _apply_update.bat >nul

:: 一時ファイル削除
rd /s /q "{temp_extract_dir}" >nul 2>&1
del /f /q "{zip_path}" >nul 2>&1

:: 新バージョン再起動
{relaunch_cmd}

:: バッチ自身を削除
del "%~f0" >nul 2>&1
exit
"""
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat_content)

    # バックグラウンドでバッチ起動して自プロセス終了
    subprocess.Popen(
        ["cmd.exe", "/c", bat_path],
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        close_fds=True
    )
    sys.exit(0)

def download_and_install_update(
    download_url: str,
    base_dir: str,
    progress_callback: Optional[Callable[[float], None]] = None,
    on_error: Optional[Callable[[str], None]] = None
):
    """
    更新zipをダウンロードし、完了後にバトンタッチ実行
    """
    def _worker():
        try:
            zip_dest = os.path.join(base_dir, "_peko_update.zip")
            req = urllib.request.Request(
                download_url,
                headers={"User-Agent": "PekoScore-App"}
            )
            
            with urllib.request.urlopen(req, timeout=30) as resp, open(zip_dest, "wb") as out_file:
                total_size = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                block_size = 65536
                
                while True:
                    chunk = resp.read(block_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0 and progress_callback:
                        progress = downloaded / total_size
                        progress_callback(progress)
            
            if progress_callback:
                progress_callback(1.0)
            
            time.sleep(0.3)
            execute_baton_pass_update(zip_dest, base_dir)

        except Exception as e:
            if on_error:
                on_error(str(e))

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
