import cv2
import numpy as np
import os
import glob

class OWDetector:
    def __init__(self, templates_dir):
        # 基準テンプレートの保存
        self.vic_template = cv2.imread(os.path.join(templates_dir, "bright_VICTORY.png"), cv2.IMREAD_GRAYSCALE)
        self.def_template = cv2.imread(os.path.join(templates_dir, "bright_DEFEAT.png"), cv2.IMREAD_GRAYSCALE)
        self.ref_h, self.ref_w = 173, 999

    def extract_text_mask(self, img_bgr):
        h, w = img_bgr.shape[:2]
        # 中央ROI (Y: 42%~58%, X: 24%~76%)
        y1, y2 = int(h * 0.42), int(h * 0.58)
        x1, x2 = int(w * 0.24), int(w * 0.76)
        roi = img_bgr[y1:y2, x1:x2]
        
        # 基準サイズに正規化
        roi_resized = cv2.resize(roi, (self.ref_w, self.ref_h))
        
        # グレースケール & 輝度二値化
        # OWの文字は背景に関わらず輝度(V)が非常に高い (>=180)
        gray = cv2.cvtColor(roi_resized, cv2.COLOR_BGR2GRAY)
        
        # Otsuまたは固定しきい値(180)
        # 固定しきい値(170)で切り抜く
        _, mask = cv2.threshold(gray, 170, 255, cv2.THRESH_BINARY)
        
        # 小さな点ノイズを除去（モルフォロジー演算）
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        mask_clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        return mask_clean

    def detect(self, img_bgr):
        mask = self.extract_text_mask(img_bgr)
        
        # テンプレートマッチング (正規化相互相関: TM_CCOEFF_NORMED)
        res_vic = cv2.matchTemplate(mask, self.vic_template, cv2.TM_CCOEFF_NORMED)
        res_def = cv2.matchTemplate(mask, self.def_template, cv2.TM_CCOEFF_NORMED)
        
        score_vic = float(np.max(res_vic))
        score_def = float(np.max(res_def))
        
        # しきい値: 0.70以上で極めて高精度に判定
        THRESHOLD = 0.70
        detected = "NONE"
        if score_vic >= THRESHOLD and score_vic > score_def:
            detected = "VICTORY"
        elif score_def >= THRESHOLD and score_def > score_vic:
            detected = "DEFEAT"
            
        return {
            "result": detected,
            "score_victory": score_vic,
            "score_defeat": score_def
        }

if __name__ == "__main__":
    samples_dir = r"C:\Users\sasas\.gemini\antigravity\scratch\ow-counter\samples"
    debug_dir = os.path.join(samples_dir, "debug")
    templates_dir = os.path.join(samples_dir, "templates")
    
    # テンプレート保存
    vic_bright = cv2.imread(os.path.join(debug_dir, "bright_roi_VICTORY_2.jpg"), cv2.IMREAD_GRAYSCALE)
    def_bright = cv2.imread(os.path.join(debug_dir, "bright_roi_DEFEAT_1.jpg"), cv2.IMREAD_GRAYSCALE)
    cv2.imwrite(os.path.join(templates_dir, "bright_VICTORY.png"), vic_bright)
    cv2.imwrite(os.path.join(templates_dir, "bright_DEFEAT.png"), def_bright)
    
    detector = OWDetector(templates_dir)
    print("=== 判定テスト開始 ===")
    for img_path in glob.glob(os.path.join(samples_dir, "*.jpg")):
        filename = os.path.basename(img_path)
        img = cv2.imread(img_path)
        res = detector.detect(img)
        print(f"[{filename:14s}] => 判定: {res['result']:7s} | 勝利スコア: {res['score_victory']:.4f} | 敗北スコア: {res['score_defeat']:.4f}")
