import pygame
import tkinter as tk
from tkinter import messagebox
from PIL import Image
from io import BytesIO
import requests
import json
import random
import json
import os
from tkinter import filedialog, messagebox
import subprocess
import pathlib

# -----------------------------
# Load card data
# -----------------------------
with open('YGOProDeck_Card_Info.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

YGOProDeck_Card_Info = {c['name']: c for c in data['data']}

CARD_WIDTH, CARD_HEIGHT = 68, 98
SPACING = 10
PREVIEW_WIDTH, PREVIEW_HEIGHT = 375, 546
MAX_HAND = 17
CARD_WIDTH, CARD_HEIGHT = 68, 98
OPPONENT_HAND_Y = 0  # adjust if needed
HAND_START_X = 0  # starting x for leftmost slot
padding_x = 773
padding_y = 109
gap_x = 35
gap_y = 15

# -----------------------------
# Tkinter Card Selection Window
# -----------------------------
class CardSelectionWindow(tk.Toplevel):
    def __init__(self, master, callback):
        super().__init__(master)
        self.title("Select Cards")
        self.state("zoomed")  # Windows only; for cross-platform, see below
        self.callback = callback
        self.protocol("WM_DELETE_WINDOW", self.on_close)  # handle window close

        self.all_cards = sorted(YGOProDeck_Card_Info.keys())

        # --- Player frame ---
        player_frame = tk.Frame(self)
        player_frame.place(relx=0.025, rely=0.05, relwidth=0.45, relheight=0.85)

        tk.Label(player_frame, text="Select Player Cards (1–5)").place(relx=0.5, rely=0.02, anchor='n')

        self.player_search_var = tk.StringVar()
        self.player_search_var.trace_add("write", self.update_player_list)
        tk.Entry(player_frame, textvariable=self.player_search_var).place(relx=0.5, rely=0.08, anchor='n', relwidth=0.9)

        self.player_listbox = tk.Listbox(player_frame, selectmode=tk.MULTIPLE, exportselection=False)
        self.player_listbox.place(relx=0.05, rely=0.15, relwidth=0.9, relheight=0.8)

        for name in self.all_cards:
            self.player_listbox.insert(tk.END, name)

        # --- Opponent frame ---
        opponent_frame = tk.Frame(self)
        opponent_frame.place(relx=0.525, rely=0.05, relwidth=0.45, relheight=0.85)

        tk.Label(opponent_frame, text="Select Opponent Cards (1–5)").place(relx=0.5, rely=0.02, anchor='n')

        self.opponent_search_var = tk.StringVar()
        self.opponent_search_var.trace_add("write", self.update_opponent_list)
        tk.Entry(opponent_frame, textvariable=self.opponent_search_var).place(relx=0.5, rely=0.08, anchor='n', relwidth=0.9)

        self.opponent_listbox = tk.Listbox(opponent_frame, selectmode=tk.MULTIPLE, exportselection=False)
        self.opponent_listbox.place(relx=0.05, rely=0.15, relwidth=0.9, relheight=0.8)

        for name in self.all_cards:
            self.opponent_listbox.insert(tk.END, name)

        # --- Confirm button ---
        confirm_button = tk.Button(self, text="Confirm", command=self.confirm_selection)
        confirm_button.place(relx=0.5, rely=0.95, anchor='s')

    # --- Update listboxes dynamically ---
    def update_player_list(self, *args):
        search = self.player_search_var.get().lower()
        self.player_listbox.delete(0, tk.END)
        for name in self.all_cards:
            if search in name.lower():
                self.player_listbox.insert(tk.END, name)

    def update_opponent_list(self, *args):
        search = self.opponent_search_var.get().lower()
        self.opponent_listbox.delete(0, tk.END)
        for name in self.all_cards:
            if search in name.lower():
                self.opponent_listbox.insert(tk.END, name)

    # --- Confirm selection ---
    def confirm_selection(self):
        player_cards = [self.player_listbox.get(i) for i in self.player_listbox.curselection()]
        opponent_cards = [self.opponent_listbox.get(i) for i in self.opponent_listbox.curselection()]

        if not (1 <= len(player_cards) <= 5):
            tk.messagebox.showerror("Error", "Select between 1 and 5 Player cards")
            return
        if not (1 <= len(opponent_cards) <= 5):
            tk.messagebox.showerror("Error", "Select between 1 and 5 Opponent cards")
            return

        self.destroy()
        self.callback(player_cards, opponent_cards)

    # --- Exit program if user closes window ---
    def on_close(self):
        self.destroy()
        import sys
        sys.exit()  # ensures program exits

# -----------------------------
# Tkinter Draw Card Window
# -----------------------------
class DrawCardWindow(tk.Toplevel):
    def __init__(self, master, callback):
        super().__init__(master)
        self.title("Draw Cards")
        self.state("zoomed")  # Windows only; for cross-platform, see below
        self.callback = callback

        self.all_cards = sorted(YGOProDeck_Card_Info.keys())

        # --- Search entry ---
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.update_list)
        search_entry = tk.Entry(self, textvariable=self.search_var)
        search_entry.pack(padx=10, pady=5)

        # --- Listbox ---
        self.listbox = tk.Listbox(self, selectmode=tk.MULTIPLE, width=40, height=20)
        self.listbox.pack(padx=10, pady=5)

        for name in self.all_cards:
            self.listbox.insert(tk.END, name)

        # --- Confirm button ---
        tk.Button(self, text="Confirm", command=self.confirm).pack(pady=5)

    def update_list(self, *args):
        search = self.search_var.get().lower()
        self.listbox.delete(0, tk.END)
        for name in self.all_cards:
            if search in name.lower():
                self.listbox.insert(tk.END, name)

    def confirm(self):
        selected = [self.listbox.get(i) for i in self.listbox.curselection()]
        self.destroy()
        self.callback(selected)

