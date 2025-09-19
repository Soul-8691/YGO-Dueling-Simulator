import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
import json
import os
import requests
from io import BytesIO
from PIL import Image, ImageTk

DECKS_DIR = "decks"
os.makedirs(DECKS_DIR, exist_ok=True)

# Load card info and format library
with open("YGOProDeck_Card_Info.json", "r", encoding="utf-8") as f:
    data = json.load(f)
YGOProDeck_Card_Info = {c["name"]: c for c in data["data"]}

with open("cards_by_format_updated.json", "r", encoding="utf-8") as f:
    format_data = json.load(f)

# ---------- Helper: Show Card Image ----------
def show_card_preview(card_name):
    try:
        card_id = YGOProDeck_Card_Info[card_name]["id"]
        url = f"https://db.ygoprodeck.com/api/v7/cardimages/{card_id}.jpg"
        resp = requests.get(url)
        resp.raise_for_status()
        img_data = resp.content
        pil_img = Image.open(BytesIO(img_data))
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

# ---------- Deck Builder ----------
def build_deck_interactively():
    deck = {}
    root = tk.Tk()
    root.title("Deck Builder")
    root.geometry("750x600")

    # --- Format sort option ---
    sort_formats_var = tk.StringVar(value="Alphabetical")
    sort_formats_var.trace_add("write", lambda *args: populate_format_list())

    # --- Sort Option (for Format Library) ---
    sort_var = tk.StringVar(value="Alphabetical")

    # --- Combined Sort Controls ---
    sort_frame = tk.Frame(root)
    sort_frame.pack(fill="x", padx=5, pady=2)

    # Sort Formats
    tk.Label(sort_frame, text="Sort Formats:").pack(side="left", padx=5)
    tk.OptionMenu(sort_frame, sort_formats_var, "Alphabetical", "By Date").pack(side="left", padx=5)

    # Sort Cards
    tk.Label(sort_frame, text="Sort Cards:").pack(side="left", padx=5)
    tk.OptionMenu(sort_frame, sort_var, "Alphabetical", "By Level", "By Attribute", "By ATK", "By DEF", "By Race", "By Type", "By Konami ID", "By Usage Count").pack(side="left", padx=5)

    def populate_format_list():
        listbox.delete(0, tk.END)
        formats = list(format_data.keys())
        if sort_formats_var.get() == "Alphabetical":
            formats.sort()
        else:  # By Date
            # Assuming each format has a 'date' key (ISO: YYYY-MM-DD)
            formats.sort(key=lambda f: format_data[f].get("date", "9999-12-31"))

        for fmt in formats:
            listbox.insert(tk.END, fmt)

    # --- Top Buttons ---
    def load_deck():
        path = filedialog.askopenfilename(initialdir=DECKS_DIR, title="Select deck JSON",
                                          filetypes=[("JSON Files", "*.json")])
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
                json.dump(deck, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Deck Saved", f"Deck saved to {path}")

    top_frame = tk.Frame(root)
    top_frame.pack(fill="x", padx=5, pady=5)
    tk.Button(top_frame, text="Load Deck", command=load_deck).pack(side="left", padx=5)
    tk.Button(top_frame, text="Save Deck", command=save_deck).pack(side="left", padx=5)

    # --- Mode selection ---
    mode_frame = tk.Frame(root)
    mode_frame.pack(fill="x", pady=5)
    mode_var = tk.StringVar(value="all")

    def switch_mode():
        nonlocal current_format_stage
        current_format_stage = "format_select"
        update_listbox()

    tk.Radiobutton(mode_frame, text="All Cards", variable=mode_var, value="all", command=switch_mode).pack(side="left")
    tk.Radiobutton(mode_frame, text="Format Library", variable=mode_var, value="format", command=switch_mode).pack(side="left")

    # --- Copies Entry ---
    copies_var = tk.StringVar(value="1")
    tk.Label(root, text="Copies to add").pack(side="left", padx=5)
    copies_entry = tk.Entry(root, textvariable=copies_var, width=5)
    copies_entry.pack(side="left", padx=5)

    # --- Listbox ---
    listbox_frame = tk.Frame(root)
    listbox_frame.pack(fill="both", expand=True)
    scrollbar = tk.Scrollbar(listbox_frame)
    scrollbar.pack(side="right", fill="y")
    listbox = tk.Listbox(listbox_frame, selectmode=tk.SINGLE, yscrollcommand=scrollbar.set)
    listbox.pack(fill="both", expand=True)
    scrollbar.config(command=listbox.yview)

    current_format_stage = "format_select"  # tracks Format Library navigation
    selected_format = None

    # ---------- Update Listbox ----------
    def update_listbox(*args):
        listbox.delete(0, tk.END)
        if mode_var.get() == "all":
            if sort_var.get() == "By Level":
                items = sorted(YGOProDeck_Card_Info.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("level", 0) if YGOProDeck_Card_Info[x].get("level", 0) is not None else 0, reverse=True)
                for name in items:
                    level = YGOProDeck_Card_Info[name].get("level", 0)
                    listbox.insert(tk.END, f"{name} ({level})")
            elif sort_var.get() == "By Attribute":
                items = sorted(YGOProDeck_Card_Info.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("attribute", "None"))
                for name in items:
                    attribute = YGOProDeck_Card_Info[name].get("attribute", "None")
                    listbox.insert(tk.END, f"{name} ({attribute})")
            elif sort_var.get() == "By ATK":
                items = sorted(YGOProDeck_Card_Info.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("atk", 0), reverse=True)
                for name in items:
                    atk = YGOProDeck_Card_Info[name].get("atk", 0)
                    listbox.insert(tk.END, f"{name} ({atk})")
            elif sort_var.get() == "By DEF":
                items = sorted(YGOProDeck_Card_Info.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("def", 0) if YGOProDeck_Card_Info[x].get("def", 0) is not None else 0, reverse=True)
                for name in items:
                    defn = YGOProDeck_Card_Info[name].get("def", 0)
                    listbox.insert(tk.END, f"{name} ({defn})")
            elif sort_var.get() == "By Race":
                items = sorted(YGOProDeck_Card_Info.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("race", "None"))
                for name in items:
                    race = YGOProDeck_Card_Info[name].get("race", "None")
                    listbox.insert(tk.END, f"{name} ({race})")
            elif sort_var.get() == "By Type":
                items = sorted(YGOProDeck_Card_Info.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("type", "None"))
                for name in items:
                    type_ = YGOProDeck_Card_Info[name].get("type", "None")
                    listbox.insert(tk.END, f"{name} ({type_})")
            elif sort_var.get() == "By Konami ID":
                items = sorted(YGOProDeck_Card_Info.keys(), key=lambda x: YGOProDeck_Card_Info[x]['misc_info'][0].get("konami_id", 0))
                for name in items:
                    konami_id = YGOProDeck_Card_Info[name]['misc_info'][0].get("konami_id", 0)
                    listbox.insert(tk.END, f"{name} ({konami_id})")
            else:
                for name in sorted(YGOProDeck_Card_Info.keys()):
                    listbox.insert(tk.END, name)
        else:
            nonlocal selected_format
            if current_format_stage == "format_select":
                selected_format = None
                for fmt in sorted(format_data.keys()):
                    listbox.insert(tk.END, fmt)
            elif current_format_stage == "cards" and selected_format:
                cards_for_format = format_data[selected_format]
                # Sort
                if sort_var.get() == "Alphabetical":
                    items = sorted(cards_for_format.keys())
                elif sort_var.get() == "By Usage Count":  # By Usage Count descending
                    items = sorted(cards_for_format.keys(), key=lambda x: cards_for_format[x].get("count", 1), reverse=True)
                if sort_var.get() == "Alphabetical" or sort_var.get() == "By Usage Count":
                    # Insert with counts
                    for name in items:
                        count = cards_for_format[name].get("count", 1)
                        listbox.insert(tk.END, f"{name} ({count})")
                elif sort_var.get() == "By Level":
                    items = sorted(cards_for_format.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("level", 0) if YGOProDeck_Card_Info[x].get("level", 0) is not None else 0, reverse=True)
                    for name in items:
                        level = YGOProDeck_Card_Info[name].get("level", 0)
                        listbox.insert(tk.END, f"{name} ({level})")
                elif sort_var.get() == "By Attribute":
                    items = sorted(cards_for_format.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("attribute", "None"))
                    for name in items:
                        attribute = YGOProDeck_Card_Info[name].get("attribute", "None")
                        listbox.insert(tk.END, f"{name} ({attribute})")
                elif sort_var.get() == "By ATK":
                    items = sorted(cards_for_format.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("atk", 0), reverse=True)
                    for name in items:
                        atk = YGOProDeck_Card_Info[name].get("atk", 0)
                        listbox.insert(tk.END, f"{name} ({atk})")
                elif sort_var.get() == "By DEF":
                    items = sorted(cards_for_format.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("def", 0) if YGOProDeck_Card_Info[x].get("def", 0) is not None else 0, reverse=True)
                    for name in items:
                        defn = YGOProDeck_Card_Info[name].get("def", 0)
                        listbox.insert(tk.END, f"{name} ({defn})")
                elif sort_var.get() == "By Race":
                    items = sorted(cards_for_format.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("race", "None"))
                    for name in items:
                        race = YGOProDeck_Card_Info[name].get("race", "None")
                        listbox.insert(tk.END, f"{name} ({race})")
                elif sort_var.get() == "By Type":
                    items = sorted(cards_for_format.keys(), key=lambda x: YGOProDeck_Card_Info[x].get("type", "None"))
                    for name in items:
                        type_ = YGOProDeck_Card_Info[name].get("type", "None")
                        listbox.insert(tk.END, f"{name} ({type_})")
                elif sort_var.get() == "By Konami ID":
                    items = sorted(cards_for_format.keys(), key=lambda x: YGOProDeck_Card_Info[x]['misc_info'][0].get("konami_id", 0))
                    for name in items:
                        konami_id = YGOProDeck_Card_Info[name]['misc_info'][0].get("konami_id", 0)
                        listbox.insert(tk.END, f"{name} ({konami_id})")

    sort_var.trace_add("write", update_listbox)
    update_listbox()

    # ---------- Deck Display ----------
    deck_text = tk.Text(root, height=10)
    deck_text.pack(fill="both", expand=True, padx=5, pady=5)

    def update_deck_display():
        deck_text.delete("1.0", tk.END)
        for name, count in sorted(deck.items()):
            deck_text.insert(tk.END, f"{name}: {count}\n")

    # ---------- Add / Remove ----------
    def add_selected():
        selection = listbox.curselection()
        if not selection:
            return
        try:
            copies = int(copies_var.get())
            if copies < 1:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Input", "Copies must be a positive integer.")
            return

        name = listbox.get(selection[0]).rsplit(" (", 1)[0]  # remove " (count)"
        # prevent formats from being added as cards
        if mode_var.get() == "format" and current_format_stage == "format_select":
            return
        if name in YGOProDeck_Card_Info:
            deck[name] = deck.get(name, 0) + copies
            update_deck_display()

    def remove_selected():
        selection = listbox.curselection()
        if not selection:
            return
        name = listbox.get(selection[0])
        if name in deck:
            del deck[name]
            update_deck_display()

    control_frame = tk.Frame(root)
    control_frame.pack(pady=5)
    tk.Button(control_frame, text="Add Selected", command=add_selected).pack(side="left", padx=5)
    tk.Button(control_frame, text="Remove Selected", command=remove_selected).pack(side="left", padx=5)

    # ---------- Navigation ----------
    def on_enter(event=None):
        selection = listbox.curselection()
        if not selection:
            return
        name = listbox.get(selection[0])
        if mode_var.get() == "all":
            show_card_preview(name)
        else:
            nonlocal current_format_stage, selected_format
            if current_format_stage == "format_select":
                selected_format = name
                current_format_stage = "cards"
                update_listbox()
            elif current_format_stage == "cards":
                show_card_preview(name)

    def on_backspace(event=None):
        nonlocal current_format_stage, selected_format
        if mode_var.get() == "format" and current_format_stage == "cards":
            current_format_stage = "format_select"
            selected_format = None
            update_listbox()

    listbox.bind("<Return>", on_enter)
    listbox.bind("<Double-1>", on_enter)
    root.bind("<BackSpace>", on_backspace)

    # ---------- Finish ----------
    def finish():
        root.destroy()

    tk.Button(root, text="Finish", command=finish).pack(pady=5)

    root.mainloop()
    return deck
