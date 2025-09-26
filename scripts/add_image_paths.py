import json
import os
import re

GOAT_JSON = "json/cards.json"          # original JSON
UPDATED_JSON = "json/cards_updated.json" # output JSON
IMG_DIR = "static/img/card"

# Sanitize card names for Windows/Linux paths
def sanitize_name(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def main():
    if not os.path.exists(GOAT_JSON):
        print(f"Error: {GOAT_JSON} not found.")
        return

    with open(GOAT_JSON, "r", encoding="utf-8") as f:
        goat_cards = json.load(f)

    for card in goat_cards:
        card_name = sanitize_name(card['name'])
        local_images = []

        # Check how many images exist for this card
        card_dir = os.path.join(IMG_DIR, card_name)
        if os.path.exists(card_dir):
            images = sorted(os.listdir(card_dir))
            for i, img in enumerate(images, start=1):
                local_images.append(f"/static/img/card/{card_name}/{img}")

        # Add field to card JSON
        card['local_images'] = local_images

    # Save updated JSON
    with open(UPDATED_JSON, "w", encoding="utf-8") as f:
        json.dump(goat_cards, f, indent=4, ensure_ascii=False)

    print(f"Updated JSON saved as {UPDATED_JSON}")

if __name__ == "__main__":
    main()