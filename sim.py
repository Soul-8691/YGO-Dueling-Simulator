import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import requests
from io import BytesIO
import json

# Load card info from JSON
with open('YGOProDeck_Card_Info.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

YGOProDeck_Card_Info = {}
for cdata in data['data']:
    YGOProDeck_Card_Info[cdata['name']] = cdata

CARD_WIDTH, CARD_HEIGHT = 80, 116
SPACING = 10


class CardSelector(tk.Toplevel):
    def __init__(self, callback):
        super().__init__()
        self.title("Select Cards")
        self.geometry("400x600")
        self.callback = callback

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.update_list)

        search_entry = ttk.Entry(self, textvariable=self.search_var, width=40)
        search_entry.pack(pady=5)

        self.listbox = tk.Listbox(self, selectmode=tk.SINGLE, width=40, height=20)
        self.listbox.pack(padx=10, pady=5)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=5)

        self.btn_player = ttk.Button(btn_frame, text="Add to Player", command=lambda: self.add_card("player"))
        self.btn_player.grid(row=0, column=0, padx=5)

        self.btn_opponent = ttk.Button(btn_frame, text="Add to Opponent", command=lambda: self.add_card("opponent"))
        self.btn_opponent.grid(row=0, column=1, padx=5)

        confirm_btn = ttk.Button(self, text="Confirm Selection", command=self.confirm_selection)
        confirm_btn.pack(pady=10)

        self.player_cards = []
        self.opponent_cards = []

        self.populate_listbox()

    def populate_listbox(self):
        self.listbox.delete(0, tk.END)
        for name in sorted(YGOProDeck_Card_Info.keys()):
            self.listbox.insert(tk.END, name)

    def update_list(self, *args):
        search_term = self.search_var.get().lower()
        self.listbox.delete(0, tk.END)
        for name in sorted(YGOProDeck_Card_Info.keys()):
            if search_term in name.lower():
                self.listbox.insert(tk.END, name)

    def add_card(self, side):
        selection = self.listbox.curselection()
        if not selection:
            return
        name = self.listbox.get(selection[0])

        if side == "player":
            if len(self.player_cards) >= 5:
                messagebox.showwarning("Limit Reached", "Player already has 5 cards.")
                return
            self.player_cards.append(name)
        else:
            if len(self.opponent_cards) >= 5:
                messagebox.showwarning("Limit Reached", "Opponent already has 5 cards.")
                return
            self.opponent_cards.append(name)

        print(f"Added {name} to {side}.")

    def confirm_selection(self):
        if not (1 <= len(self.player_cards) <= 5):
            messagebox.showerror("Error", "You must select between 1 and 5 cards for the Player.")
            return
        if not (1 <= len(self.opponent_cards) <= 5):
            messagebox.showerror("Error", "You must select between 1 and 5 cards for the Opponent.")
            return
        self.callback(self.player_cards, self.opponent_cards)
        self.destroy()


class YGOSimulator(tk.Tk):
    def __init__(self, player_cards, opponent_cards):
        super().__init__()
        self.title("Yu-Gi-Oh! Manual Simulator")
        self.state('zoomed')  # maximize window

        self.canvas = tk.Canvas(self, bg="green")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.card_images = []  # list instead of dict
        self.player_cards = player_cards
        self.opponent_cards = opponent_cards

        self.canvas.bind("<Configure>", self.on_first_resize)
        self.has_drawn = False

    def fetch_card_image(self, card_id):
        url = f"https://images.ygoprodeck.com/images/cards/{card_id}.jpg"
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))
        img = img.resize((CARD_WIDTH, CARD_HEIGHT), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        self.card_images.append(photo)  # keep every copy
        return photo

    def display_cards(self):
        self.canvas.delete("all")
        self.card_images.clear()  # reset but keep list structure

        # Opponent cards
        x, y = 10, 10
        for card in self.opponent_cards:
            card_id = YGOProDeck_Card_Info[card]["id"]
            img = self.fetch_card_image(card_id)
            self.canvas.create_image(x, y, image=img, anchor=tk.NW)
            x += CARD_WIDTH + SPACING

        # Player cards
        canvas_height = self.canvas.winfo_height()
        x, y = 10, canvas_height - CARD_HEIGHT - 10
        for card in self.player_cards:
            card_id = YGOProDeck_Card_Info[card]["id"]
            img = self.fetch_card_image(card_id)
            self.canvas.create_image(x, y, image=img, anchor=tk.NW)
            x += CARD_WIDTH + SPACING

    def on_first_resize(self, event=None):
        # only draw once the canvas has a valid size
        if not self.has_drawn and self.canvas.winfo_height() > CARD_HEIGHT * 2:
            self.has_drawn = True
            self.display_cards()


def main():
    root = tk.Tk()
    root.withdraw()  # hide root while selecting cards

    def on_selection(player_cards, opponent_cards):
        # Open simulator only after selection
        root.destroy()  # close hidden root before launching simulator
        sim = YGOSimulator(player_cards, opponent_cards)
        sim.mainloop()

    selector = CardSelector(on_selection)
    selector.mainloop()


if __name__ == "__main__":
    main()
