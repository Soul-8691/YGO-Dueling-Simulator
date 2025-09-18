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

        # Cards stored as dicts: name, owner ('player'/'opponent'), location ('hand','field','graveyard','banished')
        self.cards = []
        for card in player_cards:
            self.cards.append({"name": card, "owner": "player", "location": "hand"})
        for card in opponent_cards:
            self.cards.append({"name": card, "owner": "opponent", "location": "hand"})

        self.card_surfaces = []
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

        # Create zones
        self.zones = self.create_zones()

        # Graveyard & banish zones (hardcoded example positions)
        self.graveyard_zones = [
            pygame.Rect(150, self.screen_height//2 - CARD_HEIGHT//2, CARD_WIDTH, CARD_HEIGHT),  # Player
            pygame.Rect(self.screen_width-300, self.screen_height//2 - CARD_HEIGHT//2, CARD_WIDTH, CARD_HEIGHT)  # Opponent
        ]
        self.banish_zones = [
            pygame.Rect(150, self.screen_height//2 + CARD_HEIGHT + 20, CARD_WIDTH, CARD_HEIGHT),  # Player
            pygame.Rect(self.screen_width-300, self.screen_height//2 + CARD_HEIGHT + 20, CARD_WIDTH, CARD_HEIGHT)  # Opponent
        ]

        # Drag state
        self.dragged_card_index = None
        self.dragged_card_pos = (0,0)
        self.drag_offset = (0,0)

        self.load_cards()
        self.run()

    # -----------------------------
    # Create 20 zones (2 rows of 5 per side)
    # -----------------------------
    def create_zones(self):
        zones = []
        padding_x = 773
        padding_y = 109
        gap_x = 35
        gap_y = 15

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
    # Fetch card image
    # -----------------------------
    def fetch_card_surface(self, card_name, width, height):
        card_id = YGOProDeck_Card_Info[card_name]["id"]
        url = f"https://images.ygoprodeck.com/images/cards/{card_id}.jpg"
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))
        img = img.resize((width, height), Image.LANCZOS)
        return pygame.image.fromstring(img.tobytes(), img.size, img.mode)

    # -----------------------------
    # Load cards onto screen surfaces
    # -----------------------------
    def load_cards(self):
        self.card_surfaces.clear()
        self.card_rects.clear()
        self.card_preview_surfaces.clear()

        # Track positions for hand and field
        player_x, player_y = 0, self.screen_height - CARD_HEIGHT
        opponent_x, opponent_y = 0, 0
        field_positions = self.zones

        for card in self.cards:
            surface = self.fetch_card_surface(card["name"], CARD_WIDTH, CARD_HEIGHT)
            preview = self.fetch_card_surface(card["name"], PREVIEW_WIDTH, PREVIEW_HEIGHT)

            if card["location"] == "hand":
                if card["owner"] == "player":
                    rect = surface.get_rect(topleft=(player_x, player_y))
                    player_x += CARD_WIDTH + SPACING
                else:
                    rect = surface.get_rect(topleft=(opponent_x, opponent_y))
                    opponent_x += CARD_WIDTH + SPACING
            elif card["location"] == "field":
                # Assign first available zone
                for zone in field_positions:
                    if not any(r.colliderect(zone) for r in self.card_rects):
                        rect = surface.get_rect(topleft=(zone.x, zone.y))
                        break
            elif card["location"] == "graveyard":
                if card["owner"] == "player":
                    rect = surface.get_rect(topleft=(self.graveyard_zones[0].x, self.graveyard_zones[0].y))
                else:
                    rect = surface.get_rect(topleft=(self.graveyard_zones[1].x, self.graveyard_zones[1].y))
            elif card["location"] == "banished":
                if card["owner"] == "player":
                    rect = surface.get_rect(topleft=(self.banish_zones[0].x, self.banish_zones[0].y))
                else:
                    rect = surface.get_rect(topleft=(self.banish_zones[1].x, self.banish_zones[1].y))

            self.card_surfaces.append(surface)
            self.card_preview_surfaces.append(preview)
            self.card_rects.append(rect)

    # -----------------------------
    # Draw everything
    # -----------------------------
    def draw_field(self, hover_index=None):
        self.screen.blit(self.mat_surface, (0,0))

        # Draw zones
        for zone in self.zones:
            pygame.draw.rect(self.screen, (100,100,100), zone, 2)
        for gy in self.graveyard_zones:
            pygame.draw.rect(self.screen, (150,0,0), gy, 2)
        for bz in self.banish_zones:
            pygame.draw.rect(self.screen, (0,0,150), bz, 2)

        # Highlight dragged
        if self.dragged_card_index is not None:
            for zone in self.zones:
                if zone.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(self.screen, (255,255,0), zone, 3)

        # Draw cards
        for i, surface in enumerate(self.card_surfaces):
            if i != self.dragged_card_index:
                self.screen.blit(surface, self.card_rects[i].topleft)
        if self.dragged_card_index is not None:
            self.screen.blit(self.card_surfaces[self.dragged_card_index], self.dragged_card_pos)

        # Preview
        if hover_index is not None:
            preview_surface = self.card_preview_surfaces[hover_index]
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
        pygame.display.flip()

    # -----------------------------
    # Open Tkinter selection for moving cards
    # -----------------------------
    def select_cards_from_game_state(self, callback):
        # Only allow selecting cards in hand or on field
        available = [c["name"] for c in self.cards if c["location"] in ("hand","field")]
        if not available:
            return
        def apply_selection(selected):
            callback(selected)
        root = tk.Tk()
        root.withdraw()
        draw_window = DrawCardWindow(root, apply_selection)
        draw_window.listbox.delete(0, tk.END)
        for name in available:
            draw_window.listbox.insert(tk.END, name)
        root.wait_window(draw_window)
        root.destroy()

    # -----------------------------
    # Open Tkinter draw window
    # -----------------------------
    def open_draw_window(self, side):
        def add_cards(selected):
            for name in selected:
                self.cards.append({"name": name, "owner": side, "location": "hand"})
            self.load_cards()
        root = tk.Tk()
        root.withdraw()
        draw_window = DrawCardWindow(root, add_cards)
        root.wait_window(draw_window)
        root.destroy()

    # -----------------------------
    # Main loop
    # -----------------------------
    def run(self):
        running = True
        clock = pygame.time.Clock()
        while running:
            hover_index = None
            mouse_pos = pygame.mouse.get_pos()
            for i, rect in enumerate(self.card_rects):
                if rect.collidepoint(mouse_pos):
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
                        elif cmd == "graveyard":
                            self.select_cards_from_game_state(lambda selected: self.move_cards(selected,"graveyard"))
                        elif cmd == "banish":
                            self.select_cards_from_game_state(lambda selected: self.move_cards(selected,"banished"))
                        else:
                            print(f"Unknown command: {cmd}")
                        self.console_text = ""
                    else:
                        self.console_text += event.unicode

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for i, rect in enumerate(self.card_rects):
                        if rect.collidepoint(event.pos):
                            self.dragged_card_index = i
                            self.drag_offset = (event.pos[0]-rect.x, event.pos[1]-rect.y)
                            break

                elif event.type == pygame.MOUSEBUTTONUP:
                    if self.dragged_card_index is not None:
                        # Snap to nearest zone if on field
                        for zone in self.zones:
                            if zone.collidepoint(event.pos):
                                self.cards[self.dragged_card_index]["location"] = "field"
                                self.card_rects[self.dragged_card_index].topleft = (zone.x, zone.y)
                                break
                        self.dragged_card_index = None

                elif event.type == pygame.MOUSEMOTION:
                    if self.dragged_card_index is not None:
                        self.dragged_card_pos = (event.pos[0]-self.drag_offset[0], event.pos[1]-self.drag_offset[1])

            clock.tick(30)
        pygame.quit()

    # -----------------------------
    # Move selected cards to a new location
    # -----------------------------
    def move_cards(self, card_names, new_location):
        for card in self.cards:
            if card["name"] in card_names:
                card["location"] = new_location
        self.load_cards()

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
