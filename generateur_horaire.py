# -*- coding: utf-8 -*-
"""
Générateur d'horaires XML (7 prochains jours) pour plusieurs locaux.
- API POST: https://simple-planning.henallux.be/api/getHoraireSalle
- Params: action=getHoraireSalle, codeSalle=<NomSalle>
- Options: --mock, --mock-dir, --include-empty-days, --no-filter-location, --verbose
- Sortie: chaque <tNBEvent> est sur UNE SEULE LIGNE.
Compatible Python 3.8+.
"""
import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

# ---- Fuseau Europe/Brussels (si disponible)
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
    TZ = ZoneInfo("Europe/Brussels")
except Exception:
    TZ = None

# ---- HTTP (POST): requests si présent, sinon urllib
def http_post_text(url: str, data: Dict[str, str], timeout: int = 30) -> str:
    try:
        import requests  # type: ignore
        resp = requests.post(url, data=data, timeout=timeout, headers={"User-Agent": "HoraireFetcher/1.0"})
        resp.raise_for_status()
        return resp.text
    except Exception:
        import urllib.parse
        import urllib.request
        encoded = urllib.parse.urlencode(data).encode("utf-8")
        req = urllib.request.Request(url, data=encoded, headers={"User-Agent": "HoraireFetcher/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")

# ---- Utils
def load_salles_ini(path: str) -> List[str]:
    salles: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if "=" in s:
                _, val = s.split("=", 1)
                val = val.strip()
                if val:
                    salles.append(val)
    return salles

def clean_text(x: Optional[str]) -> str:
    if x is None:
        return ""
    x = x.replace("\u00a0", " ")
    x = re.sub(r"[\r\n]+", " ", x)
    x = re.sub(r"\s{2,}", " ", x)
    return x.strip()

def parse_dt_ical(dt_str: Optional[str]) -> Optional[datetime]:
    """Transforme 'YYYYMMDDTHHMMSSZ?' en datetime; convertit vers Europe/Brussels si 'Z'."""
    if not dt_str:
        return None
    s = dt_str.strip()
    zulu = s.endswith("Z")
    if zulu:
        s = s[:-1]
    if "T" not in s or len(s) < 13:
        return None
    date_part, time_part = s.split("T", 1)
    try:
        year = int(date_part[0:4]); month = int(date_part[4:6]); day = int(date_part[6:8])
        hour = int(time_part[0:2]); minute = int(time_part[2:4])
        dt = datetime(year, month, day, hour, minute)
        if zulu:
            dt = dt.replace(tzinfo=timezone.utc)
            if TZ is not None:
                dt = dt.astimezone(TZ)
        else:
            if TZ is not None:
                dt = dt.replace(tzinfo=TZ)
        return dt
    except Exception:
        return None

def normalize_feed(struct: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Accepte struct['horaire']['ICAL'] (string JSON) ou struct['feed'] direct."""
    if isinstance(struct, dict):
        horaire = struct.get("horaire")
        if isinstance(horaire, dict) and "ICAL" in horaire:
            ical_str = horaire.get("ICAL", "")
            try:
                ical = json.loads(ical_str)
                feed = ical.get("feed", [])
                return feed if isinstance(feed, list) else []
            except Exception:
                return []
        feed = struct.get("feed")
        if isinstance(feed, list):
            return feed
    return []

def events_from_feed(feed: List[Dict[str, Any]], salle_filter: Optional[str],
                     start_date, end_date, shift_hours: int) -> List[Dict[str, str]]:
    evts: List[Dict[str, str]] = []
    for it in feed:
        loc = clean_text(it.get("location"))
        if salle_filter and loc != salle_filter:
            continue
        dt1 = parse_dt_ical(it.get("dtstart"))
        dt2 = parse_dt_ical(it.get("dtend"))
        if not dt1 or not dt2:
            continue
        # appliquer le décalage horaire demandé
        if shift_hours:
            from datetime import timedelta
            dt1 = dt1 + timedelta(hours=shift_hours)
            dt2 = dt2 + timedelta(hours=shift_hours)
        if start_date and dt1.date() < start_date:
            continue
        if end_date and dt1.date() > end_date:
            continue
        summary = clean_text(it.get("summary;language=fr") or it.get("summary"))
        evts.append({
            "LOCATION": loc,
            "TimeSTART": dt1.strftime("%H%M"),
            "TimeEND": dt2.strftime("%H%M"),
            "SUMMARY": summary,
            "DATEKEY": dt1.strftime("%Y%m%d")
        })
    return evts

# ---- Fusion des créneaux contigus (même LOCATION & SUMMARY)
def _hhmm_to_minutes(hhmm: str) -> int:
    try:
        return int(hhmm[:2]) * 60 + int(hhmm[2:4])
    except Exception:
        return 0

def _minutes_to_hhmm(m: int) -> str:
    h = (m // 60) % 24
    mn = m % 60
    return f"{h:02d}{mn:02d}"

def merge_contiguous_events(day_events: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Regroupe les créneaux contigus si TimeEND == TimeSTART suivant et (LOCATION,SUMMARY) identiques."""
    if not day_events:
        return []
    day_events = sorted(day_events, key=lambda e: (e.get("LOCATION",""), e.get("SUMMARY",""), e.get("TimeSTART",""), e.get("TimeEND","")))
    merged: List[Dict[str, str]] = []
    cur: Optional[Dict[str, str]] = None
    for e in day_events:
        if cur is None:
            cur = dict(e)
            continue
        same_loc = e.get("LOCATION","") == cur.get("LOCATION","")
        same_sum = e.get("SUMMARY","") == cur.get("SUMMARY","")
        if same_loc and same_sum:
            end_cur = _hhmm_to_minutes(cur.get("TimeEND","0000"))
            start_e = _hhmm_to_minutes(e.get("TimeSTART","0000"))
            if start_e == end_cur:
                end_e = _hhmm_to_minutes(e.get("TimeEND","0000"))
                if end_e > end_cur:
                    cur["TimeEND"] = _minutes_to_hhmm(end_e)
                continue
        merged.append(cur)
        cur = dict(e)
    if cur is not None:
        merged.append(cur)
    return merged

def ensure_full_week(events_by_date: Dict[str, list], start_date) -> None:
    for i in range(7):
        dkey = (start_date + timedelta(days=i)).strftime("%Y%m%d")
        events_by_date.setdefault(dkey, [])

def build_xml(events_by_date: Dict[str, list]) -> str:
    """Sérialise le XML, <tNBEvent> sur une seule ligne, sauts de ligne entre nœuds."""
    from xml.etree import ElementTree as ET
    root = ET.Element("dataentry")
    for idx, (date_key, evts) in enumerate(sorted(events_by_date.items())):
        day = ET.SubElement(root, 'MAIN.DayOfWeek', attrib={"index": str(idx)})
        ddate = ET.SubElement(day, "dDate"); ddate.text = date_key
        for i, e in enumerate(evts):
            t = ET.SubElement(day, "tNBEvent", attrib={"index": str(i)})
            ET.SubElement(t, "LOCATION").text  = e.get("LOCATION", "")
            ET.SubElement(t, "TimeSTART").text = e.get("TimeSTART", "")
            ET.SubElement(t, "TimeEND").text   = e.get("TimeEND", "")
            ET.SubElement(t, "SUMMARY").text   = e.get("SUMMARY", "")
    # Construction manuelle
    lines = ["<dataentry>"]
    for day in root:
        lines.append(f'<MAIN.DayOfWeek index="{day.attrib.get("index","0")}">')
        # dDate
        for c in day:
            if c.tag == "dDate":
                lines.append(f'<dDate>{c.text or ""}</dDate>')
                break
        # événements (une seule ligne chacun)
        for child in day:
            if child.tag != "tNBEvent":
                continue
            parts = []
            for sub in child:
                text = "" if sub.text is None else sub.text
                parts.append(f'<{sub.tag}>{text}</{sub.tag}>')
            inner = "".join(parts)
            idx_attr = child.attrib.get("index", "0")
            lines.append(f'<tNBEvent index="{idx_attr}">{inner}</tNBEvent>')
        lines.append("</MAIN.DayOfWeek>")
    lines.append("</dataentry>")
    return "\n".join(lines) + "\n"

def fetch_for_salle(api_url: Optional[str], salle: str,
                    mock_path: Optional[str], mock_dir: Optional[str],
                    verbose: bool=False) -> Dict[str, Any]:
    """Retourne le JSON pour une salle (mock-dir > mock > POST API)."""
    # mock-dir prioritaire
    if mock_dir:
        from pathlib import Path
        cand_json = Path(mock_dir) / (salle + ".json")
        cand_txt  = Path(mock_dir) / (salle + ".txt")
        for cand in (cand_json, cand_txt):
            if cand.exists():
                if verbose:
                    print("[mock-dir] %s <- %s" % (salle, str(cand)))
                with cand.open("r", encoding="utf-8") as f:
                    return json.load(f)
        if verbose:
            print("[mock-dir] aucun fichier dédié pour %s" % salle)
    # mock unique
    if mock_path:
        if verbose:
            print("[mock] %s <- %s" % (salle, mock_path))
        with open(mock_path, "r", encoding="utf-8") as f:
            return json.load(f)
    # API POST
    if not api_url:
        raise RuntimeError("Aucune API fournie. Utilisez --api ou --mock/--mock-dir.")
    if verbose:
        print("[api] POST %s salle=%s" % (api_url, salle))
    payload = {"action": "getHoraireSalle", "codeSalle": salle}
    text = http_post_text(api_url, payload)
    return json.loads(text)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--salles", required=True, help="fichier .ini avec salleXX=Nom")
    ap.add_argument("--out", required=True, help="fichier XML de sortie")
    ap.add_argument("--api", required=False, help="URL POST (ex: https://simple-planning.henallux.be/api/getHoraireSalle)")
    ap.add_argument("--mock", required=False, help="chemin du mock unique (JSON)")
    ap.add_argument("--mock-dir", required=False, help="dossier avec un mock par salle (<salle>.json|.txt)")
    ap.add_argument("--include-empty-days", action="store_true", help="affiche les 7 jours même sans événements")
    ap.add_argument("--no-filter-location", action="store_true", help="(test) ne pas filtrer par nom de salle")
    ap.add_argument("--verbose", action="store_true", help="affiche la progression")
    ap.add_argument("--shift-hours", type=int, default=-2, help="décalage (en heures) appliqué aux TimeSTART/TimeEND et à la date (ex: -2)")
    args = ap.parse_args()

    salles = load_salles_ini(args.salles)
    if not salles:
        print("Aucune salle trouvée dans", args.salles)
        return 1

    # Fenêtre de 7 jours en timezone locale si disponible
    now = datetime.now(TZ) if TZ is not None else datetime.now(timezone.utc)
    today = now.date()
    end = today + timedelta(days=6)

    events_by_date: Dict[str, list] = defaultdict(list)
    if args.include_empty_days:
        ensure_full_week(events_by_date, today)

    total_evt = 0
    for salle in salles:
        data = fetch_for_salle(args.api, salle, args.mock, args.mock_dir, verbose=args.verbose)
        feed = normalize_feed(data)
        evts = events_from_feed(feed, salle_filter=(None if args.no_filter_location else salle),
                                start_date=today, end_date=end, shift_hours=args.shift_hours)
        total_evt += len(evts)
        if args.verbose:
            print("[ok] %s: %d événements" % (salle, len(evts)))
        for e in evts:
            date_key = e.pop("DATEKEY")
            events_by_date[date_key].append(e)

    # Tri et fusion par jour
    for date_key, lst in list(events_by_date.items()):
        lst.sort(key=lambda x: (x.get("LOCATION",""), x.get("SUMMARY",""), x.get("TimeSTART",""), x.get("TimeEND","")))
        events_by_date[date_key] = merge_contiguous_events(lst)

    if args.include_empty_days:
        ensure_full_week(events_by_date, today)

    xml_out = build_xml(events_by_date)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(xml_out)

    if args.verbose:
        print("[total] événements conservés:", total_evt)
        print("OK ->", args.out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
