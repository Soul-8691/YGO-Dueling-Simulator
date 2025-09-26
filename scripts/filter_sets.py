import json

# Load sets_info.json
with open("json/sets_info.json", "r", encoding="utf-8") as f:
    sets_data = json.load(f)

# Create a set of valid set names
valid_set_names = {s["Name"] for s in sets_data}

# Load cards_updated.json
with open("json/cards.json", "r", encoding="utf-8") as f:
    cards_data = json.load(f)

# Filter each card's card_sets
for card in cards_data:
    if "card_sets" in card:
        card["card_sets"] = [
            s for s in card["card_sets"] if s["set_name"] in valid_set_names
        ]

# Save back to a new file
with open("json/cards_filtered.json", "w", encoding="utf-8") as f:
    json.dump(cards_data, f, indent=4, ensure_ascii=False)
