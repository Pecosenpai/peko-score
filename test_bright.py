import cv2
import numpy as np
import os
import glob

def analyze_character_shapes():
    samples_dir = r"C:\Users\sasas\.gemini\antigravity\scratch\ow-counter\samples"
    debug_dir = os.path.join(samples_dir, "debug")
    
    # VICTORY: 'V', 'I', 'C', 'T', 'O', 'R', 'Y', '!'
    # DEFEAT: 'D', 'E', 'F', 'E', 'A', 'T'
    
    # 各画像の二値化・エッジ特性
    for name in ["roi_VICTORY_1.jpg", "roi_VICTORY_2.jpg", "roi_DEFEAT_1.jpg"]:
        path = os.path.join(debug_dir, name)
        img = cv2.imread(path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 文字の境界線（黒縁取り）を検出
        # 文字の内側は明度が高く、縁取りは真っ黒(0付近)
        # モルフォロジー勾配 (Morphological Gradient)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        grad = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel)
        
        # 黄色/文字色のマスク (HSV)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # 彩度 S > 50, 明度 V > 150 (色覚変更で色が変わっても「高輝度」であることは共通)
        # 高輝度マスク (白〜黄色〜シアン〜ピンク〜赤などUIの文字は常に高輝度)
        bright_mask = cv2.inRange(gray, 180, 255)
        
        cv2.imwrite(os.path.join(debug_dir, f"bright_{name}"), bright_mask)
        print(f"Processed {name}: bright pixels = {np.sum(bright_mask > 0)}")

if __name__ == "__main__":
    analyze_character_shapes()
