import os
from PIL import Image

def resize_images_in_folder(base_folder):
    for root, dirs, files in os.walk(base_folder):
        for file in files:
            if file.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")) and file != 'playmat.png' and file != 'card_back.png':
                file_path = os.path.join(root, file)
                try:
                    img = Image.open(file_path)
                    # Resize to 63x91 pixels
                    if '_cropped' in file:
                        new_size = (150, 150)
                    else:
                        new_size = (63, 91)
                    img_resized = img.resize(new_size, Image.LANCZOS)
                    
                    # Overwrite original file (or change if you want to save separately)
                    img_resized.save(file_path)
                    print(f"Resized: {file_path}")
                except Exception as e:
                    print(f"Error resizing {file_path}: {e}")

if __name__ == "__main__":
    base_folder = os.path.join(os.path.dirname(__file__), '../', "static", "img")
    resize_images_in_folder(base_folder)