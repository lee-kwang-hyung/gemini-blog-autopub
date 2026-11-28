import re
from html import unescape
from bs4 import BeautifulSoup, Comment


def strip_html(html: str) -> str:
    text = BeautifulSoup(html or "", "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def sanitize_review_mode(html: str) -> str:
    """REVIEW 모드에서는 HTML 주석 중첩 없이 쿠팡·트립닷컴 제휴 문구와 링크를 완전 삭제"""
    soup = BeautifulSoup(html or "", "html.parser")
    for comment in soup.find_all(string=lambda x: isinstance(x, Comment)):
        comment.extract()
    for tag in soup.find_all(["script", "style", "template", "iframe", "noscript"]):
        tag.decompose()
    for tag in list(soup.find_all(True)):
        if tag.parent is None:
            continue
        if FORBIDDEN.search(unescape(str(tag.attrs))):
            tag.decompose()
    for node in list(soup.find_all(string=True)):
        if node.parent is None:
            continue
        if FORBIDDEN.search(str(node)):
            parent = node.parent
            if parent.name in {"p", "a", "small", "figcaption", "button"}:
                parent.decompose()
            else:
                node.extract()
        else:
            node.replace_with(str(node).replace("<!--", "").replace("-->", ""))
    return str(soup).strip()


FORBIDDEN = re.compile(r"쿠팡|파트너스|트립\s*닷컴|coupang|coupa\.ng|trip\s*\.\s*com|트립닷컴|10882341|affiliate-product-card|일정액의\s*수수료|제휴\s*수수료|대가성\s*고지", re.I)
TRAVEL = re.compile(r"여행|항공|공항|출국|입국|수하물|기내|여권|숙박|숙소|호텔|탑승|비행|경유|관광|렌터카|면세|비자")


def run_triple_qa(title: str, html: str, mode: str, min_chars: int = 1300, travel_only: bool = False) -> dict:
    """1차 제휴/주석 정제 -> 2차 본문 길이 검사 -> 3차 제목-본문 키워드 정합성 검사"""
    final_html = sanitize_review_mode(html) if mode == "REVIEW" else (html or "").strip()
    plain = strip_html(final_html)

    decoded = unescape(final_html)
    has_forbidden = FORBIDDEN.search(decoded) or FORBIDDEN.search(plain) or "<!--" in decoded or "-->" in decoded
    if mode == "REVIEW" and has_forbidden:
        return {"ok": False, "reason": "REVIEW_FORBIDDEN_TOKEN", "html": final_html, "draft": True}

    if len(plain) < min_chars:
        return {"ok": False, "reason": f"THIN_CONTENT_{len(plain)}", "html": final_html, "draft": True}

    if travel_only and (not TRAVEL.search(title or "") or not TRAVEL.search(plain)):
        return {"ok": False, "reason": "TRAVEL_TOPIC_REVIEW", "html": final_html, "draft": True}

    keywords = [
        w
        for w in re.findall(r"[가-힣A-Za-z0-9]{2,}", title or "")
        if w not in {"가이드", "방법", "정리", "총정리"}
    ]
    matched = sum(1 for kw in keywords[:5] if kw.lower() in plain.lower())
    if not keywords or matched < min(2, len(set(keywords[:5]))):
        return {"ok": False, "reason": "TITLE_BODY_MISMATCH", "html": final_html, "draft": True}

    return {"ok": True, "reason": "PASSED", "html": final_html, "draft": False}
