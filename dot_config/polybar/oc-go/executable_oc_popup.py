#!/usr/bin/env python3
"""Popup stato piano OpenCode Go (legge cache, toggle come nc-popup)."""
import argparse
import json
import os
import tkinter as tk
from datetime import datetime, timezone

BG, FG = "#282A36", "#F8F8F2"
ACCENT, RED, GRAY, ORANGE = "#50FA7B", "#FF5555", "#6272A4", "#FFB86C"
FONT = ("JetBrainsMono Nerd Font", 10)
CACHE = os.path.expanduser("~/.cache/polybar/oc-go/status.json")


def load():
    try:
        with open(CACHE) as f:
            return json.load(f)
    except Exception:
        return None


def bar(parent, label, pct, row):
    tk.Label(parent, text=label, bg=BG, fg=GRAY, font=FONT,
             anchor="w").grid(row=row, column=0, sticky="w")
    c = ACCENT if pct < 70 else ORANGE if pct < 90 else RED
    tk.Label(parent, text=f"{pct:.1f}%", bg=BG, fg=c, font=FONT,
             anchor="w").grid(row=row, column=1, sticky="w", padx=8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--posx", type=int, default=100)
    ap.add_argument("--posy", type=int, default=100)
    ap.add_argument("--width", type=int, default=420)
    ap.add_argument("--height", type=int, default=340)
    args = ap.parse_args()
    d = load()

    root = tk.Tk()
    root.title("oc-popup")
    root.configure(bg=BG)
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.geometry(f"{args.width}x{args.height}+{args.posx}+{args.posy}")

    tk.Label(root, text=" OpenCode Go", bg=BG, fg=FG,
             font=("JetBrainsMono Nerd Font", 12, "bold")).pack(pady=(10, 2))
    body = tk.Frame(root, bg=BG)
    body.pack(fill="both", expand=True, padx=15, pady=5)
    r = 0
    if not d:
        tk.Label(body, text="cache assente: sync in corso…", bg=BG, fg=GRAY,
                 font=FONT).grid(row=0, column=0, sticky="w")
    else:
        w = d["windows"]
        tk.Label(body, text=f"piano: {d['plan']} · complessivo, solo CLI/TUI locale",
                 bg=BG, fg=FG, font=FONT, anchor="w").grid(
            row=r, column=0, columnspan=2, sticky="w")
        r += 1
        bar(body, "5 ore (tetto $12):", w["h5"]["pct"], r)
        tk.Label(body, text=f"${w['h5']['spent']} / ${w['h5']['cap']}",
                 bg=BG, fg=GRAY, font=FONT).grid(row=r, column=2, sticky="w")
        r += 1
        bar(body, "7 giorni (tetto $30):", w["week"]["pct"], r)
        tk.Label(body, text=f"${w['week']['spent']} / ${w['week']['cap']}",
                 bg=BG, fg=GRAY, font=FONT).grid(row=r, column=2, sticky="w")
        r += 1
        bar(body, "mese (tetto $60):", w["month"]["pct"], r)
        tk.Label(body, text=f"${w['month']['spent']} / ${w['month']['cap']}",
                 bg=BG, fg=GRAY, font=FONT).grid(row=r, column=2, sticky="w")
        r += 1
        tk.Label(body, text="top modelli (mese):", bg=BG, fg=GRAY,
                 font=FONT, anchor="w").grid(row=r, column=0, columnspan=3,
                                             sticky="w", pady=(6, 0))
        r += 1
        for t in d.get("top", [])[:5]:
            tk.Label(body, text=f"· {t['model']}", bg=BG, fg=FG,
                     font=FONT, anchor="w").grid(row=r, column=0,
                                                 columnspan=2, sticky="w")
            tk.Label(body, text=f"${t['cost']}", bg=BG, fg=GRAY,
                     font=FONT).grid(row=r, column=2, sticky="w")
            r += 1
        upd = datetime.fromtimestamp(d["updated"]).strftime("%d/%m %H:%M")
        tk.Label(body, text="pi e altri client: solo su dashboard", bg=BG, fg=GRAY,
                 font=FONT).grid(row=r, column=0, columnspan=3,
                                  sticky="w", pady=(6, 0))
        r += 1
        tk.Label(body, text=f"aggiornato: {upd}", bg=BG, fg=GRAY,
                 font=FONT).grid(row=r, column=0, columnspan=3,
                                  sticky="w", pady=(6, 0))
    root.bind("<Escape>", lambda e: root.destroy())
    root.mainloop()


if __name__ == "__main__":
    main()
