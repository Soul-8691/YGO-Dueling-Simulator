import tkinter as tk
from tkinter import simpledialog, messagebox, Tk, filedialog
import json
import os

DECKS_DIR = "decks"
os.makedirs(DECKS_DIR, exist_ok=True)

# Load YGOProDeck card info
with open("YGOProDeck_Card_Info.json", "r", encoding="utf-8") as f:
    data = json.load(f)
YGOProDeck_Card_Info = {c["name"]: c for c in data["data"]}

class DeckBuilder(tk.Toplevel):
    def __init__(self, master, callback):
        super().__init__(master)
        self.title("Deck Builder")
        self.state("zoomed")
        self.callback = callback
        self.deck = {}  # card name -> count

        self.all_cards = sorted(YGOProDeck_Card_Info.keys())

        # --- Search and listbox ---
        tk.Label(self, text="Available Cards").pack(pady=5)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.update_list)
        tk.Entry(self, textvariable=self.search_var).pack(fill="x", padx=10)

        self.card_listbox = tk.Listbox(self, selectmode=tk.SINGLE)
        self.card_listbox.pack(fill="both", expand=True, padx=10, pady=5)
        for name in self.all_cards:
            self.card_listbox.insert(tk.END, name)

        # --- Add / Remove ---
        control_frame = tk.Frame(self)
        control_frame.pack(pady=5)
        tk.Button(control_frame, text="Add Card", command=self.add_card).pack(side="left", padx=5)
        tk.Button(control_frame, text="Remove Card", command=self.remove_card).pack(side="left", padx=5)

        # --- Deck display ---
        tk.Label(self, text="Current Deck").pack(pady=5)
        self.deck_listbox = tk.Listbox(self)
        self.deck_listbox.pack(fill="both", expand=True, padx=10, pady=5)

        # --- Save / Confirm ---
        tk.Button(self, text="Confirm Deck", command=self.confirm).pack(pady=5)

    def update_list(self, *args):
        search = self.search_var.get().lower()
        self.card_listbox.delete(0, tk.END)
        for name in self.all_cards:
            if search in name.lower():
                self.card_listbox.insert(tk.END, name)

    def add_card(self):
        selection = self.card_listbox.curselection()
        if not selection:
            return
        name = self.card_listbox.get(selection[0])
        self.deck[name] = self.deck.get(name, 0) + 1
        self.update_deck_listbox()

    def remove_card(self):
        selection = self.deck_listbox.curselection()
        if not selection:
            return
        name = self.deck_listbox.get(selection[0]).split(" x")[0]
        if name in self.deck:
            self.deck[name] -= 1
            if self.deck[name] <= 0:
                del self.deck[name]
        self.update_deck_listbox()

    def update_deck_listbox(self):
        self.deck_listbox.delete(0, tk.END)
        for name, count in sorted(self.deck.items()):
            self.deck_listbox.insert(tk.END, f"{name} x{count}")

    def confirm(self):
        total_cards = sum(self.deck.values())
        if total_cards < 1:
            messagebox.showerror("Error", "Deck must have at least 1 card")
            return
        self.destroy()
        self.callback(self.deck)

