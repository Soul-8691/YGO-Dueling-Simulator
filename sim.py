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

CARD_WIDTH, CARD_HEIGHT = 80, 116
SPACING = 10
PREVIEW_WIDTH, PREVIEW_HEIGHT = 350, 510
MAX_HAND = 12

# -----------------------------
# Tkinter Card Selection Window
# -----------------------------
class CardSelectionWindow(tk.Toplevel):
    def __init__(self, master, callback):
        super().__init__(master)
        self.title("Select Cards")

        self.callback = callback

        all_cards = sorted(YGOProDeck_Card_Info.keys())

        tk.Label(self, text="Select Player Cards (1–5)").pack()
        self.player_listbox = tk.Listbox(self, selectmode=tk.MULTIPLE, exportselection=False, width=40, height=20)
        self.player_listbox.pack(side=tk.LEFT, padx=10)
        for name in all_cards:
            self.player_listbox.insert(tk.END, name)

        tk.Label(self, text="Select Opponent Cards (1–5)").pack()
        self.opponent_listbox = tk.Listbox(self, selectmode=tk.MULTIPLE, exportselection=False, width=40, height=20)
        self.opponent_listbox.pack(side=tk.RIGHT, padx=10)
        for name in all_cards:
            self.opponent_listbox.insert(tk.END, name)

        tk.Button(self, text="Confirm", command=self.confirm_selection).pack(pady=10)

    def confirm_selection(self):
        player_cards = [self.player_listbox.get(i) for i in self.player_listbox.curselection()]
        opponent_cards = [self.opponent_listbox.get(i) for i in self.opponent_listbox.curselection()]

        if not (1 <= len(player_cards) <= 5):
            messagebox.showerror("Error", "Select between 1 and 5 Player cards")
            return
        if not (1 <= len(opponent_cards) <= 5):
            messagebox.showerror("Error", "Select between 1 and 5 Opponent cards")
            return

        self.destroy()
        self.callback(player_cards, opponent_cards)

