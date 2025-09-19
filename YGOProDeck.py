import json

# Load existing card info from YGOProDeck
with open('YGOProDeck_Card_Info.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

card_info = {}
for cdata in data['data']:
    card_info[cdata['name']] = cdata

# Load your existing cards_by_format.json
with open('cards_by_format.json', 'r', encoding='utf-8') as f:
    cards_by_format = json.load(f)

# Update each card with main/extra info
for fmt_name, cards in cards_by_format.items():
    for card_name in list(cards.keys()):
        ctype = card_info.get(card_name, {}).get('type', '')
        if ctype in ("Fusion Monster", "XYZ Monster", "Synchro Monster", "Link Monster", "Pendulum Effect Fusion Monster", "XYZ Pendulum Effect Monster", "Synchro Pendulum Effect Monster"):
            cards[card_name] = {"count": cards[card_name], "location": "extra"}
        else:
            cards[card_name] = {"count": cards[card_name], "location": "main"}

# Save the updated JSON
with open('cards_by_format_updated.json', 'w', encoding='utf-8') as f:
    json.dump(cards_by_format, f, indent=2, ensure_ascii=False)

print("cards_by_format_updated.json updated with main/extra info!")
