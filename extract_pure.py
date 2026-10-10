import cv2
import numpy as np
import os

def create_pure_templates():
    samples_dir = r"C:\Users\sasas\.gemini\antigravity\scratch\ow-counter\samples"
    debug_dir = os.path.join(samples_dir, "debug")
    templates_dir = os.path.join(samples_dir, "templates")
    
    # DEFEAT_1は背景がほぼ真っ黒なので、輪郭が完璧にクリーン
    def_edge = cv2.imread(os.path.join(debug_dir, "edges_DEFEAT_1.jpg"), cv2.IMREAD_GRAYSCALE)
    # 中央の赤い横線ノイズを除去：文字の主輪郭のみ抽出
    # 輪郭検出 (findContours) で一定以上の面積の文字パーツだけを残す
    contours, _ = cv2.findContours(def_edge, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pure_def = np.zeros_like(def_edge)
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if h > 50 and w > 20: # 文字の高さ・幅フィルタ
            cv2.drawContours(pure_def, [c], -1, 255, 2)
            
    # VICTORYも同様に、内部・外部の大きな輪郭を抽出
    vic_edge = cv2.imread(os.path.join(debug_dir, "edges_VICTORY_1.jpg"), cv2.IMREAD_GRAYSCALE)
    contours_v, _ = cv2.findContours(vic_edge, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    pure_vic = np.zeros_like(vic_edge)
    for c in contours_v:
        x, y, w, h = cv2.boundingRect(c)
        # 文字の大きさ（高さ50px以上かつ縦横比が文字らしいもの）
        if 50 < h < 160 and 20 < w < 250:
            cv2.drawContours(pure_vic, [c], -1, 255, 2)
            
    cv2.imwrite(os.path.join(templates_dir, "pure_defeat.png"), pure_def)
    cv2.imwrite(os.path.join(templates_dir, "pure_victory.png"), pure_vic)
    print("Pure templates saved.")

if __name__ == "__main__":
    create_pure_templates()