# -----------------------------
# Pygame Simulator
# -----------------------------
class YGOSimulator:
    def __init__(self, player_deck_data, opponent_deck_data):
        pygame.init()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Yu-Gi-Oh! Simulator")
        self.screen_width, self.screen_height = self.screen.get_size()
        
        # Expand the deck dicts into flat lists for easier draw/remove logic
        self.player_deck = self._expand_deck(player_deck_data["main"])
        self.player_extra = self._expand_deck(player_deck_data["extra"])
        self.player_side = self._expand_deck(player_deck_data["side"])

        self.opponent_deck = self._expand_deck(opponent_deck_data["main"])
        self.opponent_extra = self._expand_deck(opponent_deck_data["extra"])
        self.opponent_side = self._expand_deck(opponent_deck_data["side"])
        self.player_deck_pos = (self.screen_width-CARD_WIDTH-14, self.screen_height//2 - CARD_HEIGHT//2 + CARD_HEIGHT*2 + gap_y*2)
        self.opponent_deck_pos = (padding_x-CARD_WIDTH-gap_x, self.screen_height//2 - CARD_HEIGHT//2 - CARD_HEIGHT*2 - gap_y*2)

        # Hand slot positions (17 slots)
        self.player_hand_slots = [(i*(CARD_WIDTH + SPACING),
                                self.screen_height - CARD_HEIGHT) for i in range(17)]
        self.opponent_hand_slots = [(i*(CARD_WIDTH + SPACING),
                                    0) for i in range(17)]

        self.next_uid = 0

        # Cards: dicts with name, owner, location
        self.cards = []

        # Shuffle decks so draw works randomly like in YGO
        import random
        random.shuffle(self.player_deck)
        random.shuffle(self.opponent_deck)

        # Draw 5 random cards from each deck as starting hand
        self.starting_hand_size = 5
        self.player_starting_hand = [self.player_deck.pop(0) for _ in range(self.starting_hand_size)]
        self.opponent_starting_hand = [self.opponent_deck.pop(0) for _ in range(self.starting_hand_size)]

        for name in self.player_starting_hand:
            inst = self._create_card_instance(name, owner="player", location="hand")
            self.cards.append(inst)

        for name in self.opponent_starting_hand:
            inst = self._create_card_instance(name, owner="opponent", location="hand")
            self.cards.append(inst)
        
        self.dragged_card_uid = None
        self.dragged_card_pos = (0,0)
        self.drag_offset = (0,0)

        # Life Points
        self.life_points = {"play": 8000, "opp": 8000}

        # Card surfaces
        self.card_surfaces = []
        self.card_rects = []
        self.card_preview_surfaces = []

        # Console
        self.console_font = pygame.font.SysFont(None, 18)
        self.console_text = ""
        self.console_history = []
        console_width, console_height = 150, 100
        self.console_rect = pygame.Rect(380, (self.screen_height - console_height)//2, console_width, console_height)

        # Load mat
        self.mat_surface = pygame.image.load("mat.jpg").convert()
        self.mat_surface = pygame.transform.scale(self.mat_surface, (self.screen_width, self.screen_height))

        # Load card back
        self.card_back_surface = pygame.image.load("card_back.png").convert_alpha()
        self.card_back_surface = pygame.transform.scale(self.card_back_surface, (CARD_WIDTH, CARD_HEIGHT))

        # Zones
        self.zones = self.create_zones()
        self.graveyard_zones = [
            pygame.Rect(padding_x-CARD_WIDTH-gap_x, self.screen_height//2 - CARD_HEIGHT//2 - CARD_HEIGHT - gap_y, CARD_WIDTH, CARD_HEIGHT),
            pygame.Rect(self.screen_width-CARD_WIDTH-14, self.screen_height//2 - CARD_HEIGHT//2 + CARD_HEIGHT + gap_y, CARD_WIDTH, CARD_HEIGHT)
        ]
        self.banish_zones = [
            pygame.Rect(padding_x-CARD_WIDTH-gap_x, self.screen_height//2 - CARD_HEIGHT//2, CARD_HEIGHT, CARD_WIDTH),
            pygame.Rect(self.screen_width-CARD_WIDTH-14-gap_x+5, self.screen_height//2 - CARD_HEIGHT//2 + gap_y + 10, CARD_HEIGHT, CARD_WIDTH)
        ]

        # Dragging
        self.dragged_card_index = None
        self.dragged_card_pos = (0,0)
        self.drag_offset = (0,0)

        self.load_cards()
        self.run()
    
    def _expand_deck(self, deck_dict):
        # turns {"Dark Magician": 3, "Blue-Eyes": 2} into
        # ["Dark Magician", "Dark Magician", "Dark Magician", "Blue-Eyes", "Blue-Eyes"]
        deck_list = []
        for name, count in deck_dict.items():
            deck_list.extend([name] * count)
        return deck_list
    
    def load_decks(self):
        """Load or build decks for both players."""
        messagebox.showinfo("Deck Setup", "Choose Player Deck")

        self.player_deck = self.ensure_deck_exists("Player")
        self.opponent_deck = self.ensure_deck_exists("Opponent")

        random.shuffle(self.player_deck)
        random.shuffle(self.opponent_deck)

    def ensure_deck_exists(self, who):
        """Make sure a deck exists for this player. Launch deckbuilder if needed."""
        decks_dir = pathlib.Path("decks")
        decks_dir.mkdir(exist_ok=True)

        file_path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialdir="decks",
            title=f"Select {who} Deck"
        )

        if not file_path:
            # Launch deckbuilder.py if no deck chosen
            messagebox.showinfo("Deckbuilder", f"No {who} deck selected. Opening Deckbuilder...")
            subprocess.run(["python", "deckbuilder.py"])
            # Ask again after building
            return self.ensure_deck_exists(who)

        with open(file_path, "r", encoding="utf-8") as f:
            deck_dict = json.load(f)

        # Expand dict into list of card names
        deck_list = []
        for card, count in deck_dict.items():
            deck_list.extend([card] * count)

        if not deck_list:
            messagebox.showerror("Error", f"{who} deck is empty! Rebuild it.")
            subprocess.run(["python", "deckbuilder.py"])
            return self.ensure_deck_exists(who)

        return deck_list

    def pick_deck(self):
        """Load a deck from JSON and expand into a shuffled list."""
        file_path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialdir="decks"
        )
        if not file_path:
            messagebox.showerror("Error", "No deck chosen! Exiting.")
            self.root.destroy()
            return []

        with open(file_path, "r", encoding="utf-8") as f:
            deck_dict = json.load(f)

        # Expand dict into list of card names
        deck_list = []
        for card, count in deck_dict.items():
            deck_list.extend([card] * count)

        if len(deck_list) < 1:
            messagebox.showerror("Error", "Deck is empty!")
            return []

        return deck_list

    def get_hand_positions(self, owner):
        """Return a list of 17 slot positions for a hand, left-to-right."""
        PLAYER_HAND_Y = self.screen_height - CARD_HEIGHT  # adjust if needed
        y = PLAYER_HAND_Y if owner == "player" else OPPONENT_HAND_Y
        return [(HAND_START_X + i*(CARD_WIDTH + SPACING), y) for i in range(MAX_HAND)]

    def drawplay(self, count=1):
        # Clamp count to available cards
        actual_count = min(count, len(self.player_deck))
        if actual_count < count:
            print(f"Player tried to draw {count}, but only {actual_count} available.")

        for _ in range(actual_count):
            card_name = self.player_deck.pop(0)
            inst = self._create_card_instance(card_name, owner="player", location="hand")
            self.cards.append(inst)

        self.load_cards()

    def drawopp(self, count=1):
        actual_count = min(count, len(self.opponent_deck))
        if actual_count < count:
            print(f"Opponent tried to draw {count}, but only {actual_count} available.")

        for _ in range(actual_count):
            card_name = self.opponent_deck.pop(0)
            inst = self._create_card_instance(card_name, owner="opponent", location="hand")
            self.cards.append(inst)

        self.load_cards()

    # -----------------------------
    # Helper: create a unique card instance (fetch images once)
    # -----------------------------
    def _create_card_instance(self, card_name, owner="player", location="hand"):
        if not hasattr(self, "next_uid"):
            self.next_uid = 0
        uid = self.next_uid
        self.next_uid += 1

        card_id = YGOProDeck_Card_Info[card_name]["id"]

        # Fetch surfaces
        surface_orig = self._fetch_surface_from_id(card_id, CARD_WIDTH, CARD_HEIGHT)
        preview = self._fetch_surface_from_id(card_id, PREVIEW_WIDTH, PREVIEW_HEIGHT)

        # Initial rect at 0,0 (will be repositioned in load_cards)
        rect = surface_orig.get_rect(topleft=(0,0))

        instance = {
            "uid": uid,
            "name": card_name,
            "id": card_id,
            "owner": owner,
            "location": location,
            "surface_orig": surface_orig,
            "surface": surface_orig,   # may rotate later if banished
            "preview": preview,
            "rect": rect,
        }

        # Rotate surface if banished
        if location == "banished":
            instance["surface"] = pygame.transform.rotate(surface_orig, 90)

        return instance

    def _fetch_surface_from_id(self, card_id, width, height):
        url = f"https://images.ygoprodeck.com/images/cards/{card_id}.jpg"
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content)).convert("RGBA")
        img = img.resize((width, height), Image.LANCZOS)
        mode = img.mode
        size = img.size
        data = img.tobytes()
        return pygame.image.fromstring(data, size, mode)

    # -----------------------------
    # Life points helper
    # -----------------------------
    def adjust_life_points(self, target, amount):
        if target not in self.life_points:
            print(f"Invalid LP target: {target}")
            return
        self.life_points[target] += amount
        if self.life_points[target] < 0:
            self.life_points[target] = 0

    # -----------------------------
    # Create 20 zones (2 rows of 5 per side)
    # -----------------------------
    def create_zones(self):
        self.player_field_zones = []
        self.opponent_field_zones = []

        # Player zones (bottom)
        start_y = self.screen_height - CARD_HEIGHT*2 - padding_y + 1 - gap_y
        for row in range(2):
            y = start_y + row*(CARD_HEIGHT + gap_y)
            for col in range(5):
                x = padding_x + col*(CARD_WIDTH + gap_x)
                self.player_field_zones.append(pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT))

        # Opponent zones (top)
        start_y = padding_y
        for row in range(2):
            y = start_y + row*(CARD_HEIGHT + gap_y)
            for col in range(5):
                x = padding_x + col*(CARD_WIDTH + gap_x)
                self.opponent_field_zones.append(pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT))

        return self.player_field_zones + self.opponent_field_zones  # old full list

    # -----------------------------
    # Fetch card surface wrapper (by name)
    # -----------------------------
    def fetch_card_surface(self, card_name, width, height):
        card_id = YGOProDeck_Card_Info[card_name]["id"]
        return self._fetch_surface_from_id(card_id, width, height)

    # -----------------------------
    # Load card surfaces
    # -----------------------------
    def load_cards(self):
        self.card_surfaces.clear()
        self.card_rects.clear()
        self.card_preview_surfaces.clear()

        # Starting positions for new hand cards
        player_x, player_y = 0, self.screen_height - CARD_HEIGHT
        opponent_x, opponent_y = 0, 0

        field_positions = self.zones

        for card in self.cards:
            # Always recalc rect if card is in graveyard or banished
            if card.get("rect") is not None and card.get("placed", False) and card["location"] in ("hand", "field"):
                self.card_surfaces.append(card["surface"])
                self.card_preview_surfaces.append(card["preview"])
                self.card_rects.append(card["rect"])
                continue

            surface = card.get("surface") or self.fetch_card_surface(card["name"], CARD_WIDTH, CARD_HEIGHT)
            preview = card.get("preview") or self.fetch_card_surface(card["name"], PREVIEW_WIDTH, PREVIEW_HEIGHT)

            if card["location"] == "hand":
                if card["owner"] == "player":
                    rect = surface.get_rect(topleft=(player_x, player_y))
                    player_x += CARD_WIDTH + SPACING
                else:
                    rect = surface.get_rect(topleft=(opponent_x, opponent_y))
                    opponent_x += CARD_WIDTH + SPACING
            elif card["location"] == "field":
                rect = pygame.Rect(0, 0, CARD_WIDTH, CARD_HEIGHT)
                
                # Select which zones to use based on owner
                if card["owner"] == "player":
                    zones_to_check = self.player_field_zones  # top/bottom depends on your layout
                else:
                    zones_to_check = self.opponent_field_zones

                # Iterate through the zones to find a free slot
                for zone in zones_to_check:
                    if not any(c["rect"].colliderect(zone) for c in self.cards if c["location"]=="field" and c["owner"]==card["owner"]):
                        rect.topleft = (zone.x, zone.y)
                        card["placed"] = True
                        break
            elif card["location"] == "graveyard":
                rect = surface.get_rect(
                    topleft=(self.graveyard_zones[0].x, self.graveyard_zones[0].y)
                    if card["owner"]=="player" else
                    (self.graveyard_zones[1].x, self.graveyard_zones[1].y)
                )
            elif card["location"] == "banished":
                rect = surface.get_rect(
                    topleft=(self.banish_zones[0].x, self.banish_zones[0].y)
                    if card["owner"]=="player" else
                    (self.banish_zones[1].x, self.banish_zones[1].y)
                )
                # Do NOT rotate here; rotation already handled on move
            else:
                # assign a default rect
                rect = pygame.Rect(0, 0, CARD_WIDTH, CARD_HEIGHT)

            card["rect"] = rect
            card["surface"] = surface
            card["preview"] = preview

            # Mark as placed only for hand/field cards
            if card["location"] in ("hand", "field"):
                card["placed"] = True

            self.card_surfaces.append(surface)
            self.card_preview_surfaces.append(preview)
            self.card_rects.append(rect)
        
        # Reposition hand cards in order
        for owner in ("player", "opponent"):
            hand_slots = self.player_hand_slots if owner=="player" else self.opponent_hand_slots
            hand_cards = [c for c in self.cards if c["owner"]==owner and c["location"]=="hand"]
            for i, card in enumerate(hand_cards):
                card["rect"].topleft = hand_slots[i]

    # -----------------------------
    # Draw everything
    # -----------------------------
    def draw_field(self, hover_index=None):
        self.screen.blit(self.mat_surface, (0,0))

        # Draw player hand slots
        for pos in self.player_hand_slots:
            pygame.draw.rect(self.screen, (50,50,50), (*pos, CARD_WIDTH, CARD_HEIGHT), 2)
        # Draw opponent hand slots
        for pos in self.opponent_hand_slots:
            pygame.draw.rect(self.screen, (50,50,50), (*pos, CARD_WIDTH, CARD_HEIGHT), 2)

        # Draw zones
        for zone in self.zones:
            pygame.draw.rect(self.screen, (100,100,100), zone, 2)
        for gy in self.graveyard_zones:
            pygame.draw.rect(self.screen, (150,0,0), gy, 2)
        for bz in self.banish_zones:
            pygame.draw.rect(self.screen, (0,0,150), bz, 2)

        # Highlight dragged over zone
        if self.dragged_card_uid is not None:
            for zone in self.zones:
                if zone.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(self.screen, (255,255,0), zone, 3)

        # Draw decks
        # Only show top 5 cards stacked slightly offset
        for i in range(min(5, len(self.player_deck))):
            offset = i * 0.5
            pos = (self.player_deck_pos[0] + offset, self.player_deck_pos[1] - offset)
            self.screen.blit(self.card_back_surface, pos)

        for i in range(min(5, len(self.opponent_deck))):
            offset = i * 0.5
            pos = (self.opponent_deck_pos[0] + offset, self.opponent_deck_pos[1] + offset)
            self.screen.blit(self.card_back_surface, pos)

        # Draw cards (non-dragged)
        for card in self.cards:
            if card.get("surface") is None or card.get("rect") is None:
                continue  # skip cards not fully initialized yet
            if card["uid"] != self.dragged_card_uid:
                self.screen.blit(card["surface"], card["rect"].topleft)

        # Draw dragged card on top
        if self.dragged_card_uid is not None:
            card = next((c for c in self.cards if c["uid"] == self.dragged_card_uid), None)
            if card is not None and card.get("surface") is not None:
                self.screen.blit(card["surface"], self.dragged_card_pos)

        # Card preview
        if hover_index is not None and hover_index < len(self.cards):
            preview_surface = self.cards[hover_index].get("preview")
            if preview_surface:
                preview_x = 0
                preview_y = (self.screen_height - PREVIEW_HEIGHT)//2
                self.screen.blit(preview_surface, (preview_x, preview_y))

        # Console
        pygame.draw.rect(self.screen, (50,50,50), self.console_rect)
        pygame.draw.rect(self.screen, (200,200,200), self.console_rect, 2)
        line_height = self.console_font.get_height() + 2
        max_history = self.console_rect.height // line_height - 1
        display_text = self.console_text
        max_width = self.console_rect.width - 10
        while self.console_font.size(display_text)[0] > max_width and len(display_text) > 0:
            display_text = display_text[1:]
        for i, cmd in enumerate(self.console_history[-max_history:]):
            txt_surf = self.console_font.render(cmd, True, (0,255,0))
            self.screen.blit(txt_surf, (self.console_rect.x+5, self.console_rect.y + i*line_height))
        txt_surf = self.console_font.render(display_text, True, (255,255,255))
        self.screen.blit(txt_surf, (self.console_rect.x+5, self.console_rect.y + self.console_rect.height - line_height))

        # Life Points
        lp_font = pygame.font.SysFont(None, 24)
        player_lp_text = lp_font.render(f"{self.life_points['play']}", True, (255,255,255))
        opponent_lp_text = lp_font.render(f"{self.life_points['opp']}", True, (255,255,255))
        self.screen.blit(player_lp_text, (self.screen_width - 700, self.screen_height//2 + 35))
        self.screen.blit(opponent_lp_text, (self.screen_width - 115, self.screen_height//2 - 50))

        pygame.display.flip()

    # -----------------------------
    # Select cards from current game state (hand + field) using Tkinter list
    # returns list of uids via callback
    # -----------------------------
    def select_cards_from_game_state(self, callback):
        # build display strings unique per instance (owner + name + uid)
        available = []
        display_map = {}
        for c in self.cards:
            if c["location"] in ("hand", "field"):
                owner_label = "Player" if c["owner"] == "player" else "Opponent"
                disp = f"{owner_label}: {c['name']} (uid:{c['uid']})"
                available.append(disp)
                display_map[disp] = c["uid"]

        if not available:
            return  # nothing to select

        def apply_selection(selected_display_list):
            # map back to uids and invoke callback
            selected_uids = [display_map[d] for d in selected_display_list if d in display_map]
            callback(selected_uids)

        root = tk.Tk()
        root.withdraw()
        draw_window = DrawCardWindow(root, apply_selection)
        # populate draw_window listbox with available display strings
        draw_window.listbox.delete(0, tk.END)
        for disp in available:
            draw_window.listbox.insert(tk.END, disp)
        root.wait_window(draw_window)
        root.destroy()

    # -----------------------------
    # Add cards from main deck to hand using GUI (for addhand play/opp)
    # -----------------------------
    def open_draw_window(self, side):
        deck_list = self.player_deck if side == "player" else self.opponent_deck
        if not deck_list:
            tk.messagebox.showinfo("Empty Deck", f"{side.capitalize()} deck is empty!")
            return

        class AddHandCardWindow(tk.Toplevel):
            def __init__(self, master, available_cards, callback):
                super().__init__(master)
                self.title(f"Add Cards to {side.capitalize()} Hand")
                self.callback = callback
                self.available_cards = available_cards.copy()

                tk.Label(self, text="Search Card:").grid(row=0, column=0, padx=5, pady=5)
                self.search_var = tk.StringVar()
                self.search_var.trace_add("write", self.update_list)
                self.search_entry = tk.Entry(self, textvariable=self.search_var)
                self.search_entry.grid(row=0, column=1, padx=5, pady=5)

                self.listbox = tk.Listbox(self, selectmode=tk.SINGLE, width=40, height=15)
                self.listbox.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
                self.update_list()

                tk.Label(self, text="Selected Cards:").grid(row=2, column=0, padx=5, pady=5)
                self.selected_listbox = tk.Listbox(self, width=40, height=10)
                self.selected_listbox.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

                self.selected_cards = []

                tk.Button(self, text="Add Card", command=self.add_card).grid(row=4, column=0, padx=5, pady=5)
                tk.Button(self, text="Confirm", command=self.confirm).grid(row=4, column=1, padx=5, pady=5)

            def update_list(self, *args):
                search = self.search_var.get().lower()
                self.listbox.delete(0, tk.END)
                for name in self.available_cards:
                    if search in name.lower():
                        self.listbox.insert(tk.END, name)

            def add_card(self):
                sel = self.listbox.curselection()
                if not sel:
                    tk.messagebox.showerror("Error", "Select a card from the list.")
                    return
                name = self.listbox.get(sel[0])
                self.selected_cards.append(name)
                self.selected_listbox.insert(tk.END, name)
                # Remove the card from available cards so it can't be added again
                self.available_cards.remove(name)
                self.update_list()

            def confirm(self):
                self.destroy()
                self.callback(self.selected_cards)

        def add_cards_to_hand(selected_names):
            hand_slots = [
                (padding_x + i*(CARD_WIDTH+SPACING), self.screen_height-CARD_HEIGHT if side=="player" else 0)
                for i in range(17)
            ]

            occupied_indices = [
                min(range(17), key=lambda i: abs(card["rect"].x - hand_slots[i][0]))
                for card in self.cards if card["owner"]==side and card["location"]=="hand"
            ]

            for name in selected_names:
                if name in deck_list:
                    deck_list.remove(name)
                free_index = next((i for i in range(17) if i not in occupied_indices), None)
                if free_index is None:
                    free_index = max(occupied_indices)+1 if occupied_indices else 0
                    if free_index >= 17:
                        free_index = 16
                slot_pos = hand_slots[free_index]
                inst = self._create_card_instance(name, owner=side, location="hand")
                inst["rect"].topleft = slot_pos
                self.cards.append(inst)
                occupied_indices.append(free_index)

            self.load_cards()

        root = tk.Tk()
        root.withdraw()
        draw_window = AddHandCardWindow(root, deck_list, add_cards_to_hand)
        root.wait_window(draw_window)
        root.destroy()

    def open_field_window(self, side):
        # --- Select the correct deck ---
        deck_cards = self.player_deck if side == "player" else self.opponent_deck
        if not deck_cards:
            tk.messagebox.showinfo("Info", f"No cards in {side}'s deck to place.")
            return

        class FieldPlacementWindow(tk.Toplevel):
            def __init__(self, master, available_cards, callback):
                super().__init__(master)
                self.title("Place Card on Field")
                self.callback = callback
                self.available_cards = sorted(available_cards)

                tk.Label(self, text="Search Card:").grid(row=0, column=0, padx=5, pady=5)
                self.search_var = tk.StringVar()
                self.search_var.trace_add("write", self.update_list)
                self.search_entry = tk.Entry(self, textvariable=self.search_var)
                self.search_entry.grid(row=0, column=1, padx=5, pady=5)

                self.listbox = tk.Listbox(self, selectmode=tk.SINGLE, width=40, height=15)
                self.listbox.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
                for name in self.available_cards:
                    self.listbox.insert(tk.END, name)

                tk.Label(self, text="Field Slot (1-10):").grid(row=2, column=0, padx=5, pady=5)
                self.slot_var = tk.IntVar(value=1)
                self.slot_entry = tk.Entry(self, textvariable=self.slot_var)
                self.slot_entry.grid(row=2, column=1, padx=5, pady=5)

                tk.Button(self, text="Confirm", command=self.confirm).grid(row=3, column=0, columnspan=2, padx=5, pady=5)

            def update_list(self, *args):
                search = self.search_var.get().lower()
                self.listbox.delete(0, tk.END)
                for name in self.available_cards:
                    if search in name.lower():
                        self.listbox.insert(tk.END, name)

            def confirm(self):
                sel = self.listbox.curselection()
                if not sel:
                    tk.messagebox.showerror("Error", "Select a card.")
                    return
                name = self.listbox.get(sel[0])
                slot_num = self.slot_var.get()
                if not (1 <= slot_num <= 10):
                    tk.messagebox.showerror("Error", "Slot must be 1-10.")
                    return
                self.available_cards.remove(name)  # prevent duplicates
                self.callback(name, slot_num, side)
                self.destroy()

        # -----------------------------
        # Callback to place the card on the field
        # -----------------------------
        def place_card_callback(name, slot_num, side):
            # Determine the correct zones array
            zones = self.player_field_zones if side == "player" else self.opponent_field_zones
            zone_index = slot_num - 1  # slot_num 1-10 -> index 0-9

            # Find the card in the deck
            for idx, card in enumerate(deck_cards):
                if card == name:
                    deck_card = deck_cards.pop(idx)
                    break
            else:
                tk.messagebox.showerror("Error", f"Card {name} not found in deck.")
                return

            # Create the card instance
            inst = self._create_card_instance(deck_card, owner=side, location="field")

            # Set the card rect to the correct field position
            target_zone = zones[zone_index]
            inst["rect"] = pygame.Rect(target_zone.x, target_zone.y, CARD_WIDTH, CARD_HEIGHT)
            inst["rect"].topleft = (target_zone.x, target_zone.y)
            inst["placed"] = True

            self.cards.append(inst)
            self.load_cards()  # updates hover and display

        # -----------------------------
        # Launch Tk window
        # -----------------------------
        root = tk.Tk()
        root.withdraw()
        win = FieldPlacementWindow(root, deck_cards, place_card_callback)
        root.wait_window(win)
        root.destroy()

    # -----------------------------
    # Move cards by uid to a new location
    # -----------------------------
    def move_cards_by_uid(self, uids, new_location):
        uid_set = set(uids)
        for c in self.cards:
            if c["uid"] in uid_set:
                c["location"] = new_location

                # Rotate if moving to banished
                if new_location == "banished":
                    c["surface"] = pygame.transform.rotate(c["surface_orig"], 90)
                else:
                    # Reset to normal for other locations
                    c["surface"] = c["surface_orig"]

        self.load_cards()

    # -----------------------------
    # Main loop
    # -----------------------------
    def run(self):
        running = True
        clock = pygame.time.Clock()
        while running:
            hover_index = None
            mouse_pos = pygame.mouse.get_pos()
            # find hover index by checking card rects (top-most first)
            for i in range(len(self.card_rects)-1, -1, -1):
                if self.card_rects[i].collidepoint(mouse_pos):
                    hover_index = i
                    break

            self.draw_field(hover_index)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_BACKSPACE:
                        self.console_text = self.console_text[:-1]
                    elif event.key == pygame.K_RETURN:
                        command = self.console_text.strip().split()
                        if not command:
                            continue

                        cmd = command[0].lower()
                        self.console_history.append(cmd)
                        arg = int(command[1]) if len(command) > 1 and command[1].isdigit() else 1
                        if cmd == "drawplay":
                            self.drawplay(arg)
                        elif cmd == "drawopp":
                            self.drawopp(arg)
                        elif cmd == "hand":
                            arg = 'player'
                            if command[1] == 'opp':
                                arg = 'opponent'
                            self.open_draw_window(arg)
                        elif cmd == "field":
                            arg = 'player'
                            if command[1] == 'opp':
                                arg = 'opponent'
                            self.open_field_window(arg)
                        elif cmd in ("gy", "graveyard"):
                            # open selection and move selected uids to graveyard
                            self.select_cards_from_game_state(lambda uids: self.move_cards_by_uid(uids, "graveyard"))
                        elif cmd in ("bz", "banish"):
                            self.select_cards_from_game_state(lambda uids: self.move_cards_by_uid(uids, "banished"))
                        elif cmd.startswith("lp "):
                            parts = cmd.split()
                            if len(parts) == 3:
                                target, change = parts[1], parts[2]
                                if target in ("play", "opp") and (change.startswith("+") or change.startswith("-")):
                                    try:
                                        amount = int(change)
                                        self.adjust_life_points(target, amount)
                                    except ValueError:
                                        print(f"Invalid LP amount: {change}")
                                else:
                                    print("Usage: lp [play|opp] [+/-number]")
                            else:
                                print("Usage: lp [play|opp] [+/-number]")
                        else:
                            print(f"Unknown command: {cmd}")
                        self.console_text = ""
                    else:
                        # add typed char
                        self.console_text += event.unicode

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for card in reversed(self.cards):  # topmost first
                        if card["rect"].collidepoint(event.pos):
                            self.dragged_card_uid = card["uid"]
                            self.drag_offset = (event.pos[0] - card["rect"].x, event.pos[1] - card["rect"].y)
                            self.dragged_card_pos = (card["rect"].x, card["rect"].y)
                            break
                    mx, my = event.pos
                    px, py = self.player_deck_pos
                    if px <= mx <= px + CARD_WIDTH and py <= my <= py + CARD_HEIGHT and self.player_deck:
                        self.drawplay(1)

                    ox, oy = self.opponent_deck_pos
                    if ox <= mx <= ox + CARD_WIDTH and oy <= my <= oy + CARD_HEIGHT and self.opponent_deck:
                        self.drawopp(1)

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.dragged_card_uid is not None:
                        card = next(c for c in self.cards if c["uid"] == self.dragged_card_uid)
                        snapped = False

                        # Snap to hand slots if dropped near them
                        if not snapped:
                            slots = self.player_hand_slots if card["owner"]=="player" else self.opponent_hand_slots

                            # Only pick free slots
                            occupied = [c["rect"].topleft for c in self.cards if c["location"]=="hand" and c["owner"]==card["owner"] and c["uid"]!=card["uid"]]
                            free_slots = [s for s in slots if s not in occupied]
                            
                            if free_slots:
                                # Snap to the nearest free slot
                                nearest_slot = min(free_slots, key=lambda s: (card["rect"].centerx - (s[0]+CARD_WIDTH//2))**2 +
                                                                        (card["rect"].centery - (s[1]+CARD_HEIGHT//2))**2)
                                card["rect"].topleft = nearest_slot
                                card["location"] = "hand"
                                snapped = True

                        # Snap to field
                        for zone in self.zones:
                            if zone.collidepoint(event.pos):
                                card["location"] = "field"
                                card["rect"].topleft = (zone.x, zone.y)
                                snapped = True
                                break

                        # When snapping to graveyard
                        for gy in self.graveyard_zones:
                            if gy.collidepoint(event.pos):
                                card["location"] = "graveyard"
                                card["rect"].topleft = gy.topleft
                                card["surface"] = card["surface_orig"]  # reset rotation
                                snapped = True
                                break

                        # When snapping to banish
                        for bz in self.banish_zones:
                            if bz.collidepoint(event.pos):
                                card["location"] = "banished"
                                card["rect"].topleft = bz.topleft
                                card["surface"] = pygame.transform.rotate(card["surface_orig"], 90)
                                snapped = True
                                break

                        # If moving to a normal zone (hand/field), reset rotation
                        if snapped and card["location"] != "banished":
                            card["surface"] = card["surface_orig"]

                        # Mark as placed manually
                        card["placed"] = True
                        self.dragged_card_uid = None

                elif event.type == pygame.MOUSEMOTION:
                    if self.dragged_card_uid is not None:
                        card = next(c for c in self.cards if c["uid"] == self.dragged_card_uid)
                        new_x = event.pos[0] - self.drag_offset[0]
                        new_y = event.pos[1] - self.drag_offset[1]
                        self.dragged_card_pos = (new_x, new_y)
                        card["rect"].topleft = self.dragged_card_pos  # optional live update

            clock.tick(30)

        pygame.quit()

from deckbuilder import build_deck_interactively
from sim import YGOSimulator  # your simulator class

def main():
    # Build/load decks
    print("Select Player Deck")
    player_deck_data = build_deck_interactively()
    print("Select Opponent Deck")
    opponent_deck_data = build_deck_interactively()

    # Start simulator
    sim = YGOSimulator(player_deck_data, opponent_deck_data)
    sim.run()

if __name__ == "__main__":
    main()
