"""Default: read only. No deletes, no bulk or scheduled execution."""
import argparse
import hashlib
import json
from pathlib import Path
from qa_and_sanitizer import strip_html

BLOG = "2592561701693494703"
BASE = "https://genesislkh21.blogspot.com"
TARGETS = {
    "8069601392100375138": ("/2026/10/smb-8.html", "복합기 스캔이 갑자기 안 될 때｜SMB 스캔 폴더부터 확인할 8가지"),
    "1620431145509967201": ("/2026/11/blog-post_588.html", None),
    "2358790464825852127": ("/2026/10/11-24h2-10-13-pc.html", "윈도우11 24H2 지원 종료 임박｜10월 13일 전 내 PC에서 확인할 것"),
    "6783396808753110773": ("/2026/11/blog-post_15.html", None),
    "3143214705046941338": ("/2026/11/blog-post_23.html", None),
    "7291120338551248217": ("/2026/11/blog-post_25.html", None),
}

def main():
    from main import get_blogger_service
    ap = argparse.ArgumentParser()
    ap.add_argument("id", choices=TARGETS)
    ap.add_argument("--apply-digest", help="read-only run prints digest; supply only after checking target")
    ap.add_argument("--backup-dir", type=Path)
    a = ap.parse_args()
    posts = get_blogger_service().posts()
    def read():
        return posts.get(blogId=BLOG, postId=a.id, view="ADMIN").execute(num_retries=0)
    p = read()
    path,title = TARGETS[a.id]
    if str(p["id"]) != a.id or str(p["blog"]["id"]) != BLOG:
        raise SystemExit("identity mismatch")
    if p.get("status") == "DRAFT":
        print("Already DRAFT"); return
    if p.get("status") != "LIVE" or p.get("url") != BASE+path:
        raise SystemExit("URL/status mismatch")
    if title and p["title"] != title:
        raise SystemExit("title changed: review again")
    size = len(strip_html(p["content"]))
    if not title and size >= 1300:
        raise SystemExit("no longer thin")
    snapshot = json.dumps(p, ensure_ascii=False, sort_keys=True).encode()
    digest = hashlib.sha256(snapshot).hexdigest()
    print(a.id, p["title"], size, digest)
    if not a.apply_digest: return
    if a.apply_digest != digest or not a.backup_dir:
        raise SystemExit("matching digest and private backup directory required")
    a.backup_dir.mkdir(exist_ok=True, parents=True, mode=0o700)
    backup = a.backup_dir / (a.id+"-"+digest+".json")
    with backup.open("xb") as f: f.write(snapshot)
    posts.revert(blogId=BLOG, postId=a.id).execute(num_retries=0)
    if read().get("status") != "DRAFT":
        raise SystemExit("status unconfirmed: read before any further action")
    print("Verified DRAFT", a.id)

if __name__ == "__main__": main()
