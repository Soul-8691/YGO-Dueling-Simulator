import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
import json
import os
import requests
from io import BytesIO
from PIL import Image, ImageTk
from collections import Counter

DECKS_DIR = "decks"
os.makedirs(DECKS_DIR, exist_ok=True)

EXTRA_DECK_TYPES = [
    "Fusion Monster", "XYZ Monster", "Synchro Monster", "Link Monster",
    "Pendulum Effect Fusion Monster", "XYZ Pendulum Effect Monster",
    "Synchro Pendulum Effect Monster"
]

# Load card info and format library
with open("YGOProDeck_Card_Info.json", "r", encoding="utf-8") as f:
    data = json.load(f)
YGOProDeck_Card_Info = {c["name"]: c for c in data["data"]}

with open("cards_by_format_updated.json", "r", encoding="utf-8") as f:
    format_data = json.load(f)


def show_card_preview(card_name):
    """Show a popup with a card image from ygoprodeck."""
    try:
        card_id = YGOProDeck_Card_Info[card_name]["id"]
        url = f"https://images.ygoprodeck.com/images/cards/{card_id}.jpg"
        resp = requests.get(url)
        resp.raise_for_status()
        pil_img = Image.open(BytesIO(resp.content))
        pil_img.thumbnail((400, 600))
        preview_win = tk.Toplevel()
        preview_win.title(card_name)
        tk_img = ImageTk.PhotoImage(pil_img)
        label = tk.Label(preview_win, image=tk_img)
        label.image = tk_img
        label.pack()
        preview_win.bind("<Escape>", lambda e: preview_win.destroy())
    except Exception as e:
        messagebox.showerror("Error", f"Cannot load card image for {card_name}.\n{e}")


