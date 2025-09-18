import pygame
import tkinter as tk
from tkinter import messagebox
from PIL import Image
from io import BytesIO
import requests
import json

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
    def __init__(self, player_cards, opponent_cards):
        pygame.init()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Yu-Gi-Oh! Simulator")
        self.screen_width, self.screen_height = self.screen.get_size()

        # card instances: each card is a dict (unique instance)
        # fields: uid, name, id, owner ('player'/'opponent'), location ('hand','field','graveyard','banished'),
        #         surface_orig (PIL->pygame surface unrotated), surface (pygame surface currently used), preview (pygame),
        #         rect (pygame.Rect)
        self.cards = []
        self.next_uid = 1

        # initialize card instances from provided lists (each name becomes its own instance)
        for name in player_cards:
            self.cards.append(self._create_card_instance(name, owner="player", location="hand"))
        for name in opponent_cards:
            self.cards.append(self._create_card_instance(name, owner="opponent", location="hand"))

        # Life points for both players (keeps your existing keys 'play' and 'opp')
        self.life_points = {"play": 8000, "opp": 8000}

        # drawing caches (kept in sync by load_cards)
        self.card_surfaces = []        # parallel to self.card_rects (for drawing)
        self.card_rects = []
        self.card_preview_surfaces = []

        # Console settings
        self.console_font = pygame.font.SysFont(None, 18)
        self.console_text = ""
        self.console_history = []
        console_width, console_height = 150, 100
        self.console_rect = pygame.Rect(
            380,
            (self.screen_height - console_height)//2,
            console_width,
            console_height
        )

        # Load mat background
        self.mat_surface = pygame.image.load("mat.jpg").convert()
        self.mat_surface = pygame.transform.scale(self.mat_surface, (self.screen_width, self.screen_height))

        # Zones
        self.zones = self.create_zones()

        # Graveyard & banish zones (keep your placement)
        self.graveyard_zones = [
            pygame.Rect(self.screen_width - CARD_WIDTH - 14, self.screen_height//2 - CARD_HEIGHT//2 + CARD_HEIGHT + gap_y, CARD_WIDTH, CARD_HEIGHT),  # Player
            pygame.Rect(padding_x - CARD_WIDTH - gap_x, self.screen_height//2 - CARD_HEIGHT//2 - CARD_HEIGHT - gap_y, CARD_WIDTH, CARD_HEIGHT),  # Opponent
        ]
        # Note: banish zone rects store width,height swapped intentionally previously; we'll keep them sensible (width= CARD_WIDTH, height=CARD_HEIGHT)
        self.banish_zones = [
            pygame.Rect(self.screen_width - CARD_WIDTH - 14 - gap_x + 5, self.screen_height//2 - CARD_HEIGHT//2 + gap_y + 10, CARD_HEIGHT, CARD_WIDTH),  # Player
            pygame.Rect(padding_x - CARD_WIDTH - gap_x, self.screen_height//2 - CARD_HEIGHT//2, CARD_HEIGHT, CARD_WIDTH),  # Opponent
        ]

        # Drag state
        self.dragged_card = None      # reference to card dict being dragged
        self.dragged_card_index = None
        self.dragged_card_pos = (0, 0)
        self.drag_offset = (0, 0)

        # initial layout
        self.load_cards()
        self.run()

    # -----------------------------
    # Helper: create a unique card instance (fetch images once)
    # -----------------------------
    def _create_card_instance(self, card_name, owner="player", location="hand"):
        uid = self.next_uid
        self.next_uid += 1
        card_id = YGOProDeck_Card_Info[card_name]["id"]
        # fetch surfaces once and store original (unrotated)
        surface_orig = self._fetch_surface_from_id(card_id, CARD_WIDTH, CARD_HEIGHT)
        preview = self._fetch_surface_from_id(card_id, PREVIEW_WIDTH, PREVIEW_HEIGHT)
        # initial surface equals orig, rotation handled later based on location
        instance = {
            "uid": uid,
            "name": card_name,
            "id": card_id,
            "owner": owner,
            "location": location,
            "surface_orig": surface_orig,
            "surface": surface_orig,   # may be rotated copy
            "preview": preview,
            "rect": surface_orig.get_rect(topleft=(0, 0)),
        }
        # if initially banished, rotate surface
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
        zones = []
        # Player zones (bottom)
        start_y = self.screen_height - CARD_HEIGHT*2 - padding_y + 1 - gap_y
        for row in range(2):
            y = start_y + row*(CARD_HEIGHT + gap_y)
            for col in range(5):
                x = padding_x + col*(CARD_WIDTH + gap_x)
                zones.append(pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT))
        # Opponent zones (top)
        start_y = padding_y
        for row in range(2):
            y = start_y + row*(CARD_HEIGHT + gap_y)
            for col in range(5):
                x = padding_x + col*(CARD_WIDTH + gap_x)
                zones.append(pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT))
        return zones

    # -----------------------------
    # Fetch card surface wrapper (by name)
    # -----------------------------
    def fetch_card_surface(self, card_name, width, height):
        card_id = YGOProDeck_Card_Info[card_name]["id"]
        return self._fetch_surface_from_id(card_id, width, height)

    # -----------------------------
    # Load card positions and drawing arrays
    # -----------------------------
    def load_cards(self):
        # Recompute surfaces/rects lists in same order as self.cards
        self.card_surfaces.clear()
        self.card_rects.clear()
        self.card_preview_surfaces.clear()

        # Hand layout positions
        player_x, player_y = 0, self.screen_height - CARD_HEIGHT
        opponent_x, opponent_y = 0, 0

        # track which zones are occupied (so we snap cards to empty zone)
        occupied_zones = []

        for card in self.cards:
            # determine surface (rotate for banished)
            if card["location"] == "banished":
                # rotate original by 90 degrees (keep consistent)
                surf = pygame.transform.rotate(card["surface_orig"], 90)
            else:
                surf = card["surface_orig"]
            card["surface"] = surf
            # preview
            preview = card.get("preview")
            # determine rect based on location & owner
            if card["location"] == "hand":
                if card["owner"] == "player":
                    rect = surf.get_rect(topleft=(player_x, player_y))
                    player_x += CARD_WIDTH + SPACING
                else:
                    rect = surf.get_rect(topleft=(opponent_x, opponent_y))
                    opponent_x += CARD_WIDTH + SPACING
            elif card["location"] == "field":
                rect = None
                # place in first free zone
                for zone in self.zones:
                    if zone not in occupied_zones:
                        # ensure no existing card rect collides with this zone
                        if not any(r.colliderect(zone) for r in self.card_rects):
                            rect = surf.get_rect(topleft=(zone.x, zone.y))
                            occupied_zones.append(zone)
                            break
                if rect is None:
                    # fallback: place offscreen if no free zone
                    rect = surf.get_rect(topleft=(0, 0))
            elif card["location"] == "graveyard":
                # stack on appropriate graveyard zone (player-> index0, opponent-> index1)
                if card["owner"] == "player":
                    gx, gy = self.graveyard_zones[0].topleft
                else:
                    gx, gy = self.graveyard_zones[1].topleft
                rect = surf.get_rect(topleft=(gx, gy))
            elif card["location"] == "banished":
                if card["owner"] == "player":
                    bx, by = self.banish_zones[0].topleft
                else:
                    bx, by = self.banish_zones[1].topleft
                rect = surf.get_rect(topleft=(bx, by))
            else:
                rect = surf.get_rect(topleft=(0, 0))

            card["rect"] = rect
            self.card_surfaces.append(card["surface"])
            self.card_preview_surfaces.append(preview)
            self.card_rects.append(rect)

    # -----------------------------
    # Drawing
    # -----------------------------
    def draw_field(self, hover_index=None):
        self.screen.blit(self.mat_surface, (0, 0))

        # Draw zones
        for zone in self.zones:
            pygame.draw.rect(self.screen, (100, 100, 100), zone, 2)
        # grave/banish visual
        for gy in self.graveyard_zones:
            pygame.draw.rect(self.screen, (150, 0, 0), gy, 2)
        for bz in self.banish_zones:
            pygame.draw.rect(self.screen, (0, 0, 150), bz, 2)

        # zone highlight while dragging
        if self.dragged_card is not None:
            for zone in self.zones + self.graveyard_zones + self.banish_zones:
                if zone.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(self.screen, (255, 255, 0), zone, 3)

        # draw cards (non-dragged)
        for i, card in enumerate(self.cards):
            if self.dragged_card is not None and card is self.dragged_card:
                continue
            self.screen.blit(card["surface"], card["rect"].topleft)

        # draw dragged on top
        if self.dragged_card is not None:
            # use dragged_card rect (we keep it updated while dragging)
            self.screen.blit(self.dragged_card["surface"], self.dragged_card["rect"].topleft)

        # draw preview for hover card
        if hover_index is not None and 0 <= hover_index < len(self.cards):
            # choose preview from that card
            preview = self.cards[hover_index]["preview"]
            preview_x = 0
            preview_y = (self.screen.get_height() - PREVIEW_HEIGHT) // 2
            self.screen.blit(preview, (preview_x, preview_y))

        # console
        pygame.draw.rect(self.screen, (50, 50, 50), self.console_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), self.console_rect, 2)
        line_height = self.console_font.get_height() + 2
        max_history = self.console_rect.height // line_height - 1
        display_text = self.console_text
        max_width = self.console_rect.width - 10
        while self.console_font.size(display_text)[0] > max_width and len(display_text) > 0:
            display_text = display_text[1:]
        for i, cmd in enumerate(self.console_history[-max_history:]):
            txt_surf = self.console_font.render(cmd, True, (0, 255, 0))
            self.screen.blit(txt_surf, (self.console_rect.x + 5, self.console_rect.y + i * line_height))
        txt_surf = self.console_font.render(display_text, True, (255, 255, 255))
        self.screen.blit(txt_surf, (self.console_rect.x + 5, self.console_rect.y + self.console_rect.height - line_height))

        # Life Points display
        lp_font = pygame.font.SysFont(None, 24)
        player_lp_text = lp_font.render(f"{self.life_points['play']}", True, (255, 255, 255))
        opponent_lp_text = lp_font.render(f"{self.life_points['opp']}", True, (255, 255, 255))
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
    # Add drawn cards (from draw window)
    # -----------------------------
    def open_draw_window(self, side):
        def add_cards(selected_names):
            # create new instances for each selected name
            for name in selected_names:
                inst = self._create_card_instance(name, owner=side, location="hand")
                self.cards.append(inst)
            self.load_cards()
        root = tk.Tk()
        root.withdraw()
        draw_window = DrawCardWindow(root, add_cards)
        root.wait_window(draw_window)
        root.destroy()

    # -----------------------------
    # Move cards by uid to a new location
    # -----------------------------
    def move_cards_by_uid(self, uids, new_location):
        uid_set = set(uids)
        for c in self.cards:
            if c["uid"] in uid_set:
                c["location"] = new_location
                # rotate surface immediately if banished
                if new_location == "banished":
                    c["surface"] = pygame.transform.rotate(c["surface_orig"], 90)
                else:
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
                        cmd = self.console_text.strip().lower()
                        self.console_history.append(cmd)
                        if cmd == "drawplay":
                            self.open_draw_window("player")
                        elif cmd == "drawopp":
                            self.open_draw_window("opponent")
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
                    # iterate in reverse order so top-most card is picked first
                    for i in range(len(self.card_rects)-1, -1, -1):
                        rect = self.card_rects[i]
                        if rect.collidepoint(event.pos):
                            self.dragged_card_index = i
                            self.dragged_card = self.cards[i]
                            self.drag_offset = (event.pos[0] - rect.x, event.pos[1] - rect.y)
                            break

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.dragged_card is not None:
                        # check field zones
                        snapped = False
                        for zone in self.zones:
                            if zone.collidepoint(event.pos):
                                # set card to field and snap rect
                                self.dragged_card["location"] = "field"
                                self.dragged_card["rect"].topleft = (zone.x, zone.y)
                                snapped = True
                                break
                        # check graveyard zones
                        if not snapped:
                            for idx, gy in enumerate(self.graveyard_zones):
                                if gy.collidepoint(event.pos):
                                    self.dragged_card["location"] = "graveyard"
                                    # set to appropriate owner grave rect
                                    if self.dragged_card["owner"] == "player":
                                        self.dragged_card["rect"].topleft = self.graveyard_zones[0].topleft
                                    else:
                                        self.dragged_card["rect"].topleft = self.graveyard_zones[1].topleft
                                    snapped = True
                                    break
                        # check banish zones
                        if not snapped:
                            for idx, bz in enumerate(self.banish_zones):
                                if bz.collidepoint(event.pos):
                                    self.dragged_card["location"] = "banished"
                                    # rotate surface
                                    self.dragged_card["surface"] = pygame.transform.rotate(self.dragged_card["surface_orig"], 90)
                                    if self.dragged_card["owner"] == "player":
                                        self.dragged_card["rect"].topleft = self.banish_zones[0].topleft
                                    else:
                                        self.dragged_card["rect"].topleft = self.banish_zones[1].topleft
                                    snapped = True
                                    break
                        # if not snapped, leave it where released (rect already updated during motion)
                        self.load_cards()  # recompute arrays & ensure consistent ordering
                        self.dragged_card = None
                        self.dragged_card_index = None

                elif event.type == pygame.MOUSEMOTION:
                    if self.dragged_card is not None:
                        # move rect following mouse
                        new_x = event.pos[0] - self.drag_offset[0]
                        new_y = event.pos[1] - self.drag_offset[1]
                        self.dragged_card["rect"].topleft = (new_x, new_y)
                        # reflect change into card_rects for hover detection if needed
                        self.load_cards()  # lightweight enough here to keep arrays consistent

            clock.tick(30)

        pygame.quit()

# -----------------------------
# Main
# -----------------------------
def on_selection(player_cards, opponent_cards):
    root.destroy()
    YGOSimulator(player_cards, opponent_cards)

root = tk.Tk()
root.withdraw()  # hide main window
CardSelectionWindow(root, on_selection)
root.mainloop()
