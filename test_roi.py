import cv2
import numpy as np
import os
import glob

def test_crop_and_extract():
    samples_dir = r"C:\Users\sasas\.gemini\antigravity\scratch\ow-counter\samples"
    debug_dir = os.path.join(samples_dir, "debug")
    os.makedirs(debug_dir, exist_ok=True)
    
    images = glob.glob(os.path.join(samples_dir, "*.jpg"))
    print(f"Found {len(images)} images")

    for img_path in images:
        filename = os.path.basename(img_path)
        img = cv2.imread(img_path)
        h, w = img.shape[:2]
        
        # 画面中央の関心領域 (ROI: Region of Interest)
        # Y: 42% - 58%, X: 24% - 76% (アスペクト比非依存の相対割合)
        y1, y2 = int(h * 0.42), int(h * 0.58)
        x1, x2 = int(w * 0.24), int(w * 0.76)
        roi = img[y1:y2, x1:x2]
        
        # グレースケール変換
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # 文字部分は明るく、エッジが立っている。
        # 単純な大津の二値化 (Otsu) や 適応的二値化、Cannyエッジをテスト
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # エッジ
        edges = cv2.Canny(gray, 50, 150)
        
        # 保存して目視確認
        cv2.imwrite(os.path.join(debug_dir, f"roi_{filename}"), roi)
        cv2.imwrite(os.path.join(debug_dir, f"thresh_{filename}"), thresh)
        cv2.imwrite(os.path.join(debug_dir, f"edges_{filename}"), edges)
        
        print(f"Processed {filename}: shape={roi.shape}")

if __name__ == "__main__":
    test_crop_and_extract()
