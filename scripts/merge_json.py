import json
from collections import defaultdict

# Input files
cards_file = "json/cards.json"
usage_stats_file = "json/usage_stats.json"
deck_types_file = "json/deck_types.json"

# Output file
output_file = "json/cards_updated.json"

# Load data
with open(cards_file, "r", encoding="utf-8") as f:
    cards_data = json.load(f)

with open(usage_stats_file, "r", encoding="utf-8") as f:
    usage_stats_data = json.load(f)

with open(deck_types_file, "r", encoding="utf-8") as f:
    deck_types_data = json.load(f)

# Dictionary to hold merged results
merged = {}

# Step 1: Insert cards.json data keyed by "name"
for card in cards_data:
    card_name = card["name"]

    # ---- Transform card_sets ----
    if "card_sets" in card and isinstance(card["card_sets"], list):
        set_map = defaultdict(list)
        for entry in card["card_sets"]:
            set_name = entry["set_name"]
            rarity = entry["set_rarity"]
            set_map[set_name].append(rarity)

        # If only one rarity, store string instead of list
        normalized_sets = {}
        for set_name, rarities in set_map.items():
            if len(rarities) == 1:
                normalized_sets[set_name] = rarities[0]
            else:
                normalized_sets[set_name] = rarities

        card["card_sets"] = normalized_sets

    merged[card_name] = card
    del merged[card_name]["name"]

# Step 2: Insert usage_stats.json data
for card_name, stats in usage_stats_data.items():
    if card_name not in merged:
        merged[card_name] = {}
    merged[card_name]["usage_stats"] = stats

# Step 3: Insert deck_types.json data
for deck_name, deck_cards in deck_types_data.items():
    for card_name, stats in deck_cards.items():
        if card_name not in merged:
            merged[card_name] = {}
        if "deck_types" not in merged[card_name]:
            merged[card_name]["deck_types"] = {}
        merged[card_name]["deck_types"][deck_name] = stats

# Step 4: Write to output file
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(merged, f, indent=2, ensure_ascii=False)

print(f"Merged JSON written to {output_file}")
