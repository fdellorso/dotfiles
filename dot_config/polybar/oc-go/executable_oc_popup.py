#!/usr/bin/env python3
"""Popup stato piano OpenCode Go (legge cache, toggle come nc-popup).

Modalita' server: % ufficiale + countdown da resetsAt, niente $.
Fallback locale: $ spesi/tetto, countdown non disponibile.
Barre testuali 0-100%, verde <70% · arancio <90% · rosso sopra.
"""
import argparse
import json
import os
import tkinter as tk
from datetime import datetime, timezone

BG, FG = "#282A36", "#F8F8F2"
ACCENT, RED, GRAY, ORANGE = "#50FA7B", "#FF5555", "#6272A4", "#FFB86C"
FONT = ("JetBrainsMono Nerd Font", 10)
CACHE = os.path.expanduser("~/.cache/polybar/oc-go/status.json")
BAR_WIDTH = 16


def load():
    try:
        with open(CACHE) as f:
            return json.load(f)
    except Exception:
        return None


def color(pct):
    if pct >= 90:
        return RED
    if pct >= 70:
        return ORANGE
    return ACCENT


def bar_text(pct):
    filled = round(max(0, min(100, pct)) / 100 * BAR_WIDTH)
    return "\u2501" * filled + "\u2500" * (BAR_WIDTH - filled)


def remaining(iso, now):
    if not iso:
        return "\u2014"
    try:
        target = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        ms = (target - now).total_seconds() * 1000
    except Exception:
        return "\u2014"
    if ms <= 0:
        return "now"
    minutes = int(ms // 60_000)
    days, rem = divmod(minutes, 1440)
    hours, mins = divmod(rem, 60)
    if days > 0:
        return f"{days}d {hours}h"
    if hours > 0:
        return f"{hours}h {mins}m"
    if minutes > 0:
        return f"{minutes}m"
    return "<1m"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--posx", type=int, default=100)
    ap.add_argument("--posy", type=int, default=100)
    ap.add_argument("--width", type=int, default=460)
    ap.add_argument("--height", type=int, default=360)
    args = ap.parse_args()
    d = load()
    now = datetime.now(timezone.utc)

    root = tk.Tk()
    root.title("oc-popup")
    root.configure(bg=BG)
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.geometry(f"{args.width}x{args.height}+{args.posx}+{args.posy}")

    tk.Label(root, text="\uf120 OpenCode Go", bg=BG, fg=FG,
             font=("JetBrainsMono Nerd Font", 12, "bold")).pack(pady=(10, 2))
    body = tk.Frame(root, bg=BG)
    body.pack(fill="both", expand=True, padx=15, pady=5)

    if not d:
        tk.Label(body, text="cache assente: sync in corso\u2026", bg=BG,
                 fg=GRAY, font=FONT).pack(anchor="w")
    else:
        src = d.get("source", "?")
        err = d.get("error")
        sub = ("fonte: server · tutti i client" if src == "server"
               else "fonte: locale · solo CLI/TUI di questa macchina")
        tk.Label(body, text=sub, bg=BG, fg=FG, font=FONT,
                 anchor="w").pack(anchor="w")
        if err:
            tk.Label(body, text=f"\u2717 {err} — dati locali", bg=BG,
                     fg=RED, font=FONT, anchor="w").pack(anchor="w")
        labels = (("h5", "5 ore"), ("week", "7 giorni"), ("month", "30 giorni"))
        for key, label in labels:
            w = d["windows"][key]
            pct = float(w.get("pct", 0))
            c = color(pct)
            row = tk.Frame(body, bg=BG)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=label.ljust(9), bg=BG, fg=GRAY,
                     font=FONT).pack(side="left")
            tk.Label(row, text=bar_text(pct), bg=BG, fg=c,
                     font=FONT).pack(side="left")
            tk.Label(row, text=f" {pct:.0f}%", bg=BG, fg=c,
                     font=FONT).pack(side="left")
            if w.get("resetsAt"):
                tk.Label(row, text=f"  \u21bb {remaining(w['resetsAt'], now)}",
                         bg=BG, fg=GRAY, font=FONT).pack(side="left")
            elif "spent" in w:
                tk.Label(row, text=f"  ${w['spent']} / ${w['cap']}",
                         bg=BG, fg=GRAY, font=FONT).pack(side="left")
        tk.Label(body, text="top modelli (locale, dal 1\u00ba):", bg=BG,
                 fg=GRAY, font=FONT, anchor="w").pack(anchor="w", pady=(6, 0))
        for t in d.get("top", [])[:5]:
            r = tk.Frame(body, bg=BG)
            r.pack(fill="x")
            tk.Label(r, text=f"\u00b7 {t['model']}"[:38], bg=BG, fg=FG,
                     font=FONT, anchor="w").pack(side="left")
            tk.Label(r, text=f"${t['cost']}", bg=BG, fg=GRAY,
                     font=FONT).pack(side="right")
        upd = datetime.fromtimestamp(d["updated"]).strftime("%d/%m %H:%M")
        tk.Label(body, text=f"aggiornato: {upd} (al click)",
                 bg=BG, fg=GRAY, font=FONT).pack(anchor="w", pady=(6, 0))
    root.bind("<Escape>", lambda e: root.destroy())
    root.mainloop()


if __name__ == "__main__":
    main()
