#!/usr/bin/env python3
"""
Calendar Popup for Polybar - Nextcloud Integration
Popup Tkinter con calendario navigabile, pallini eventi e lista appuntamenti.
"""

import tkinter as tk
from tkinter import font as tkfont
import calendar
import sys
import argparse
from datetime import datetime, date
from pathlib import Path
import json


# ─── Configurazione Colori (match polybar) ───────────────────────────────────
COLORS = {
    "bg":           "#282A2E",     # sfondo popup
    "bg_dark":      "#1E1F22",     # sfondo header
    "fg":           "#C5C8C6",     # testo principale
    "fg_dim":       "#707880",     # testo secondario
    "primary":      "#F0C674",     # giallo (oggi, header)
    "accent":       "#8ABEB7",     # verde/acqua (pallini eventi)
    "hover":        "#373B41",     # hover giorni
    "today_bg":     "#F0C674",     # sfondo oggi
    "today_fg":     "#282A2E",     # testo oggi
    "weekend_fg":   "#A54242",     # fine settimana
    "border":       "#373B41",     # bordi
    "event_dot":    "#8ABEB7",     # pallino evento
    "event_time":   "#F0C674",     # ora evento
    "event_title":  "#C5C8C6",     # titolo evento
    "nav_hover":    "#373B41",     # hover frecce
    "close_hover":  "#A54242",     # hover pulsante X
}

# ─── Mesi in italiano ─────────────────────────────────────────────────────────
MESI_IT = [
    "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
]

GIORNI_IT = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]

# ─── Caricamento Eventi da ICS ────────────────────────────────────────────────
CACHE_DIR = Path.home() / ".cache" / "polybar-calendar"
CACHE_FILE = CACHE_DIR / "events.json"


def load_events_from_cache():
    """Carica eventi dalla cache JSON (popolata dal sync script)."""
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)
        # Converte le date string in oggetti date
        events = {}
        for date_str, event_list in data.items():
            d = date.fromisoformat(date_str)
            events[d] = event_list
        return events
    except (json.JSONDecodeError, ValueError):
        return {}


def get_events_for_month(events, year, month):
    """Ritorna eventi filtrati per mese, ordinati per data."""
    month_events = {}
    for d, event_list in events.items():
        if d.year == year and d.month == month:
            month_events[d] = sorted(event_list, key=lambda e: e.get("time", ""))
    return month_events


