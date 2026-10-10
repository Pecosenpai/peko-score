import cv2
import numpy as np
import os
import glob

def create_templates():
    samples_dir = r"C:\Users\sasas\.gemini\antigravity\scratch\ow-counter\samples"
    debug_dir = os.path.join(samples_dir, "debug")
    templates_dir = os.path.join(samples_dir, "templates")
    os.makedirs(templates_dir, exist_ok=True)
    
    # VICTORY_1 から "VICTORY!" の文字マスク/テンプレートを作成
    # DEFEAT_1 から "DEFEAT" の文字マスク/テンプレートを作成
    vic_roi = cv2.imread(os.path.join(debug_dir, "roi_VICTORY_1.jpg"))
    def_roi = cv2.imread(os.path.join(debug_dir, "roi_DEFEAT_1.jpg"))
    
    # HSV空間で黄色の抽出 (H: 20~40, S: 100~255, V: 150~255)
    # または グレースケールで文字輪郭抽出
    # 色覚設定で黄色以外になっても対応できるよう、エッジ画像をテンプレート化する
    vic_gray = cv2.cvtColor(vic_roi, cv2.COLOR_BGR2GRAY)
    def_gray = cv2.cvtColor(def_roi, cv2.COLOR_BGR2GRAY)
    
    vic_edge = cv2.Canny(vic_gray, 50, 150)
    def_edge = cv2.Canny(def_gray, 50, 150)
    
    cv2.imwrite(os.path.join(templates_dir, "template_victory_edge.png"), vic_edge)
    cv2.imwrite(os.path.join(templates_dir, "template_defeat_edge.png"), def_edge)
    
    # また、文字部分そのもののグレースケールも保存
    cv2.imwrite(os.path.join(templates_dir, "template_victory_gray.png"), vic_gray)
    cv2.imwrite(os.path.join(templates_dir, "template_defeat_gray.png"), def_gray)
    print("Templates created successfully.")

if __name__ == "__main__":
    create_templates()
