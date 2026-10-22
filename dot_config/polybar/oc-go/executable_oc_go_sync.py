#!/usr/bin/env python3
"""Sync spesa OpenCode Go -> cache JSON per polybar.

Sorgente primaria: endpoint ufficiale https://opencode.ai/zen/go/v1/usage
(quello della console web). Auth Bearer, chiave risolta come il plugin
di riferimento: env OPENCODE_GO_API_KEY -> tabella `credential`
(integration_id='opencode-go', active=1) -> auth.json. Ritorna percentuali
+ resetsAt ISO per rolling/weekly/monthly: niente tetti hardcodati,
countdown vero.

Fallback: calcolo locale da session_v2 (cost>0, provider opencode-go).
Refresh on-demand all'apertura del popup (vedi oc-popup.sh).

Soglie widget: verde <70% · arancio <90% · rosso sopra.
"""
import json
import os
import sqlite3
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

CACHE = os.path.expanduser("~/.cache/polybar/oc-go/status.json")
DB = os.path.expanduser("~/.local/share/opencode/opencode.db")
AUTH = os.path.expanduser("~/.local/share/opencode/auth.json")
USAGE_URL = "https://opencode.ai/zen/go/v1/usage"
TIMEOUT = 10

MONTH_CAP = 60.0  # piano Go $10: $12/5h · $30/sett · $60/mese (solo fallback)
GO_PROVIDER = "opencode-go"


class UsageError(Exception):
    pass


def resolve_key():
    env = os.environ.get("OPENCODE_GO_API_KEY", "").strip()
    if env:
        return env
    if os.path.exists(DB):
        try:
            con = sqlite3.connect(f"file:{DB}?immutable=1", uri=True, timeout=5)
            row = con.execute(
                "SELECT value FROM credential "
                "WHERE integration_id=? AND active=1 LIMIT 1",
                (GO_PROVIDER,)).fetchone()
            con.close()
            if row and row[0]:
                val = json.loads(row[0])
                for f in ("key", "apiKey", "access", "token"):
                    if isinstance(val, dict) and val.get(f):
                        return val[f]
        except Exception:
            pass
    try:
        with open(AUTH) as f:
            store = json.load(f)
        entry = store.get(GO_PROVIDER, {})
        if isinstance(entry, dict):
            for f in ("key", "apiKey", "access", "token"):
                if entry.get(f):
                    return entry[f]
    except Exception:
        pass
    return None


def fetch_server(key):
    req = urllib.request.Request(
        USAGE_URL, headers={
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
            # il WAF rifiuta gli UA non-browser (403): come la console web
            "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/143.0.0.0 Safari/537.36")})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            payload = json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise UsageError("credential rejected — riconnetti OpenCode Go")
        if e.code == 429:
            raise UsageError("rate limited, riprova tra poco")
        raise UsageError(f"HTTP {e.code}")
    except Exception:
        raise UsageError("network error")
    try:
        usage = payload["usage"]
        out = {}
        for name in ("rolling", "weekly", "monthly"):
            w = usage[name]
            out[name] = {"percent": float(w.get("percent", 0)),
                         "resetsAt": w.get("resetsAt")}
        return out
    except Exception:
        raise UsageError("unexpected response")


def local_month_start_ms():
    ms = datetime.now(timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0)
    return int(ms.timestamp() * 1000)


def local_windows():
    now_ms = int(time.time() * 1000)
    bounds = {"h5": now_ms - 5 * 3600 * 1000,
              "week": now_ms - 7 * 24 * 3600 * 1000,
              "month": local_month_start_ms()}
    frac = {"h5": 0.2, "week": 0.5, "month": 1.0}
    con = sqlite3.connect(f"file:{DB}?immutable=1", uri=True, timeout=5)
    out = {}
    for name, since in bounds.items():
        s = con.execute(
            "SELECT COALESCE(SUM(cost),0) FROM session_v2 "
            "WHERE cost > 0 AND time_created >= ? "
            "AND json_extract(model,'$.providerID')=?",
            (since, GO_PROVIDER)).fetchone()[0] or 0.0
        cap = round(MONTH_CAP * frac[name], 2)
        out[name] = {"spent": round(s, 4), "cap": cap,
                     "pct": round(100 * s / cap, 1) if cap else 0.0,
                     "resetsAt": None}
    con.close()
    return out


def local_top():
    con = sqlite3.connect(f"file:{DB}?immutable=1", uri=True, timeout=5)
    rows = con.execute(
        "SELECT COALESCE(json_extract(model,'$.id'),'?'), "
        "COALESCE(SUM(cost),0) FROM session_v2 "
        "WHERE cost > 0 AND time_created >= ? "
        "AND json_extract(model,'$.providerID')=? "
        "GROUP BY 1 ORDER BY 2 DESC LIMIT 5",
        (local_month_start_ms(), GO_PROVIDER)).fetchall()
    con.close()
    return [{"model": (r[0] or "?"), "cost": round(r[1], 4)} for r in rows]


def main():
    data = {"updated": int(time.time()), "top": local_top(),
            "error": None}
    key = resolve_key()
    if not key:
        data.update({"source": "local", "windows": local_windows(),
                     "error": "no credential found"})
    else:
        try:
            srv = fetch_server(key)
            data.update({"source": "server", "windows": {
                "h5": {"pct": srv["rolling"]["percent"],
                       "resetsAt": srv["rolling"]["resetsAt"]},
                "week": {"pct": srv["weekly"]["percent"],
                         "resetsAt": srv["weekly"]["resetsAt"]},
                "month": {"pct": srv["monthly"]["percent"],
                          "resetsAt": srv["monthly"]["resetsAt"]}}})
        except UsageError as e:
            data.update({"source": "local", "windows": local_windows(),
                         "error": str(e)})

    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE + ".tmp", "w") as f:
        json.dump(data, f)
    os.replace(CACHE + ".tmp", CACHE)
    w = data["windows"]["month"]
    print(f"source={data['source']} month={w.get('pct')}% err={data['error']}")


if __name__ == "__main__":
    main()