# ─── Popup Calendario ─────────────────────────────────────────────────────────
class CalendarPopup:
    def __init__(self, pos_x, pos_y, width=420, height=480):
        self.root = tk.Tk()
        self.root.title("calendar-popup")
        self.root.overrideredirect(True)  # no titlebar
        self.root.attributes("-topmost", True)
        self.root.configure(bg=COLORS["bg"])

        # Dimensioni
        self.width = width
        self.height = height
        self.root.geometry(f"{self.width}x{self.height}+{pos_x}+{pos_y}")

        # Stato corrente
        today = date.today()
        self.current_year = today.year
        self.current_month = today.month
        self.today = today

        # Carica eventi
        self.all_events = load_events_from_cache()
        self.month_events = get_events_for_month(
            self.all_events, self.current_year, self.current_month
        )

        # Font
        self.font_header = tkfont.Font(family="JetBrainsMono Nerd Font", size=12, weight="bold")
        self.font_nav = tkfont.Font(family="JetBrainsMono Nerd Font", size=14)
        self.font_day_name = tkfont.Font(family="JetBrainsMono Nerd Font", size=10)
        self.font_day = tkfont.Font(family="JetBrainsMono Nerd Font", size=12)
        self.font_event_time = tkfont.Font(family="JetBrainsMono Nerd Font", size=9)
        self.font_event_title = tkfont.Font(family="JetBrainsMono Nerd Font", size=10)
        self.font_empty = tkfont.Font(family="JetBrainsMono Nerd Font", size=9)
        self.font_close = tkfont.Font(family="JetBrainsMono Nerd Font", size=12, weight="bold")

        # Costruisci UI
        self._build_header()
        self._build_calendar_grid()
        self._build_event_list()

        # Chiusura con Escape (bind_all per catturare ovunque)
        self.root.bind_all("<Escape>", lambda e: self._close())

    def _close(self):
        """Chiudi il popup."""
        self.root.destroy()

    def _build_header(self):
        """Header con navigazione mese/anno e pulsante chiudi."""
        header = tk.Frame(self.root, bg=COLORS["bg_dark"], height=40)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        # Pulsante chiudi (X)
        self.btn_close = tk.Label(
            header, text=" ✕ ", font=self.font_close,
            bg=COLORS["bg_dark"], fg=COLORS["fg_dim"], cursor="hand2"
        )
        self.btn_close.pack(side="right", padx=(0, 5))
        self.btn_close.bind("<Button-1>", lambda e: self._close())
        self.btn_close.bind("<Enter>", lambda e: self.btn_close.configure(bg=COLORS["close_hover"], fg=COLORS["fg"]))
        self.btn_close.bind("<Leave>", lambda e: self.btn_close.configure(bg=COLORS["bg_dark"], fg=COLORS["fg_dim"]))

        # Freccia anno successivo (esterna destra)
        self.btn_next_year = tk.Label(
            header, text=" ▶ ", font=self.font_nav,
            bg=COLORS["bg_dark"], fg=COLORS["fg_dim"], cursor="hand2"
        )
        self.btn_next_year.pack(side="right")
        self.btn_next_year.bind("<Button-1>", lambda e: self._change_year(1))
        self.btn_next_year.bind("<Enter>", lambda e: self.btn_next_year.configure(bg=COLORS["nav_hover"]))
        self.btn_next_year.bind("<Leave>", lambda e: self.btn_next_year.configure(bg=COLORS["bg_dark"]))

        # Freccia mese successivo (interna destra)
        self.btn_next_month = tk.Label(
            header, text=" ▸ ", font=self.font_nav,
            bg=COLORS["bg_dark"], fg=COLORS["fg_dim"], cursor="hand2"
        )
        self.btn_next_month.pack(side="right")
        self.btn_next_month.bind("<Button-1>", lambda e: self._change_month(1))
        self.btn_next_month.bind("<Enter>", lambda e: self.btn_next_month.configure(bg=COLORS["nav_hover"]))
        self.btn_next_month.bind("<Leave>", lambda e: self.btn_next_month.configure(bg=COLORS["bg_dark"]))

        # Freccia anno precedente (esterna sinistra)
        self.btn_prev_year = tk.Label(
            header, text=" ◀ ", font=self.font_nav,
            bg=COLORS["bg_dark"], fg=COLORS["fg_dim"], cursor="hand2"
        )
        self.btn_prev_year.pack(side="left", padx=(5, 0))
        self.btn_prev_year.bind("<Button-1>", lambda e: self._change_year(-1))
        self.btn_prev_year.bind("<Enter>", lambda e: self.btn_prev_year.configure(bg=COLORS["nav_hover"]))
        self.btn_prev_year.bind("<Leave>", lambda e: self.btn_prev_year.configure(bg=COLORS["bg_dark"]))

        # Freccia mese precedente (interna sinistra)
        self.btn_prev_month = tk.Label(
            header, text=" ◂ ", font=self.font_nav,
            bg=COLORS["bg_dark"], fg=COLORS["fg_dim"], cursor="hand2"
        )
        self.btn_prev_month.pack(side="left")
        self.btn_prev_month.bind("<Button-1>", lambda e: self._change_month(-1))
        self.btn_prev_month.bind("<Enter>", lambda e: self.btn_prev_month.configure(bg=COLORS["nav_hover"]))
        self.btn_prev_month.bind("<Leave>", lambda e: self.btn_prev_month.configure(bg=COLORS["bg_dark"]))

        # Titolo mese/anno (centrato con frame espandibile)
        center_frame = tk.Frame(header, bg=COLORS["bg_dark"])
        center_frame.pack(side="left", fill="both", expand=True)
        self.label_month = tk.Label(
            center_frame, text="", font=self.font_header,
            bg=COLORS["bg_dark"], fg=COLORS["primary"]
        )
        self.label_month.pack(expand=True)

    def _build_calendar_grid(self):
        """Griglia del calendario."""
        # Frame centrato per il calendario
        calendar_container = tk.Frame(self.root, bg=COLORS["bg"])
        calendar_container.pack(fill="x", pady=(5, 0))
        
        self.calendar_frame = tk.Frame(calendar_container, bg=COLORS["bg"])
        self.calendar_frame.pack(anchor="center")

        # Giorni della settimana
        for i, day_name in enumerate(GIORNI_IT):
            fg = COLORS["weekend_fg"] if i >= 5 else COLORS["fg_dim"]
            lbl = tk.Label(
                self.calendar_frame, text=day_name, font=self.font_day_name,
                bg=COLORS["bg"], fg=fg, width=4
            )
            lbl.grid(row=0, column=i, padx=5, pady=(0, 5))

        # Griglia giorni (6 righe max)
        self.day_labels = []
        for row in range(1, 7):
            row_labels = []
            for col in range(7):
                frame = tk.Frame(self.calendar_frame, bg=COLORS["bg"])
                frame.grid(row=row, column=col, padx=5, pady=2)

                # Frame con altezza fissa
                frame.configure(height=35)
                frame.grid_propagate(False)

                # Numero del giorno
                lbl = tk.Label(
                    frame, text="", font=self.font_day,
                    bg=COLORS["bg"], fg=COLORS["fg"],
                    width=4
                )
                lbl.pack()

                # Pallino evento (sempre presente, trasparente di default)
                dot = tk.Label(
                    frame, text="●", font=("JetBrainsMono Nerd Font", 6),
                    bg=COLORS["bg"], fg=COLORS["bg"]  # Trasparente
                )
                dot.pack()

                row_labels.append({"frame": frame, "label": lbl, "dot": dot})
            self.day_labels.append(row_labels)

    def _build_event_list(self):
        """Lista eventi sotto il calendario."""
        # Separatore
        sep = tk.Frame(self.root, bg=COLORS["border"], height=1)
        sep.pack(fill="x", padx=10, pady=(8, 5))

        # Titolo
        self.events_title = tk.Label(
            self.root, text="Eventi del mese", font=self.font_day_name,
            bg=COLORS["bg"], fg=COLORS["fg_dim"], anchor="w"
        )
        self.events_title.pack(fill="x", padx=15)

        # Container scrollabile per gli eventi
        events_container = tk.Frame(self.root, bg=COLORS["bg"])
        events_container.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # Canvas + scrollbar
        self.events_canvas = tk.Canvas(events_container, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(events_container, orient="vertical", command=self.events_canvas.yview)
        self.events_inner = tk.Frame(self.events_canvas, bg=COLORS["bg"])

        self.events_inner.bind("<Configure>", 
            lambda e: self.events_canvas.configure(scrollregion=self.events_canvas.bbox("all")))
        
        self.canvas_window = self.events_canvas.create_window((0, 0), window=self.events_inner, anchor="nw")
        self.events_canvas.configure(yscrollcommand=scrollbar.set)

        self.events_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind per ridimensionamento
        self.events_canvas.bind("<Configure>", self._on_canvas_configure)

        # Scroll con rotella mouse
        self.events_canvas.bind_all("<MouseWheel>", 
            lambda e: self.events_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # Label "nessun evento"
        self.no_events_label = tk.Label(
            self.events_inner, text="Nessun evento questo mese",
            font=self.font_empty, bg=COLORS["bg"], fg=COLORS["fg_dim"]
        )

        self._update_calendar()

    def _on_canvas_configure(self, event):
        """Adatta la larghezza del frame interno al canvas."""
        self.events_canvas.itemconfig(self.canvas_window, width=event.width)

    def _change_month(self, delta):
        """Cambia mese (+1 o -1)."""
        self.current_month += delta
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        elif self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        
        self.month_events = get_events_for_month(
            self.all_events, self.current_year, self.current_month
        )
        self._update_calendar()

    def _change_year(self, delta):
        """Cambia anno (+1 o -1)."""
        self.current_year += delta
        self.month_events = get_events_for_month(
            self.all_events, self.current_year, self.current_month
        )
        self._update_calendar()

    def _update_calendar(self):
        """Aggiorna tutta la vista del calendario."""
        # Aggiorna header
        self.label_month.configure(
            text=f"{MESI_IT[self.current_month - 1]} {self.current_year}"
        )

        # Calcola giorni del mese
        cal = calendar.Calendar(firstweekday=0)  # Lunedì primo
        month_days = cal.monthdayscalendar(self.current_year, self.current_month)

        # Aggiorna griglia giorni
        for row_idx, week in enumerate(month_days):
            for col_idx, day in enumerate(week):
                cell = self.day_labels[row_idx][col_idx]
                lbl = cell["label"]
                dot = cell["dot"]
                frame = cell["frame"]

                if day == 0:
                    # Giorno vuoto (mese precedente/successivo)
                    lbl.configure(text="", bg=COLORS["bg"], fg=COLORS["fg"])
                    dot.configure(fg=COLORS["bg"])  # Trasparente
                    continue

                # Colori base
                bg = COLORS["bg"]
                fg = COLORS["fg"]
                is_weekend = col_idx >= 5
                is_today = (self.current_year == self.today.year and 
                           self.current_month == self.today.month and 
                           day == self.today.day)
                d = date(self.current_year, self.current_month, day)
                has_events = d in self.month_events and len(self.month_events[d]) > 0

                # Applica stili
                if is_today:
                    bg = COLORS["today_bg"]
                    fg = COLORS["today_fg"]
                elif is_weekend:
                    fg = COLORS["weekend_fg"]

                lbl.configure(text=str(day), bg=bg, fg=fg)

                # Mostra/nascondi pallino evento
                if has_events and not is_today:
                    dot.configure(fg=COLORS["event_dot"])  # Verde = visibile
                elif has_events and is_today:
                    dot.configure(fg=COLORS["today_fg"])  # Oggi con evento
                else:
                    dot.configure(fg=COLORS["bg"])  # Trasparente

        # Aggiorna lista eventi
        self._update_event_list()

    def _update_event_list(self):
        """Aggiorna la lista degli eventi del mese."""
        # Pulisci eventi precedenti
        for widget in self.events_inner.winfo_children():
            widget.destroy()

        # Raccogli tutti gli eventi del mese
        all_month_events = []
        for d in sorted(self.month_events.keys()):
            for event in self.month_events[d]:
                all_month_events.append((d, event))

        if not all_month_events:
            self.no_events_label = tk.Label(
                self.events_inner, text="Nessun evento questo mese",
                font=self.font_empty, bg=COLORS["bg"], fg=COLORS["fg_dim"]
            )
            self.no_events_label.pack(pady=10)
            return

        # Raggruppa per giorno
        current_day = None
        for d, event in all_month_events:
            if d != current_day:
                current_day = d
                # Header giorno
                day_name = GIORNI_IT[d.weekday()]
                day_text = f"{day_name} {d.day}"
                day_header = tk.Label(
                    self.events_inner, text=day_text, font=self.font_day_name,
                    bg=COLORS["bg"], fg=COLORS["primary"], anchor="w"
                )
                day_header.pack(fill="x", pady=(8, 2))

            # Evento
            event_frame = tk.Frame(self.events_inner, bg=COLORS["bg"])
            event_frame.pack(fill="x", padx=5, pady=1)

            # Ora
            time_str = event.get("time", "")
            if time_str:
                time_lbl = tk.Label(
                    event_frame, text=f"  {time_str}", font=self.font_event_time,
                    bg=COLORS["bg"], fg=COLORS["event_time"], width=7, anchor="w"
                )
                time_lbl.pack(side="left", padx=(0, 10))

            # Titolo
            title = event.get("title", "Senza titolo")
            title_lbl = tk.Label(
                event_frame, text=title, font=self.font_event_title,
                bg=COLORS["bg"], fg=COLORS["event_title"], anchor="w"
            )
            title_lbl.pack(side="left", fill="x", expand=True)

    def run(self):
        """Avvia il popup."""
        self.root.mainloop()


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Calendar Popup for Polybar")
    parser.add_argument("--posx", type=int, default=100, help="Posizione X del popup")
    parser.add_argument("--posy", type=int, default=100, help="Posizione Y del popup")
    parser.add_argument("--width", type=int, default=420, help="Larghezza del popup")
    parser.add_argument("--height", type=int, default=480, help="Altezza del popup")
    args = parser.parse_args()

    popup = CalendarPopup(args.posx, args.posy, args.width, args.height)
    popup.run()


if __name__ == "__main__":
    main()
