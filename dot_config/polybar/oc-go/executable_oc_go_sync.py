#!/usr/bin/env python3
"""Sync spesa OpenCode Go dal DB locale -> cache JSON per polybar.
Finestre rolling allineate ai limiti Go (5h=20%, sett=50%, mese=100%).
Solo sessioni a pagamento (cost>0): i modelli locali non consumano il piano.
Piano via env OC_GO_PLAN: go (default) | go-plus. Tetti Spark: go 60/30/12.
"""
import json
import os
import sqlite3
import time
from datetime import datetime, timezone

CACHE = os.path.expanduser("~/.cache/polybar/oc-go/status.json")
DB = os.path.expanduser("~/.local/share/opencode/opencode.db")
PLAN = os.environ.get("OC_GO_PLAN", "go")

CAPS = {
    # modello (sottostringa id) -> {go: mensile, plus: mensile}
    "spark": {"go": 60.0, "go-plus": 120.0},
}
DEFAULT_CAP = {"go": 60.0, "go-plus": 120.0}


def cap_for(model_id):
    mid = (model_id or "").lower()
    for key, caps in CAPS.items():
        if key in mid:
            return caps[PLAN]
    return DEFAULT_CAP[PLAN]


def main():
    now_ms = int(time.time() * 1000)
    month_start = datetime.now(timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0)
    month_ms = int(month_start.timestamp() * 1000)
    week_ms = now_ms - 7 * 24 * 3600 * 1000
    h5_ms = now_ms - 5 * 3600 * 1000

    con = sqlite3.connect(f"file:{DB}?immutable=1", uri=True, timeout=5)
    cur = con.cursor()

    def spent(since_ms):
        cur.execute(
            "SELECT COALESCE(SUM(cost),0) FROM session "
            "WHERE cost > 0 AND time_created >= ?", (since_ms,))
        return cur.fetchone()[0] or 0.0

    cur.execute(
        "SELECT COALESCE(json_extract(model,'$.id'),'?'), COALESCE(SUM(cost),0) "
        "FROM session WHERE cost > 0 AND time_created >= ? "
        "GROUP BY 1 ORDER BY 2 DESC LIMIT 6", (month_ms,))
    top = [{"model": (r[0] or "?"), "cost": round(r[1], 4)} for r in cur.fetchall()]

    focus = top[0]["model"] if top else "?"
    cap = cap_for(focus)
    windows = {}
    for name, since in (("h5", h5_ms), ("week", week_ms), ("month", month_ms)):
        s = spent(since)
        frac = {"h5": 0.2, "week": 0.5, "month": 1.0}[name]
        c = round(cap * frac, 2)
        windows[name] = {"spent": round(s, 4), "cap": c,
                         "pct": round(100 * s / c, 1) if c else 0.0}

    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    con.close()
    with open(CACHE + ".tmp", "w") as f:
        json.dump({"plan": PLAN, "focus": focus, "windows": windows,
                   "top": top, "updated": int(time.time())}, f)
    os.replace(CACHE + ".tmp", CACHE)
    m = windows["month"]
    print(f"plan={PLAN} focus={focus} month=${m['spent']}/${m['cap']} ({m['pct']}%)")


if __name__ == "__main__":
    main()
