from PIL import Image
import os
import numpy as np

def crop_and_make_transparent():
    base_dir = r"C:\Users\sasas\.gemini\antigravity\scratch\ow-counter"
    img_path = os.path.join(base_dir, "sidebar_icons.jpg")
    icons_dir = os.path.join(base_dir, "icons")
    os.makedirs(icons_dir, exist_ok=True)
    
    img = Image.open(img_path).convert("RGBA")
    w, h = img.size
    
    # 4分割のバウンディングボックス
    # 1: 左上 (Home), 2: 右上 (OBS / Video), 3: 左下 (Keyboard), 4: 右下 (Settings)
    quads = {
        "nav_main": (0, 0, w // 2, h // 2),
        "nav_obs": (w // 2, 0, w, h // 2),
        "nav_hotkey": (0, h // 2, w // 2, h),
        "nav_settings": (w // 2, h // 2, w, h)
    }
    
    for name, bbox in quads.items():
        crop = img.crop(bbox)
        arr = np.array(crop)
        
        # 白背景 (R, G, B すべて >= 240) を透過に変換
        r, g, b, a = arr[:,:,0], arr[:,:,1], arr[:,:,2], arr[:,:,3]
        white_mask = (r >= 238) & (g >= 238) & (b >= 238)
        
        # アルファ値を調整（エッジを滑らかに）
        arr[white_mask, 3] = 0
        
        # 非透過ピクセルのバウンディングボックスでさらにタイトにクロップ
        non_zero = np.where(arr[:,:,3] > 10)
        if len(non_zero[0]) > 0:
            ymin, ymax = np.min(non_zero[0]), np.max(non_zero[0])
            xmin, xmax = np.min(non_zero[1]), np.max(non_zero[1])
            pad = 8
            ymin = max(0, ymin - pad)
            ymax = min(arr.shape[0], ymax + pad)
            xmin = max(0, xmin - pad)
            xmax = min(arr.shape[1], xmax + pad)
            arr = arr[ymin:ymax, xmin:xmax]
            
        cropped_img = Image.fromarray(arr, "RGBA")
        # 正方形に整えてリサイズ
        max_dim = max(cropped_img.size)
        square = Image.new("RGBA", (max_dim, max_dim), (0, 0, 0, 0))
        offset = ((max_dim - cropped_img.width) // 2, (max_dim - cropped_img.height) // 2)
        square.paste(cropped_img, offset)
        
        # 64x64 で保存
        square_resized = square.resize((64, 64), Image.Resampling.LANCZOS)
        out_path = os.path.join(icons_dir, f"{name}.png")
        square_resized.save(out_path)
        print(f"Saved {out_path}")

if __name__ == "__main__":
    crop_and_make_transparent()
