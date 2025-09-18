import tkinter as tk
from tkinter import messagebox
import requests
from PIL import Image
from io import BytesIO
import pygame
import json

# -----------------------------
# Load Card Data
# -----------------------------
with open('YGOProDeck_Card_Info.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

YGOProDeck_Card_Info = {}
for cdata in data['data']:
    YGOProDeck_Card_Info[cdata['name']] = cdata

CARD_WIDTH, CARD_HEIGHT = 80, 116
SPACING = 10

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
# Pygame Simulator
# -----------------------------
class YGOSimulator:
    PREVIEW_WIDTH, PREVIEW_HEIGHT = 400, 583

    def __init__(self, player_cards, opponent_cards):
        pygame.init()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Yu-Gi-Oh! Manual Simulator")

        self.player_cards = player_cards
        self.opponent_cards = opponent_cards
        self.card_surfaces = []      # small card surfaces
        self.card_rects = []         # small card rects for hover detection
        self.card_preview_surfaces = []  # large preview surfaces

        self.load_cards()
        self.run()

    def fetch_card_surface(self, card_id, width, height):
        url = f"https://images.ygoprodeck.com/images/cards/{card_id}.jpg"
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))
        img = img.resize((width, height), Image.LANCZOS)
        mode = img.mode
        size = img.size
        data = img.tobytes()
        return pygame.image.fromstring(data, size, mode)

    def load_cards(self):
        # Opponent cards (top left)
        x, y = 10, 10
        for card in self.opponent_cards:
            card_id = YGOProDeck_Card_Info[card]["id"]
            surface = self.fetch_card_surface(card_id, CARD_WIDTH, CARD_HEIGHT)
            preview_surface = self.fetch_card_surface(card_id, self.PREVIEW_WIDTH, self.PREVIEW_HEIGHT)
            rect = surface.get_rect(topleft=(x, y))
            self.card_surfaces.append(surface)
            self.card_preview_surfaces.append(preview_surface)
            self.card_rects.append(rect)
            x += CARD_WIDTH + SPACING

        # Player cards (bottom left)
        screen_height = self.screen.get_height()
        x, y = 10, screen_height - CARD_HEIGHT - 10
        for card in self.player_cards:
            card_id = YGOProDeck_Card_Info[card]["id"]
            surface = self.fetch_card_surface(card_id, CARD_WIDTH, CARD_HEIGHT)
            preview_surface = self.fetch_card_surface(card_id, self.PREVIEW_WIDTH, self.PREVIEW_HEIGHT)
            rect = surface.get_rect(topleft=(x, y))
            self.card_surfaces.append(surface)
            self.card_preview_surfaces.append(preview_surface)
            self.card_rects.append(rect)
            x += CARD_WIDTH + SPACING

    def draw_field(self, hover_index=None):
        self.screen.fill((0, 128, 0))  # green background

        # Draw all cards
        for surface, rect in zip(self.card_surfaces, self.card_rects):
            self.screen.blit(surface, rect.topleft)

        # Draw preview if hovering
        if hover_index is not None:
            preview_surface = self.card_preview_surfaces[hover_index]
            preview_x = 10  # leftmost
            preview_y = (self.screen.get_height() - self.PREVIEW_HEIGHT) // 2
            self.screen.blit(preview_surface, (preview_x, preview_y))

        pygame.display.flip()

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
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False

            clock.tick(30)  # limit FPS

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
