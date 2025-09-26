import requests
import json

# -----------------------------
# Config
# -----------------------------
API_URL = "https://db.ygoprodeck.com/api/v7/cardinfo.php"
OUTPUT_FILE = "json/cards.json"

# Fields to keep
FIELDS_TO_KEEP = [
    "id",
    "name",
    "type",
    "desc",
    "atk",
    "def",
    "level",
    "race",
    "attribute",
    "card_sets",
    "banlist_info"  # Banlist info included if needed
]

# -----------------------------
# Fetch GOAT format cards from API
# -----------------------------
params = {
    "format": "goat",  # Only cards legal in GOAT format
    "misc": "yes"
}

response = requests.get(API_URL, params=params)
if response.status_code != 200:
    raise Exception(f"API request failed with status code {response.status_code}")

all_cards = response.json().get("data", [])

# -----------------------------
# Keep only relevant fields
# -----------------------------
cleaned_cards = []
for card in all_cards:
    cleaned_card = {field: card.get(field, None) for field in FIELDS_TO_KEEP}
    # Optional: Add a simple "status" field based on banlist_info
    banlist = card.get("banlist_info", {}).get("ban_tcg", "Unlimited")
    cleaned_card["status"] = banlist
    del cleaned_card["banlist_info"]
    cleaned_cards.append(cleaned_card)

# -----------------------------
# Save to JSON
# -----------------------------
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(cleaned_cards, f, indent=4, ensure_ascii=False)

print(f"Saved {len(cleaned_cards)} GOAT format cards to {OUTPUT_FILE}")