# -----------------------------
# Tkinter Draw Card Window
# -----------------------------
class DrawCardWindow(tk.Toplevel):
    def __init__(self, master, callback):
        super().__init__(master)
        self.title("Draw Cards")
        self.callback = callback

        all_cards = sorted(YGOProDeck_Card_Info.keys())
        self.listbox = tk.Listbox(self, selectmode=tk.MULTIPLE, width=40, height=20)
        self.listbox.pack(padx=10, pady=10)

        for name in all_cards:
            self.listbox.insert(tk.END, name)

        tk.Button(self, text="Confirm", command=self.confirm).pack(pady=5)

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

        self.player_cards = player_cards
        self.opponent_cards = opponent_cards

        self.card_surfaces = []      
        self.card_rects = []         
        self.card_preview_surfaces = []

        # Console settings
        self.console_font = pygame.font.SysFont(None, 24)
        self.console_text = ""
        self.console_history = []  # store valid commands
        self.console_rect = pygame.Rect(
            self.screen_width-260, self.screen_height-160, 250, 150
        )

        # Load mat background
        self.mat_surface = pygame.image.load("mat.jpg").convert()
        self.mat_surface = pygame.transform.scale(self.mat_surface, (self.screen_width, self.screen_height))

        # Create zones
        self.zones = self.create_zones()

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

        padding_x = 50
        padding_y = 50
        gap_x = (self.screen_width - 2*padding_x - 5*CARD_WIDTH)/4
        gap_y = 30

        # Player zones (bottom)
        start_y = self.screen_height - CARD_HEIGHT*2 - padding_y
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
    def fetch_card_surface(self, card_id, width, height):
        url = f"https://images.ygoprodeck.com/images/cards/{card_id}.jpg"
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))
        img = img.resize((width, height), Image.LANCZOS)
        mode = img.mode
        size = img.size
        data = img.tobytes()
        return pygame.image.fromstring(data, size, mode)

    # -----------------------------
    # Load cards for player and opponent
    # -----------------------------
    def load_cards(self):
        self.card_surfaces.clear()
        self.card_rects.clear()
        self.card_preview_surfaces.clear()

        # Opponent cards (top left)
        x, y = 10, 10
        for card in self.opponent_cards:
            card_id = YGOProDeck_Card_Info[card]["id"]
            surface = self.fetch_card_surface(card_id, CARD_WIDTH, CARD_HEIGHT)
            preview_surface = self.fetch_card_surface(card_id, PREVIEW_WIDTH, PREVIEW_HEIGHT)
            rect = surface.get_rect(topleft=(x, y))
            self.card_surfaces.append(surface)
            self.card_preview_surfaces.append(preview_surface)
            self.card_rects.append(rect)
            x += CARD_WIDTH + SPACING

        # Player cards (bottom left)
        x, y = 10, self.screen_height - CARD_HEIGHT - 10
        for card in self.player_cards:
            card_id = YGOProDeck_Card_Info[card]["id"]
            surface = self.fetch_card_surface(card_id, CARD_WIDTH, CARD_HEIGHT)
            preview_surface = self.fetch_card_surface(card_id, PREVIEW_WIDTH, PREVIEW_HEIGHT)
            rect = surface.get_rect(topleft=(x, y))
            self.card_surfaces.append(surface)
            self.card_preview_surfaces.append(preview_surface)
            self.card_rects.append(rect)
            x += CARD_WIDTH + SPACING

    # -----------------------------
    # Draw field, zones, cards, preview, console
    # -----------------------------
    def draw_field(self, hover_index=None):
        # Draw mat
        self.screen.blit(self.mat_surface, (0,0))

        # Draw zones
        for zone in self.zones:
            pygame.draw.rect(self.screen, (100,100,100), zone, 2)

        # Highlight hovered zone while dragging
        if self.dragged_card_index is not None:
            for zone in self.zones:
                if zone.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(self.screen, (255,255,0), zone, 3)

        # Draw cards
        for i, surface in enumerate(self.card_surfaces):
            if i != self.dragged_card_index:
                self.screen.blit(surface, self.card_rects[i].topleft)

        # Draw dragged card on top
        if self.dragged_card_index is not None:
            self.screen.blit(self.card_surfaces[self.dragged_card_index], self.dragged_card_pos)

        # Draw preview
        if hover_index is not None:
            preview_surface = self.card_preview_surfaces[hover_index]
            preview_x = 10
            preview_y = (self.screen.get_height() - PREVIEW_HEIGHT)//2
            self.screen.blit(preview_surface, (preview_x, preview_y))

        # Draw console
        pygame.draw.rect(self.screen, (50,50,50), self.console_rect)
        pygame.draw.rect(self.screen, (200,200,200), self.console_rect, 2)
        line_height = self.console_font.get_height() + 2
        max_history = self.console_rect.height // line_height - 1
        for i, cmd in enumerate(self.console_history[-max_history:]):
            txt_surf = self.console_font.render(cmd, True, (0,255,0))
            self.screen.blit(txt_surf, (self.console_rect.x+5, self.console_rect.y + i*line_height))
        txt_surf = self.console_font.render(self.console_text, True, (255,255,255))
        input_y = self.console_rect.y + self.console_rect.height - line_height
        self.screen.blit(txt_surf, (self.console_rect.x+5, input_y))

        pygame.display.flip()

    # -----------------------------
    # Open Tkinter draw window
    # -----------------------------
    def open_draw_window(self, side):
        def add_cards(selected):
            if side == "player":
                if len(self.player_cards) + len(selected) > MAX_HAND:
                    print("Hand size over 12 not currently supported!")
                    return
                self.player_cards.extend(selected)
            else:
                if len(self.opponent_cards) + len(selected) > MAX_HAND:
                    print("Hand size over 12 not currently supported!")
                    return
                self.opponent_cards.extend(selected)
            self.load_cards()

        root = tk.Tk()
        root.withdraw()
        draw_window = DrawCardWindow(root, add_cards)
        root.wait_window(draw_window)
        root.destroy()

    # -----------------------------
    # Main Pygame loop
    # -----------------------------
    def run(self):
        running = True
        clock = pygame.time.Clock()

        while running:
            mouse_pos = pygame.mouse.get_pos()
            hover_index = None
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
                        if cmd == "drawplay":
                            self.console_history.append(cmd)
                            self.open_draw_window("player")
                        elif cmd == "drawopp":
                            self.console_history.append(cmd)
                            self.open_draw_window("opponent")
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
                        for zone in self.zones:
                            if zone.collidepoint(event.pos):
                                self.card_rects[self.dragged_card_index].topleft = (zone.x, zone.y)
                                break
                        self.dragged_card_index = None

                elif event.type == pygame.MOUSEMOTION:
                    if self.dragged_card_index is not None:
                        self.dragged_card_pos = (event.pos[0]-self.drag_offset[0], event.pos[1]-self.drag_offset[1])

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
