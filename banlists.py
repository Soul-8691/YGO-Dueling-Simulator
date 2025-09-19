import requests
import json

FORMATS_URL = "https://formatlibrary.com/api/formats/"
OUTPUT_FILE = "banlists_by_format.json"

# Map status to numbers
STATUS_MAP = {"forbidden": 0, "limited": 1, "semiLimited": 2}

result = {}

# 1. Fetch all formats
print("[*] Fetching formats...")
resp = requests.get(FORMATS_URL)
resp.raise_for_status()
formats = resp.json()
print(f"[+] Found {len(formats)} formats")

for f in formats:
    name = f.get("name")
    banlist_value = f.get("banlist").replace(' ', '%20')
    if not name or not banlist_value:
        continue

    print(f"[*] Processing format: {name} (banlist: {banlist_value})")
    banlist_url = f"https://formatlibrary.com/api/banlists/{banlist_value}"
    try:
        bl_resp = requests.get(banlist_url)
        bl_resp.raise_for_status()
        bl_data = bl_resp.json()
    except Exception as e:
        print(f"[!] Failed to fetch banlist for {name}: {e}")
        continue

    format_cards = {}
    for status, num in STATUS_MAP.items():
        for card in bl_data.get(status, []):
            card_name = card.get("cardName")
            if card_name:
                format_cards[card_name] = num

    result[name] = format_cards
    print(f"[+] Collected {len(format_cards)} cards for {name}")

# 2. Save to JSON
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"\n[***] Done! Results written to {OUTPUT_FILE}")
