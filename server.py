import http.server
import socketserver
import json
import threading
import os

class StateHolder:
    def __init__(self):
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.history = []  # Undo履歴
        self.font_family = "Meiryo UI"
        self.font_size = 64
        self.text_color = "#FFFFFF"
        self.outline_color = "#222222"
        self.animation_enabled = True
        self.auto_detect_enabled = True
        self.status_text = "待機中"
        self.skin = "glassmorphism"  # glassmorphism, badge, ticket, simple
        self.skin_colors = {}
        self.target_monitor = "auto"  # "auto", 1, 2, ...
        self.lock = threading.Lock()

    def get_dict(self):
        with self.lock:
            return {
                "wins": self.wins,
                "losses": self.losses,
                "draws": self.draws,
                "skin": self.skin,
                "skin_colors": self.skin_colors,
                "font_family": self.font_family,
                "font_size": self.font_size,
                "text_color": self.text_color,
                "outline_color": self.outline_color,
                "animation_enabled": self.animation_enabled,
                "auto_detect_enabled": self.auto_detect_enabled,
                "status_text": self.status_text,
            }

    def modify(self, win_delta=0, loss_delta=0, draw_delta=0, record_history=True):
        with self.lock:
            if record_history:
                self.history.append((self.wins, self.losses, self.draws))
                if len(self.history) > 30:
                    self.history.pop(0)
            self.wins = max(0, self.wins + win_delta)
            self.losses = max(0, self.losses + loss_delta)
            self.draws = max(0, self.draws + draw_delta)

    def undo(self):
        with self.lock:
            if self.history:
                self.wins, self.losses, self.draws = self.history.pop()
                return True
            return False

    def reset(self):
        with self.lock:
            self.history.append((self.wins, self.losses, self.draws))
            self.wins = 0
            self.losses = 0
            self.draws = 0

class OBSServerHandler(http.server.SimpleHTTPRequestHandler):
    state_holder: StateHolder = None
    web_dir: str = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=self.web_dir, **kwargs)

    def do_GET(self):
        if self.path == "/api/state":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            data = json.dumps(self.state_holder.get_dict()).encode("utf-8")
            self.wfile.write(data)
        elif self.path == "/" or self.path == "/counter":
            self.path = "/index.html"
            return super().do_GET()
        else:
            return super().do_GET()

    def log_message(self, format, *args):
        # コンソールログを静音化
        pass

def get_resource_dir():
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def start_server(state_holder: StateHolder, port=8080):
    base_dir = get_resource_dir()
    web_dir = os.path.join(base_dir, "web")
    OBSServerHandler.state_holder = state_holder
    OBSServerHandler.web_dir = web_dir

    # ポートが使用中の場合は次を試す
    for p in range(port, port + 10):
        try:
            httpd = socketserver.TCPServer(("127.0.0.1", p), OBSServerHandler)
            t = threading.Thread(target=httpd.serve_forever, daemon=True)
            t.start()
            print(f"OBS Server started on http://127.0.0.1:{p}")
            return p
        except OSError:
            continue
    return None
