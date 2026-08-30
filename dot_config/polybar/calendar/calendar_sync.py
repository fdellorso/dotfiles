#!/usr/bin/env python3
"""
Sincronizzazione calendario Nextcloud per Polybar.
Scarica gli eventi dal server e li salva in cache JSON.
"""

import requests
import json
import re
import urllib3
from pathlib import Path
from datetime import datetime, date, time
from xml.etree import ElementTree as ET
from calendar_config import NEXTCLOUD_URL, NEXTCLOUD_USER, NEXTCLOUD_PASS, CACHE_DIR, CACHE_FILE

# Disabilita warning per certificati self-signed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_event_list():
    """Ottieni la lista degli eventi ICS dal server CalDAV."""
    headers = {
        "Depth": "1",
        "Content-Type": "application/xml"
    }
    
    resp = requests.request(
        method="PROPFIND",
        url=NEXTCLOUD_URL,
        auth=(NEXTCLOUD_USER, NEXTCLOUD_PASS),
        headers=headers,
        verify=False  # Nextcloud locale con certificato self-signed
    )
    
    if resp.status_code != 207:
        print(f"Errore PROPFIND: {resp.status_code}")
        return []
    
    # Parsifica XML per trovare i link agli ICS
    root = ET.fromstring(resp.text)
    ns = {"d": "DAV:"}
    
    events = []
    for response in root.findall(".//d:response", ns):
        href = response.find("d:href", ns)
        if href is not None and href.text.endswith(".ics"):
            events.append(href.text)
    
    return events


def download_event(event_url):
    """Scarica un singolo evento ICS."""
    url = f"https://nextcloud.fritz.box{event_url}"
    
    resp = requests.get(
        url,
        auth=(NEXTCLOUD_USER, NEXTCLOUD_PASS),
        verify=False
    )
    
    if resp.status_code == 200:
        return resp.text
    return None


def parse_ics(ics_content):
    """Parsifica il contenuto ICS ed estrai le informazioni dell'evento."""
    event = {}
    
    # Estrai SUMMARY
    summary_match = re.search(r"SUMMARY:(.+)", ics_content)
    if summary_match:
        event["title"] = summary_match.group(1).strip()
    
    # Estrai DTSTART
    dtstart_match = re.search(r"DTSTART[^:]*:(\d{8}T?\d{0,6})", ics_content)
    if dtstart_match:
        dtstart = dtstart_match.group(1)
        try:
            if "T" in dtstart:
                dt = datetime.strptime(dtstart, "%Y%m%dT%H%M%S")
                event["date"] = dt.strftime("%Y-%m-%d")
                event["time"] = dt.strftime("%H:%M")
            else:
                dt = datetime.strptime(dtstart, "%Y%m%d")
                event["date"] = dt.strftime("%Y-%m-%d")
                event["time"] = ""  # Evento tutto il giorno
        except ValueError:
            pass
    
    # Estrai DTEND
    dtend_match = re.search(r"DTEND[^:]*:(\d{8}T?\d{0,6})", ics_content)
    if dtend_match:
        dtend = dtend_match.group(1)
        try:
            if "T" in dtend:
                dt = datetime.strptime(dtend, "%Y%m%dT%H%M%S")
                event["end_time"] = dt.strftime("%H:%M")
        except ValueError:
            pass
    
    # Estrai LOCATION
    location_match = re.search(r"LOCATION:(.+)", ics_content)
    if location_match:
        event["location"] = location_match.group(1).strip()
    
    return event


def group_events_by_date(events):
    """Raggruppa gli eventi per data."""
    events_by_date = {}
    
    for event in events:
        if "date" not in event:
            continue
        
        date_str = event["date"]
        if date_str not in events_by_date:
            events_by_date[date_str] = []
        
        events_by_date[date_str].append({
            "time": event.get("time", ""),
            "title": event.get("title", "Senza titolo"),
            "location": event.get("location", ""),
            "end_time": event.get("end_time", "")
        })
    
    # Ordina gli eventi per ora all'interno di ogni giorno
    for date_str in events_by_date:
        events_by_date[date_str].sort(key=lambda e: e.get("time", "00:00"))
    
    return events_by_date


def save_cache(events_by_date):
    """Salva gli eventi nella cache JSON."""
    cache_dir = Path(CACHE_DIR).expanduser()
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    cache_path = cache_dir / CACHE_FILE
    with open(cache_path, "w") as f:
        json.dump(events_by_date, f, indent=2, ensure_ascii=False)
    
    print(f"Cache aggiornata: {cache_path}")
    print(f"Eventi trovati: {sum(len(v) for v in events_by_date.values())}")


def main():
    print("Sync calendario Nextcloud...")
    
    # Ottieni lista eventi
    event_urls = get_event_list()
    print(f"Trovati {len(event_urls)} eventi sul server")
    
    # Scarica e parsifica ogni evento
    events = []
    for url in event_urls:
        ics = download_event(url)
        if ics:
            event = parse_ics(ics)
            if event:
                events.append(event)
    
    print(f"Parsificati {len(events)} eventi")
    
    # Raggruppa per data e salva
    events_by_date = group_events_by_date(events)
    save_cache(events_by_date)


if __name__ == "__main__":
    main()
