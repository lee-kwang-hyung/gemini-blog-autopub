"""Offline internal pre-application gate. Never submits a review."""
import json
import re
import sys
from urllib.parse import urlsplit

def assess(data):
    checks = ("robots_txt_custom_off", "robots_headers_custom_off", "ads_txt_exact", "layout_clean", "quarantine_verified", "priority_urls_resolved")
    missing = [k for k in checks if data.get(k) is not True]
    seen = set()
    for row in data.get("posts", []):
        u = urlsplit(row.get("canonical",""))
        if (u.scheme,u.netloc) != ("https","genesislkh21.blogspot.com") or u.query or u.fragment or not re.fullmatch(r"/\d{4}/\d{2}/[^/]+\.html", u.path): continue
        if row.get("status") != "LIVE" or not isinstance(row.get("chars"),int) or row["chars"] < 1300: continue
        if not all(row.get(k) is True for k in ("travel_match","page_clean","indexed","snippet_clean")): continue
        if not all(row.get(k) for k in ("inspection_evidence","snippet_evidence","checked_at")): continue
        if row.get("google_canonical") != row["canonical"]: continue
        seen.add(u.path)
    return len(seen), missing

if __name__ == "__main__":
    count, missing = assess(json.load(open(sys.argv[1],encoding="utf-8")))
    ok = count >= 15 and not missing
    print("READY" if ok else "HOLD", "verified =",count,"missing =",missing)
    sys.exit(0 if ok else 1)