class DeckBuilder:
    def __init__(self, root):
        self.root = root
        self.root.title("Deck Builder")
        self.root.geometry("750x600")
        self.root.state("zoomed")  # maximize window on start (Windows)

        self.main_deck_list = []    # Cards in the main deck
        self.extra_deck_list = []   # Cards in the extra deck
        self.side_deck_list = []    # Cards in the side deck

        # Three deck sections
        self.main_deck = {}
        self.extra_deck = {}
        self.side_deck = {}
        self.current_section = tk.StringVar(value="main")
        self.current_section.trace_add("write", lambda *args: [self.update_listbox(), self.update_deck_display()])

        # Format / sort options
        self.sort_formats_var = tk.StringVar(value="Alphabetical")
        self.sort_var = tk.StringVar(value="Alphabetical")

        self.sort_formats_var.trace_add("write", lambda *args: self.populate_format_list())

        # Format library navigation
        self.current_format_stage = "format_select"
        self.selected_format = None

        # Copies input
        self.copies_var = tk.StringVar(value="1")

        # 🔍 Search bar
        self.search_var = tk.StringVar(value="")
        self.search_var.trace_add("write", self.update_listbox)

        # Build UI
        self._build_ui()
    
    def populate_format_list(self):
        self.listbox.delete(0, tk.END)
        formats = list(format_data.keys())
        if self.sort_formats_var.get() == "Alphabetical":
            formats.sort()
        else:  # By Date
            # Assuming each format has a 'date' key (ISO: YYYY-MM-DD)
            formats.sort(key=lambda f: format_data[f].get("date", "9999-12-31"))

        for fmt in formats:
            self.listbox.insert(tk.END, fmt)

    # ------------------ UI ------------------
    def _build_ui(self):
        # Section selector
        section_frame = tk.Frame(self.root)
        section_frame.pack(fill="x", padx=5, pady=2)
        tk.Label(section_frame, text="Editing:").pack(side="left")
        tk.OptionMenu(section_frame, self.current_section, "main", "extra", "side").pack(side="left")

        # Sort controls
        sort_frame = tk.Frame(self.root)
        sort_frame.pack(fill="x", padx=5, pady=2)
        tk.Label(sort_frame, text="Sort Formats:").pack(side="left", padx=5)
        tk.OptionMenu(sort_frame, self.sort_formats_var, "Alphabetical", "By Date").pack(side="left", padx=5)
        tk.Label(sort_frame, text="Sort Cards:").pack(side="left", padx=5)
        tk.OptionMenu(
            sort_frame,
            self.sort_var,
            "Alphabetical", "By Level", "By Attribute", "By ATK",
            "By DEF", "By Race", "By Type", "By Konami ID", "By Usage Count"
        ).pack(side="left", padx=5)

        # Top buttons
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill="x", padx=5, pady=5)
        tk.Button(top_frame, text="Load Deck", command=self.load_deck).pack(side="left", padx=5)
        tk.Button(top_frame, text="Save Deck", command=self.save_deck).pack(side="left", padx=5)

        # Mode
        mode_frame = tk.Frame(self.root)
        mode_frame.pack(fill="x", pady=5)
        self.mode_var = tk.StringVar(value="all")
        tk.Radiobutton(mode_frame, text="All Cards", variable=self.mode_var, value="all", command=self.update_listbox).pack(side="left")
        tk.Radiobutton(mode_frame, text="Format Library", variable=self.mode_var, value="format", command=self.update_listbox).pack(side="left")

        # Copies
        copies_frame = tk.Frame(self.root)
        copies_frame.pack(fill="x", pady=2)
        tk.Label(copies_frame, text="Copies to add:").pack(side="left", padx=5)
        tk.Entry(copies_frame, textvariable=self.copies_var, width=5).pack(side="left")

        # Search bar
        search_frame = tk.Frame(self.root)
        search_frame.pack(fill="x", padx=5, pady=2)
        tk.Label(search_frame, text="Search:").pack(side="left")
        tk.Entry(search_frame, textvariable=self.search_var).pack(side="left", fill="x", expand=True)

        # Listbox
        listbox_frame = tk.Frame(self.root)
        listbox_frame.pack(fill="both", expand=True)
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side="right", fill="y")
        self.listbox = tk.Listbox(listbox_frame, selectmode=tk.MULTIPLE, yscrollcommand=scrollbar.set)
        self.listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)

        # --- Deck Contents Section ---
        deck_frame = tk.Frame(self.root)
        deck_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Container for the 3 lists side-by-side
        lists_frame = tk.Frame(deck_frame)
        lists_frame.pack(fill=tk.BOTH, expand=True)

        def create_listbox_with_scrollbar(parent, title):
            frame = tk.Frame(parent)
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            tk.Label(frame, text=title).pack(anchor="w")

            scrollbar = tk.Scrollbar(frame)
            listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, width=30, height=20)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            scrollbar.config(command=listbox.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            return listbox

        # Now create the three deck lists side-by-side
        self.main_listbox  = create_listbox_with_scrollbar(lists_frame, "Main Deck")
        self.extra_listbox = create_listbox_with_scrollbar(lists_frame, "Extra Deck")
        self.side_listbox  = create_listbox_with_scrollbar(lists_frame, "Side Deck")

        # Buttons
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=5)
        tk.Button(control_frame, text="Add Selected", command=self.add_selected).pack(side="left", padx=5)
        tk.Button(control_frame, text="Remove Selected", command=self.remove_selected).pack(side="left", padx=5)

        # Finish
        tk.Button(self.root, text="Finish", command=self.finish).pack(pady=5)

        # Bindings
        self.listbox.bind("<Return>", self.on_enter)
        self.listbox.bind("<Double-1>", self.on_enter)
        self.root.bind("<Left>", self.on_left_arrow_key)

        # Watchers
        self.sort_var.trace_add("write", self.update_listbox)
        self.sort_formats_var.trace_add("write", lambda *a: self.update_listbox())

        self.update_listbox()

    # ------------------ Deck Save/Load ------------------
    def save_deck(self):
        deck_name = simpledialog.askstring("Save Deck", "Enter deck name:")
        if not deck_name:
            return
        path = os.path.join(DECKS_DIR, f"{deck_name}.json")
        deck_data = {
            "main": self.main_deck,
            "extra": self.extra_deck,
            "side": self.side_deck
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(deck_data, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("Deck Saved", f"Deck saved to {path}")

    def load_deck(self):
        path = filedialog.askopenfilename(initialdir=DECKS_DIR, title="Select deck JSON", filetypes=[("JSON Files", "*.json")])
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            deck_data = json.load(f)
        self.main_deck = deck_data.get("main", {})
        self.extra_deck = deck_data.get("extra", {})
        self.side_deck = deck_data.get("side", {})
        self.update_deck_display()

    # ------------------ Deck Editing ------------------
    def add_selected(self):
        selections = self.listbox.curselection()
        if not selections:
            return
        try:
            copies = int(self.copies_var.get())
            if copies < 1:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Input", "Copies must be a positive integer.")
            return

        for idx in selections:
            name = self.listbox.get(idx).rsplit(" (", 1)[0]
            # Prevent adding formats as cards
            if self.mode_var.get() == "format" and self.current_format_stage == "format_select":
                continue
            deck_section = getattr(self, f"{self.current_section.get()}_deck")
            deck_section[name] = deck_section.get(name, 0) + copies

        self.update_deck_display()

    def remove_selected(self):
        selections = self.listbox.curselection()
        if not selections:
            return

        for idx in selections:
            name = self.listbox.get(idx).rsplit(" (", 1)[0]
            for section in [self.main_deck, self.extra_deck, self.side_deck]:
                if name in section:
                    del section[name]

        self.update_deck_display()

    def update_deck_display(self):
        # Clear existing lists
        self.main_listbox.delete(0, tk.END)
        self.extra_listbox.delete(0, tk.END)
        self.side_listbox.delete(0, tk.END)

        def add_cards_to_listbox(listbox, deck):
            counts = Counter(deck)  # Count duplicates
            for card, qty in counts.items():
                if qty > 1:
                    listbox.insert(tk.END, f"{card} ({qty}x)")
                else:
                    listbox.insert(tk.END, card)

        add_cards_to_listbox(self.main_listbox, self.main_deck)
        add_cards_to_listbox(self.extra_listbox, self.extra_deck)
        add_cards_to_listbox(self.side_listbox, self.side_deck)

    # ------------------ Navigation ------------------
    def on_enter(self, event=None):
        selection = self.listbox.curselection()
        if not selection:
            return
        name = self.listbox.get(selection[0]).rsplit(" (", 1)[0]
        if self.mode_var.get() == "all":
            show_card_preview(name)
        else:
            if self.current_format_stage == "format_select":
                self.selected_format = name
                self.current_format_stage = "cards"
                self.update_listbox()
            elif self.current_format_stage == "cards":
                show_card_preview(name)

    def on_left_arrow_key(self, event=None):
        if self.mode_var.get() == "format" and self.current_format_stage == "cards":
            self.current_format_stage = "format_select"
            self.selected_format = None
            self.update_listbox()

    # ------------------ Finish ------------------
    def finish(self):
        # Enforce deck rules
        if not (1 <= sum(self.main_deck.values()) <= 60):
            messagebox.showerror("Error", "Main Deck must have between 1 and 60 cards.")
            return
        if sum(self.extra_deck.values()) > 15:
            messagebox.showerror("Error", "Extra Deck cannot exceed 15 cards.")
            return
        if sum(self.side_deck.values()) > 15:
            messagebox.showerror("Error", "Side Deck cannot exceed 15 cards.")
            return
        self.root.quit()
        self.root.destroy()

    # ---------- Update Listbox ----------
    def update_listbox(self, *args):
        self.listbox.delete(0, tk.END)
        query = self.search_var.get().strip().lower()
        if self.mode_var.get() == "all":
            if self.sort_var.get() == "By Level":
                items = sorted(YGOProDeck_Card_Info.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("level", 0) if YGOProDeck_Card_Info[x].get("level", 0) is not None else 0, reverse=True)
                for name in items:
                    if query and query not in name.lower():
                        continue
                    card_type = YGOProDeck_Card_Info[name]["type"]

                    # Only show extra deck cards if editing extra deck
                    if self.current_section.get() == "extra" and card_type not in EXTRA_DECK_TYPES:
                        continue
                    # Only show main/side cards if editing main or side deck
                    if self.current_section.get() in ["main", "side"] and card_type in EXTRA_DECK_TYPES:
                        continue
                    level = YGOProDeck_Card_Info[name].get("level", 0)
                    self.listbox.insert(tk.END, f"{name} ({level})")
            elif self.sort_var.get() == "By Attribute":
                items = sorted(YGOProDeck_Card_Info.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("attribute", "None"))
                for name in items:
                    if query and query not in name.lower():
                        continue
                    card_type = YGOProDeck_Card_Info[name]["type"]

                    # Only show extra deck cards if editing extra deck
                    if self.current_section.get() == "extra" and card_type not in EXTRA_DECK_TYPES:
                        continue
                    # Only show main/side cards if editing main or side deck
                    if self.current_section.get() in ["main", "side"] and card_type in EXTRA_DECK_TYPES:
                        continue
                    attribute = YGOProDeck_Card_Info[name].get("attribute", "None")
                    self.listbox.insert(tk.END, f"{name} ({attribute})")
            elif self.sort_var.get() == "By ATK":
                items = sorted(YGOProDeck_Card_Info.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("atk", 0), reverse=True)
                for name in items:
                    if query and query not in name.lower():
                        continue
                    card_type = YGOProDeck_Card_Info[name]["type"]

                    # Only show extra deck cards if editing extra deck
                    if self.current_section.get() == "extra" and card_type not in EXTRA_DECK_TYPES:
                        continue
                    # Only show main/side cards if editing main or side deck
                    if self.current_section.get() in ["main", "side"] and card_type in EXTRA_DECK_TYPES:
                        continue
                    atk = YGOProDeck_Card_Info[name].get("atk", 0)
                    self.listbox.insert(tk.END, f"{name} ({atk})")
            elif self.sort_var.get() == "By DEF":
                items = sorted(YGOProDeck_Card_Info.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("def", 0) if YGOProDeck_Card_Info[x].get("def", 0) is not None else 0, reverse=True)
                for name in items:
                    if query and query not in name.lower():
                        continue
                    card_type = YGOProDeck_Card_Info[name]["type"]

                    # Only show extra deck cards if editing extra deck
                    if self.current_section.get() == "extra" and card_type not in EXTRA_DECK_TYPES:
                        continue
                    # Only show main/side cards if editing main or side deck
                    if self.current_section.get() in ["main", "side"] and card_type in EXTRA_DECK_TYPES:
                        continue
                    defn = YGOProDeck_Card_Info[name].get("def", 0)
                    self.listbox.insert(tk.END, f"{name} ({defn})")
            elif self.sort_var.get() == "By Race":
                items = sorted(YGOProDeck_Card_Info.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("race", "None"))
                for name in items:
                    if query and query not in name.lower():
                        continue
                    card_type = YGOProDeck_Card_Info[name]["type"]

                    # Only show extra deck cards if editing extra deck
                    if self.current_section.get() == "extra" and card_type not in EXTRA_DECK_TYPES:
                        continue
                    # Only show main/side cards if editing main or side deck
                    if self.current_section.get() in ["main", "side"] and card_type in EXTRA_DECK_TYPES:
                        continue
                    race = YGOProDeck_Card_Info[name].get("race", "None")
                    self.listbox.insert(tk.END, f"{name} ({race})")
            elif self.sort_var.get() == "By Type":
                items = sorted(YGOProDeck_Card_Info.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("type", "None"))
                for name in items:
                    if query and query not in name.lower():
                        continue
                    card_type = YGOProDeck_Card_Info[name]["type"]

                    # Only show extra deck cards if editing extra deck
                    if self.current_section.get() == "extra" and card_type not in EXTRA_DECK_TYPES:
                        continue
                    # Only show main/side cards if editing main or side deck
                    if self.current_section.get() in ["main", "side"] and card_type in EXTRA_DECK_TYPES:
                        continue
                    type_ = YGOProDeck_Card_Info[name].get("type", "None")
                    self.listbox.insert(tk.END, f"{name} ({type_})")
            elif self.sort_var.get() == "By Konami ID":
                items = sorted(YGOProDeck_Card_Info.keys(), key=lambda x: YGOProDeck_Card_Info[x]['misc_info'][0].get("konami_id", 0))
                for name in items:
                    if query and query not in name.lower():
                        continue
                    card_type = YGOProDeck_Card_Info[name]["type"]

                    # Only show extra deck cards if editing extra deck
                    if self.current_section.get() == "extra" and card_type not in EXTRA_DECK_TYPES:
                        continue
                    # Only show main/side cards if editing main or side deck
                    if self.current_section.get() in ["main", "side"] and card_type in EXTRA_DECK_TYPES:
                        continue
                    konami_id = YGOProDeck_Card_Info[name]['misc_info'][0].get("konami_id", 0)
                    self.listbox.insert(tk.END, f"{name} ({konami_id})")
            else:
                for name in sorted(YGOProDeck_Card_Info.keys()):
                    if query and query not in name.lower():
                        continue
                    card_type = YGOProDeck_Card_Info[name]["type"]

                    # Only show extra deck cards if editing extra deck
                    if self.current_section.get() == "extra" and card_type not in EXTRA_DECK_TYPES:
                        continue
                    # Only show main/side cards if editing main or side deck
                    if self.current_section.get() in ["main", "side"] and card_type in EXTRA_DECK_TYPES:
                        continue
                    self.listbox.insert(tk.END, name)
        else:
            if self.current_format_stage == "format_select":
                self.selected_format = None
                for fmt in sorted(format_data.keys()):
                    self.listbox.insert(tk.END, fmt)
            elif self.current_format_stage == "cards" and self.selected_format:
                cards_for_format = format_data[self.selected_format]
                # Sort
                if self.sort_var.get() == "Alphabetical":
                    items = sorted(cards_for_format.keys())
                elif self.sort_var.get() == "By Usage Count":  # By Usage Count descending
                    items = sorted(cards_for_format.keys(), key=lambda x: cards_for_format[x].get("count", 1), reverse=True)
                if self.sort_var.get() == "Alphabetical" or self.sort_var.get() == "By Usage Count":
                    # Insert with counts
                    for name in items:
                        if query and query not in name.lower():
                            continue
                        card_type = YGOProDeck_Card_Info[name]["type"]

                        # Only show extra deck cards if editing extra deck
                        if self.current_section.get() == "extra" and card_type not in EXTRA_DECK_TYPES:
                            continue
                        # Only show main/side cards if editing main or side deck
                        if self.current_section.get() in ["main", "side"] and card_type in EXTRA_DECK_TYPES:
                            continue
                        count = cards_for_format[name].get("count", 1)
                        self.listbox.insert(tk.END, f"{name} ({count})")
                elif self.sort_var.get() == "By Level":
                    items = sorted(cards_for_format.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("level", 0) if YGOProDeck_Card_Info[x].get("level", 0) is not None else 0, reverse=True)
                    for name in items:
                        if query and query not in name.lower():
                            continue
                        card_type = YGOProDeck_Card_Info[name]["type"]

                        # Only show extra deck cards if editing extra deck
                        if self.current_section.get() == "extra" and card_type not in EXTRA_DECK_TYPES:
                            continue
                        # Only show main/side cards if editing main or side deck
                        if self.current_section.get() in ["main", "side"] and card_type in EXTRA_DECK_TYPES:
                            continue
                        level = YGOProDeck_Card_Info[name].get("level", 0)
                        self.listbox.insert(tk.END, f"{name} ({level})")
                elif self.sort_var.get() == "By Attribute":
                    items = sorted(cards_for_format.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("attribute", "None"))
                    for name in items:
                        if query and query not in name.lower():
                            continue
                        card_type = YGOProDeck_Card_Info[name]["type"]

                        # Only show extra deck cards if editing extra deck
                        if self.current_section.get() == "extra" and card_type not in EXTRA_DECK_TYPES:
                            continue
                        # Only show main/side cards if editing main or side deck
                        if self.current_section.get() in ["main", "side"] and card_type in EXTRA_DECK_TYPES:
                            continue
                        attribute = YGOProDeck_Card_Info[name].get("attribute", "None")
                        self.listbox.insert(tk.END, f"{name} ({attribute})")
                elif self.sort_var.get() == "By ATK":
                    items = sorted(cards_for_format.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("atk", 0), reverse=True)
                    for name in items:
                        if query and query not in name.lower():
                            continue
                        card_type = YGOProDeck_Card_Info[name]["type"]

                        # Only show extra deck cards if editing extra deck
                        if self.current_section.get() == "extra" and card_type not in EXTRA_DECK_TYPES:
                            continue
                        # Only show main/side cards if editing main or side deck
                        if self.current_section.get() in ["main", "side"] and card_type in EXTRA_DECK_TYPES:
                            continue
                        atk = YGOProDeck_Card_Info[name].get("atk", 0)
                        self.listbox.insert(tk.END, f"{name} ({atk})")
                elif self.sort_var.get() == "By DEF":
                    items = sorted(cards_for_format.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("def", 0) if YGOProDeck_Card_Info[x].get("def", 0) is not None else 0, reverse=True)
                    for name in items:
                        if query and query not in name.lower():
                            continue
                        card_type = YGOProDeck_Card_Info[name]["type"]

                        # Only show extra deck cards if editing extra deck
                        if self.current_section.get() == "extra" and card_type not in EXTRA_DECK_TYPES:
                            continue
                        # Only show main/side cards if editing main or side deck
                        if self.current_section.get() in ["main", "side"] and card_type in EXTRA_DECK_TYPES:
                            continue
                        defn = YGOProDeck_Card_Info[name].get("def", 0)
                        self.listbox.insert(tk.END, f"{name} ({defn})")
                elif self.sort_var.get() == "By Race":
                    items = sorted(cards_for_format.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("race", "None"))
                    for name in items:
                        if query and query not in name.lower():
                            continue
                        card_type = YGOProDeck_Card_Info[name]["type"]

                        # Only show extra deck cards if editing extra deck
                        if self.current_section.get() == "extra" and card_type not in EXTRA_DECK_TYPES:
                            continue
                        # Only show main/side cards if editing main or side deck
                        if self.current_section.get() in ["main", "side"] and card_type in EXTRA_DECK_TYPES:
                            continue
                        race = YGOProDeck_Card_Info[name].get("race", "None")
                        self.listbox.insert(tk.END, f"{name} ({race})")
                elif self.sort_var.get() == "By Type":
                    items = sorted(cards_for_format.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("type", "None"))
                    for name in items:
                        if query and query not in name.lower():
                            continue
                        card_type = YGOProDeck_Card_Info[name]["type"]

                        # Only show extra deck cards if editing extra deck
                        if self.current_section.get() == "extra" and card_type not in EXTRA_DECK_TYPES:
                            continue
                        # Only show main/side cards if editing main or side deck
                        if self.current_section.get() in ["main", "side"] and card_type in EXTRA_DECK_TYPES:
                            continue
                        type_ = YGOProDeck_Card_Info[name].get("type", "None")
                        self.listbox.insert(tk.END, f"{name} ({type_})")
                elif self.sort_var.get() == "By Konami ID":
                    items = sorted(cards_for_format.keys(), key=lambda x: YGOProDeck_Card_Info[x]['misc_info'][0].get("konami_id", 0))
                    for name in items:
                        if query and query not in name.lower():
                            continue
                        card_type = YGOProDeck_Card_Info[name]["type"]

                        # Only show extra deck cards if editing extra deck
                        if self.current_section.get() == "extra" and card_type not in EXTRA_DECK_TYPES:
                            continue
                        # Only show main/side cards if editing main or side deck
                        if self.current_section.get() in ["main", "side"] and card_type in EXTRA_DECK_TYPES:
                            continue
                        konami_id = YGOProDeck_Card_Info[name]['misc_info'][0].get("konami_id", 0)
                        self.listbox.insert(tk.END, f"{name} ({konami_id})")


# ------------- Entry point -------------
def build_deck_interactively():
    root = tk.Tk()
    app = DeckBuilder(root)
    root.mainloop()
    return {
        "main": app.main_deck,
        "extra": app.extra_deck,
        "side": app.side_deck
    }