def save_deck(deck_name, deck_dict):
    path = os.path.join(DECKS_DIR, f"{deck_name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(deck_dict, f, ensure_ascii=False, indent=2)
    print(f"Deck '{deck_name}' saved to {path}")

def load_deck(deck_name):
    """Load a deck by name (returns dict with card names as keys and counts as values)."""
    path = os.path.join(DECKS_DIR, f"{deck_name}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Deck '{deck_name}' not found.")
    with open(path, "r", encoding="utf-8") as f:
        deck = json.load(f)
    return deck

def build_deck_interactively():
    """
    Opens a GUI to build a deck interactively or load an existing one.
    Returns: deck dict {card_name: count} or None if cancelled
    """
    deck = {}

    root = tk.Tk()
    root.title("Deck Builder")
    root.geometry("600x500")

    # --- Top buttons for Load/Save ---
    def load_deck():
        path = filedialog.askopenfilename(
            initialdir=DECKS_DIR,
            title="Select deck JSON",
            filetypes=[("JSON Files", "*.json")]
        )
        if path:
            with open(path, "r", encoding="utf-8") as f:
                loaded_deck = json.load(f)
            deck.clear()
            deck.update(loaded_deck)
            update_deck_display()

    def save_deck():
        deck_name = simpledialog.askstring("Save Deck", "Enter deck name:")
        if deck_name:
            path = os.path.join(DECKS_DIR, f"{deck_name}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(deck, f, indent=2)
            messagebox.showinfo("Saved", f"Deck saved to {path}")

    top_frame = tk.Frame(root)
    top_frame.pack(fill="x", padx=5, pady=5)
    tk.Button(top_frame, text="Load Deck", command=load_deck).pack(side="left", padx=5)
    tk.Button(top_frame, text="Save Deck", command=save_deck).pack(side="left", padx=5)

    # --- Search bar with placeholder ---
    search_var = tk.StringVar(value="")
    card_names = sorted(YGOProDeck_Card_Info.keys())

    search_entry = tk.Entry(root, textvariable=search_var)
    search_entry.pack(fill="x", padx=5, pady=5)

    placeholder = "Search cards..."
    search_var.set("")  # start empty

    def on_entry_focus_in(event):
        if search_var.get() == placeholder:
            search_var.set("")

    def on_entry_focus_out(event):
        if not search_var.get():
            search_var.set("")

    search_entry.bind("<FocusIn>", on_entry_focus_in)
    search_entry.bind("<FocusOut>", on_entry_focus_out)

    # --- Listbox ---
    listbox_frame = tk.Frame(root)
    listbox_frame.pack(fill="both", expand=True)

    scrollbar = tk.Scrollbar(listbox_frame)
    scrollbar.pack(side="right", fill="y")

    listbox = tk.Listbox(listbox_frame, selectmode=tk.MULTIPLE, yscrollcommand=scrollbar.set)
    listbox.pack(fill="both", expand=True)
    scrollbar.config(command=listbox.yview)

    def update_list(*args):
        term = search_var.get().lower()
        listbox.delete(0, tk.END)
        for name in card_names:
            if term in name.lower() or term == "":
                listbox.insert(tk.END, name)

    search_var.trace_add("write", update_list)

    # Initialize list with all cards
    update_list()

    # --- Copies Entry ---
    copies_var = tk.StringVar(value="1")
    copies_entry = tk.Entry(root, textvariable=copies_var, width=5)
    copies_entry.pack(side="left", padx=5, pady=5)
    tk.Label(root, text="Copies to add").pack(side="left")

    # --- Add/Remove Buttons ---
    def add_selected():
        selected = listbox.curselection()
        try:
            copies = int(copies_var.get())
            if copies < 1:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Input", "Copies must be a positive integer.")
            return
        for idx in selected:
            name = listbox.get(idx)
            deck[name] = deck.get(name, 0) + copies
        update_deck_display()

    def remove_selected():
        selected = listbox.curselection()
        for idx in selected:
            name = listbox.get(idx)
            if name in deck:
                del deck[name]
        update_deck_display()

    tk.Button(root, text="Add Selected", command=add_selected).pack(side="left", padx=5)
    tk.Button(root, text="Remove Selected", command=remove_selected).pack(side="left", padx=5)

    # --- Deck display ---
    deck_text = tk.Text(root, height=10)
    deck_text.pack(fill="both", expand=True, padx=5, pady=5)

    def update_deck_display():
        deck_text.delete("1.0", tk.END)
        for name, count in sorted(deck.items()):
            deck_text.insert(tk.END, f"{name}: {count}\n")

    # --- Finish button ---
    def finish():
        if not deck:
            if not messagebox.askyesno("Empty Deck", "Deck is empty. Continue?"):
                return
        root.destroy()

    tk.Button(root, text="Finish", command=finish).pack(pady=5)

    root.mainloop()
    return deck

def build_or_load_deck():
    """
    Interactively either build a new deck or load an existing one.
    Returns a deck dict: {card_name: count}
    """
    # Create a temporary root for dialogs
    root = Tk()
    root.withdraw()  # hide main window

    try:
        choice = simpledialog.askstring(
            "Deck Option",
            "Type 'load' to load an existing deck, or 'new' to create a new deck:"
        )
        if not choice:
            return None

        choice = choice.lower().strip()

        if choice == "load":
            decks = [f[:-5] for f in os.listdir(DECKS_DIR) if f.endswith(".json")]
            if not decks:
                messagebox.showinfo("No Decks", "No saved decks found. Please build one first.")
                return None

            deck_name = simpledialog.askstring(
                "Select Deck",
                f"Available decks:\n{', '.join(decks)}\n\nEnter deck name:"
            )
            if not deck_name or deck_name not in decks:
                messagebox.showwarning("Invalid Deck", "Deck not found or cancelled.")
                return None

            path = os.path.join(DECKS_DIR, f"{deck_name}.json")
            with open(path, "r", encoding="utf-8") as f:
                deck = json.load(f)
            return deck

        elif choice == "new":
            deck = build_deck_interactively()  # this should create its own root
            if deck:
                messagebox.showinfo("Deck Saved", "Deck created successfully!")
                deck_name = simpledialog.askstring("Save Deck", "Enter a name to save this deck:")
                if deck_name:
                    path = os.path.join(DECKS_DIR, f"{deck_name}.json")
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(deck, f, ensure_ascii=False, indent=2)
                    messagebox.showinfo("Deck Saved", f"Saved to {path}")
            return deck

        else:
            messagebox.showwarning("Invalid Choice", "Please type 'load' or 'new'.")
            return None

    finally:
        root.destroy()  # always destroy root at the end

# Example usage:
if __name__ == "__main__":
    deck = build_deck_interactively()
    print("Deck built:", deck)
