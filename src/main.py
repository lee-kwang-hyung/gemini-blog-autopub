import datetime
import json
import os
import random
import re
import socket
import time
import requests
from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from qa_and_sanitizer import run_triple_qa

socket.setdefaulttimeout(60)

TOPICS = [
    ("인천공항 액체류 반입 규정 및 기내 수하물 통과 기준", "공항규정", "airport security luggage"),
    ("해외여행 보조배터리 기내 반입 용량 계산법 및 주의사항", "여행준비", "power bank airplane travel"),
    ("국제선 수하물 분실 시 공항에서 바로 처리하는 보상 절차", "항공권", "airport baggage claim"),
    ("일본 입국 심사 비짓재팬웹 등록 절차와 필수 준비물", "해외여행", "japan airport travel"),
    ("항공권 이름 철자 오류 발견 시 항공사별 변경 기준 정리", "항공권", "flight ticket passport"),
]

MODEL_CANDIDATES = [
    os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
]
# 중복 제거 (순서 유지)
MODEL_CANDIDATES = list(dict.fromkeys(MODEL_CANDIDATES))
RETRIES_PER_MODEL = 2
RETRY_DELAY_SECONDS = 5
API_TIMEOUT_MS = 60_000


def log(msg: str) -> None:
    print(msg, flush=True)


def fetch_pexels_image(query: str) -> str:
    api_key = os.getenv("PEXELS_API_KEY", "").strip()
    if not api_key:
        return ""
    try:
        res = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": api_key},
            params={"query": query, "per_page": 5, "orientation": "landscape"},
            timeout=15,
        )
        if res.status_code != 200:
            return ""
        photos = res.json().get("photos", [])
        if not photos:
            return ""
        chosen = random.choice(photos)
        return chosen.get("src", {}).get("large", "")
    except Exception as err:
        log(f"[Pexels] 이미지 조회 생략: {err}")
        return ""


def generate_article(topic: str, mode: str, trip_id: str) -> str:
    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"],
        http_options=genai_types.HttpOptions(timeout=API_TIMEOUT_MS),
    )
    affiliate_rule = (
        "절대 쿠팡 파트너스, 트립닷컴, 광고 고지 문구, 외부 제휴 링크, HTML 주석(<!-- -->)을 포함하지 마세요."
        if mode != "APPROVED"
        else f"글 하단에 트립닷컴 제휴 안내(Alliance ID: {trip_id})를 자연스럽게 1줄 포함할 수 있습니다."
    )
    prompt = f"""
당신은 '떠나볼 가이드'의 실용 여행 정보 에디터입니다.
주제: {topic}

작성 규칙:
1. 순수 텍스트 기준 공백 포함 1,600자 이상으로 구체적인 수치, 예외 규정, 체크리스트를 포함해 작성하세요.
2. HTML 본문(<p>, <h2>, <h3>, <ul>, <li>, <table>)만 출력하고 ```html 코드펜스는 쓰지 마세요.
3. {affiliate_rule}
"""
    last_err = None
    for model_name in MODEL_CANDIDATES:
        for attempt in range(1, RETRIES_PER_MODEL + 1):
            try:
                log(f"[Gemini] 모델 호출 시작: {model_name} (시도 {attempt}/{RETRIES_PER_MODEL})")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                html = (response.text or "").strip()
                html = re.sub(r"^```html\s*|```$", "", html, flags=re.IGNORECASE).strip()
                if html:
                    log(f"[Gemini] 생성 완료: {model_name} (길이 {len(html)}자)")
                    return html
                raise RuntimeError(f"Empty response from {model_name}")
            except (genai_errors.ServerError, genai_errors.APIError, Exception) as err:
                last_err = err
                log(f"[Gemini] {model_name} 실패 ({attempt}/{RETRIES_PER_MODEL}): {err}")
                if attempt < RETRIES_PER_MODEL:
                    time.sleep(RETRY_DELAY_SECONDS)
    raise RuntimeError(f"모든 Gemini 모델 호출 실패: {last_err}")


def get_blogger_service():
    creds_info = json.loads(os.environ["BLOGGER_CREDENTIALS_JSON"])
    creds = Credentials.from_authorized_user_info(
        creds_info, scopes=["https://www.googleapis.com/auth/blogger"]
    )
    return build("blogger", "v3", credentials=creds, cache_discovery=False)


