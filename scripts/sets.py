import json

# Load the JSON file
with open("json/cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

sets_dict = {}

for card in cards:
    card_name = card["name"]
    for card_set in card.get("card_sets", []):
        set_name = card_set["set_name"]
        set_rarity = card_set["set_rarity"]
        
        # Make sure the set_name exists
        if set_name not in sets_dict:
            sets_dict[set_name] = {}
        
        # If the card is already in this set, handle rarity merging
        if card_name in sets_dict[set_name]:
            # Ensure rarity is a list
            if isinstance(sets_dict[set_name][card_name], list):
                if set_rarity not in sets_dict[set_name][card_name]:
                    sets_dict[set_name][card_name].append(set_rarity)
            else:
                if sets_dict[set_name][card_name] != set_rarity:
                    sets_dict[set_name][card_name] = [
                        sets_dict[set_name][card_name],
                        set_rarity
                    ]
        else:
            # Add first rarity
            sets_dict[set_name][card_name] = set_rarity

# Example output
print(json.dumps(sets_dict, indent=4))
