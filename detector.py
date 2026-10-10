import cv2
import numpy as np
import os
import glob

def clean_template(edge_img, text_type="victory"):
    # 文字部分だけを綺麗に残すため、文字の周辺領域のみをクロップ
    h, w = edge_img.shape
    # 文字の中心帯域 (Y: 上下20%カット)
    mask = np.zeros_like(edge_img)
    mask[int(h*0.15):int(h*0.85), int(w*0.05):int(w*0.95)] = 255
    cleaned = cv2.bitwise_and(edge_img, mask)
    return cleaned

class ResultDetector:
    def __init__(self, templates_dir):
        # テンプレート読み込み
        self.vic_template = cv2.imread(os.path.join(templates_dir, "template_victory_edge.png"), cv2.IMREAD_GRAYSCALE)
        self.def_template = cv2.imread(os.path.join(templates_dir, "template_defeat_edge.png"), cv2.IMREAD_GRAYSCALE)
        
        # 不要な背景ノイズを削る（DEFEATの中央文字領域、VICTORYの文字領域）
        # DEFEATは左右に余裕がある
        self.h_ref, self.w_ref = self.vic_template.shape
        
    def detect(self, image_bgr):
        h, w = image_bgr.shape[:2]
        
        # 1. 画面中央の切り抜き (16:9/16:10共通の相対比率)
        y1, y2 = int(h * 0.42), int(h * 0.58)
        x1, x2 = int(w * 0.24), int(w * 0.76)
        roi = image_bgr[y1:y2, x1:x2]
        
        # 2. リファレンス解像度 (基準サイズ) にリサイズ
        roi_resized = cv2.resize(roi, (self.w_ref, self.h_ref))
        
        # 3. エッジ抽出 (色に依存しない)
        gray = cv2.cvtColor(roi_resized, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # 4. テンプレートマッチング (エッジ同士の相関スコア)
        res_vic = cv2.matchTemplate(edges, self.vic_template, cv2.TM_CCOEFF_NORMED)
        res_def = cv2.matchTemplate(edges, self.def_template, cv2.TM_CCOEFF_NORMED)
        
        score_vic = np.max(res_vic)
        score_def = np.max(res_def)
        
        result = "NONE"
        # スコア判定
        if score_vic > 0.40 and score_vic > score_def:
            result = "VICTORY"
        elif score_def > 0.40 and score_def > score_vic:
            result = "DEFEAT"
            
        return {
            "result": result,
            "score_victory": float(score_vic),
            "score_defeat": float(score_def)
        }

if __name__ == "__main__":
    templates_dir = r"C:\Users\sasas\.gemini\antigravity\scratch\ow-counter\samples\templates"
    detector = ResultDetector(templates_dir)
    
    samples_dir = r"C:\Users\sasas\.gemini\antigravity\scratch\ow-counter\samples"
    for img_path in glob.glob(os.path.join(samples_dir, "*.jpg")):
        filename = os.path.basename(img_path)
        img = cv2.imread(img_path)
        res = detector.detect(img)
        print(f"[{filename}] => 判定結果: {res['result']} (勝スコア: {res['score_victory']:.3f}, 敗スコア: {res['score_defeat']:.3f})")
