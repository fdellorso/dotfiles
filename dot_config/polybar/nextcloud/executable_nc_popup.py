#!/usr/bin/env python3
"""Popup stato sync Nextcloud (sola lettura). Stile Dracula come calendar_popup."""
import configparser
import os
import sqlite3
import tkinter as tk
from datetime import datetime
from urllib.parse import urlparse

BG, FG = "#282A36", "#F8F8F2"
ACCENT, RED, GRAY, ORANGE = "#50FA7B", "#FF5555", "#6272A4", "#FFB86C"
FONT = ("JetBrainsMono Nerd Font", 10)

HOME = os.path.expanduser("~")
CFG = os.path.join(HOME, ".config/Nextcloud/nextcloud.cfg")


def cfg_data():
    info = {"user": "?", "host": "?", "folders": []}
    cp = configparser.ConfigParser()
    cp.optionxform = str
    try:
        cp.read(CFG)
    except Exception:
        return info
    for sec in cp.sections():
        for k, v in cp.items(sec):
            if k.endswith("webflow_user") and v:
                info["user"] = v
            if k.endswith("\\url") or k == "url":
                try:
                    info["host"] = urlparse(v).hostname or v
                except Exception:
                    pass
    seen = {}
    for sec in cp.sections():
        for k, v in cp.items(sec):
            if "\\Folders\\" in k:
                idx = k.split("\\Folders\\")[1].split("\\")[0]
                f = seen.setdefault(idx, {})
                leaf = k.split("\\")[-1]
                if leaf in ("localPath", "targetPath", "paused"):
                    f[leaf] = v
    info["folders"] = [seen[i] for i in sorted(seen)]
    return info


def journal():
    out = {"activity": None, "checkpoint": None, "errors": [], "conflicts": 0}
    dbs = [f for f in os.listdir(os.path.join(HOME, "Nextcloud"))
           if f.startswith(".sync_") and f.endswith(".db")] if os.path.isdir(
        os.path.join(HOME, "Nextcloud")) else []
    if not dbs:
        return out
    db = os.path.join(HOME, "Nextcloud", sorted(dbs)[0])
    for suffix in ("-wal", "-shm", ""):
        p = db + suffix
        if os.path.exists(p):
            out["activity"] = datetime.fromtimestamp(os.path.getmtime(p))
            break
    try:
        con = sqlite3.connect(f"file:{db}?immutable=1", uri=True, timeout=2)
        cur = con.cursor()
        try:
            cur.execute("SELECT value FROM key_value_store WHERE key='last_sync'")
            row = cur.fetchone()
            if row:
                out["checkpoint"] = datetime.fromtimestamp(int(row[0]))
        except Exception:
            pass
        try:
            cur.execute("SELECT path, errorstring, retrycount FROM blacklist "
                        "ORDER BY lastTryTime DESC LIMIT 5")
            out["errors"] = cur.fetchall()
        except Exception:
            pass
        try:
            cur.execute("SELECT COUNT(*) FROM conflicts")
            out["conflicts"] = cur.fetchone()[0]
        except Exception:
            pass
        con.close()
    except Exception:
        pass
    return out


def running():
    try:
        with os.popen("pgrep -x nextcloud") as p:
            return bool(p.read().strip())
    except Exception:
        return False


def main():
    info, j = cfg_data(), journal()
    ok = running()
    n_err = len(j["errors"])

    root = tk.Tk()
    root.title("nc-popup")
    root.configure(bg=BG)
    root.overrideredirect(True)  # no titlebar, galleggia come calendar-popup
    root.attributes("-topmost", True)
    W, H = 420, 320
    x = root.winfo_screenwidth() - W - 20
    root.geometry(f"{W}x{H}+{x}+45")

    tk.Label(root, text=" Nextcloud", bg=BG, fg=FG,
             font=("JetBrainsMono Nerd Font", 12, "bold")).pack(pady=(10, 2))
    st = ("● attivo" if ok else "● spento")
    stc = ACCENT if ok else GRAY
    if n_err:
        st, stc = f"● {n_err} errori", RED
    tk.Label(root, text=st, bg=BG, fg=stc, font=FONT).pack()

    body = tk.Frame(root, bg=BG)
    body.pack(fill="both", expand=True, padx=15, pady=5)
    r = 0

    def row(label, value, color=FG):
        nonlocal r
        tk.Label(body, text=label, bg=BG, fg=GRAY, font=FONT,
                 anchor="w").grid(row=r, column=0, sticky="w")
        tk.Label(body, text=value, bg=BG, fg=color, font=FONT,
                 anchor="w").grid(row=r, column=1, sticky="w", padx=8)
        r += 1

    row("Account:", f"{info['user']} @ {info['host']}")
    for f in info["folders"][:3]:
        lp = os.path.basename(f.get("localPath", "?"))
        extra = " (pausa)" if f.get("paused") == "true" else ""
        row("Cartella:", f"{lp} → {f.get('targetPath', '?')}{extra}")
    if j["activity"]:
        row("Attività:", j["activity"].strftime("%d/%m %H:%M"))
    if j["checkpoint"]:
        row("Full sync:", j["checkpoint"].strftime("%d/%m %H:%M"))
    row("Conflitti:", str(j["conflicts"]),
        RED if j["conflicts"] else FG)
    for path, err, retry in j["errors"]:
        row("Errore:", f"{os.path.basename(str(path))} (retry {retry})", RED)

    tk.Button(root, text="Chiudi", bg="#44475A", fg=FG, font=FONT,
              relief="flat", command=root.destroy).pack(pady=8)
    root.bind("<Escape>", lambda e: root.destroy())
    root.mainloop()


if __name__ == "__main__":
    main()
