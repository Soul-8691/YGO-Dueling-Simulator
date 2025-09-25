import requests
import json
import os
import re

GOAT_JSON = "goat_format_cards.json"
IMG_DIR = "static/images/goat_cards"
os.makedirs(IMG_DIR, exist_ok=True)

# Function to sanitize filenames for Windows
def sanitize_name(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)

with open(GOAT_JSON, "r", encoding="utf-8") as f:
    goat_cards = json.load(f)

for card in goat_cards:
    card_name = card['name']
    safe_name = sanitize_name(card_name)

    # Fetch card info from API
    url = f"https://db.ygoprodeck.com/api/v7/cardinfo.php?name={card_name}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        images = data['data'][0].get('card_images', [])
    except Exception as e:
        print(f"Skipping {card_name}: {e}")
        continue

    card_dir = os.path.join(IMG_DIR, safe_name)
    try:
        os.makedirs(card_dir, exist_ok=True)
    except Exception as e:
        print(f"Skipping {card_name}: cannot create folder: {e}")
        continue

    for i, img in enumerate(images):
        path = os.path.join(card_dir, f"{i+1}.jpg")
        if os.path.exists(path):
            continue
        try:
            r = requests.get(img['image_url'])
            if r.status_code == 200:
                with open(path, "wb") as f:
                    f.write(r.content)
        except Exception as e:
            print(f"Failed to download {card_name} image {i+1}: {e}")