def todays_slots(service, blog):
    # List all current live/scheduled posts, including externally created ones.
    # Account in Asia/Seoul, regardless of the timezone used in Blogger responses.
    from zoneinfo import ZoneInfo
    tz = ZoneInfo("Asia/Seoul")
    today = datetime.datetime.now(tz).date()
    seen = set()
    pages = set()
    token = None
    while True:
        page = service.posts().list(blogId=blog["blog_id"], status=["LIVE", "SCHEDULED"],
            view="ADMIN", fetchBodies=False, maxResults=500, pageToken=token,
            fields="nextPageToken,items(id,published)").execute()
        for item in page.get("items", []):
            dt = datetime.datetime.fromisoformat(item["published"].replace("Z", "+00:00"))
            if dt.tzinfo is None:
                raise ValueError("unknown publication timezone")
            if dt.astimezone(tz).date() == today:
                seen.add(item["id"])
        token = page.get("nextPageToken")
        if not token:
            return max(0, min(2, int(blog["daily_limit"])) - len(seen))
        if token in pages:
            raise ValueError("incomplete publication inventory")
        pages.add(token)


def publish_blogger(service, blog: dict, title: str, html: str, label: str, is_draft: bool):
    log(f"[Blogger] 발행 요청 시작: {blog['name']} (draft={is_draft})")
    body = {
        "kind": "blogger#post",
        "blog": {"id": blog["blog_id"]},
        "title": title,
        "content": html,
        "labels": [label] if label in blog.get("allowed_labels", []) else ["해외여행"],
    }
    res = service.posts().insert(blogId=blog["blog_id"], body=body, isDraft=is_draft).execute()
    log(f"[Blogger] 발행 완료 | draft={is_draft} | url={res.get('url', 'DRAFT')}")


def save_naver_draft(output_dir: str, title: str, html: str, img_url: str):
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(output_dir, f"naver_post_{ts}.html")
    img_tag = f'<p><img src="{img_url}" alt="{title}"></p>\n' if img_url else ""
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"<h1>{title}</h1>\n{img_tag}{html}")
    log(f"[Naver] 10초 복붙용 HTML 저장 완료: {path}")


def run():
    log("[START] Gemini Blog Autopub 파이프라인 시작")
    with open("config/blogs.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)

    trip_id = cfg.get("trip_alliance_id", "10882341")
    for blog in cfg.get("blogs", []):
        if not blog.get("enabled") or blog.get("mode") == "FROZEN":
            log(f"[SKIP] {blog['name']} (동결 상태)")
            continue

        if blog["platform"] == "blogger":
            if (str(blog.get("blog_id")), blog.get("id"), blog.get("mode")) != ("2592561701693494703", "travel_guide", "REVIEW"):
                continue
            try:
                service = get_blogger_service()
                if not todays_slots(service, blog):
                    continue
            except Exception:
                log("[Blogger] 오늘 공개/예약 수 미확인: 쓰기 보류, 네이버 원고 계속")
                continue
        topic, label, img_query = random.choice(TOPICS)
        log(f"[TOPIC] {blog['name']} -> {topic}")
        raw_html = generate_article(topic, blog["mode"], trip_id)
        img_url = fetch_pexels_image(img_query)
        if img_url:
            raw_html = f'<p><img src="{img_url}" alt="{topic}" style="max-width:100%;height:auto;"></p>\n' + raw_html

        if blog["platform"] == "blogger":
            qa = run_triple_qa(topic, raw_html, blog["mode"], max(1300, blog.get("min_chars", 1300)), travel_only=True)
            log(f"[QA] {blog['name']} -> {qa['reason']}")
            publish_blogger(service, blog, topic, qa["html"], label, qa["draft"])
        elif blog["platform"] == "naver_draft":
            qa = run_triple_qa(topic, raw_html, "REVIEW", blog.get("min_chars", 1200))
            save_naver_draft(blog.get("output_dir", "outputs/naver"), topic, qa["html"], img_url)

    log("[DONE] 파이프라인 정상 종료")


if __name__ == "__main__":
    run()
