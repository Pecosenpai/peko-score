from PIL import Image
import os

def create_ico():
    base_dir = r"C:\Users\sasas\.gemini\antigravity\scratch\ow-counter"
    png_path = os.path.join(base_dir, "icon.png")
    ico_path = os.path.join(base_dir, "icon.ico")
    
    img = Image.open(png_path)
    
    # Windows用マルチサイズアイコン（256, 128, 64, 48, 32, 16）
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(ico_path, format="ICO", sizes=sizes)
    print(f"Created {ico_path} successfully!")

if __name__ == "__main__":
    create_ico()
