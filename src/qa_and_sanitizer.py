import re
from bs4 import BeautifulSoup


def strip_html(html: str) -> str:
    text = BeautifulSoup(html or "", "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def sanitize_review_mode(html: str) -> str:
    """REVIEW 모드에서는 HTML 주석 중첩 없이 쿠팡·트립닷컴 제휴 문구와 링크를 완전 삭제"""
    cleaned = html or ""
    cleaned = re.sub(r"<!--[\s\S]*?-->", "", cleaned)
    cleaned = cleaned.replace("-->", "")
    cleaned = re.sub(
        r"<[^>]+>[^<]*(?:쿠팡\s*파트너스|트립닷컴|10882341)[^<]*</[^>]+>",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r'<a[^>]*href="[^"]*(?:coupang\.com|link\.coupang\.com|trip\.com|10882341)[^"]*"[^>]*>[\s\S]*?</a>',
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned.strip()


def run_triple_qa(title: str, html: str, mode: str, min_chars: int = 1300) -> dict:
    """1차 제휴/주석 정제 -> 2차 본문 길이 검사 -> 3차 제목-본문 키워드 정합성 검사"""
    final_html = sanitize_review_mode(html) if mode == "REVIEW" else (html or "").strip()
    plain = strip_html(final_html)

    has_forbidden = bool(
        re.search(r"(쿠팡\s*파트너스|coupang\.com|trip\.com|10882341|-->)", final_html, re.IGNORECASE)
    )
    if mode == "REVIEW" and has_forbidden:
        return {"ok": False, "reason": "REVIEW_FORBIDDEN_TOKEN", "html": final_html, "draft": True}

    if len(plain) < min_chars:
        return {"ok": False, "reason": f"THIN_CONTENT_{len(plain)}", "html": final_html, "draft": True}

    keywords = [w for w in re.findall(r"[가-힣A-Za-z0-9]{2,}", title or "") if w not in {"가이드", "방법", "정리", "총정리"}]
    matched = sum(1 for kw in keywords[:5] if kw.lower() in plain.lower())
    if keywords and matched == 0:
        return {"ok": False, "reason": "TITLE_BODY_MISMATCH", "html": final_html, "draft": True}

    return {"ok": True, "reason": "PASSED", "html": final_html, "draft": False}
