# 떠나볼 가이드 재신청 장부 — 2026-11-28 KST

**HOLD.** 다음 기준은 사이트 운영자의 사전 검수 기준이며 애드센스 승인 보장이 아니다.
대상은 genesislkh21.blogspot.com / blogId 2592561701693494703 한 곳. REVIEW·하루 최대 2편(KST), 다른 Blogger ID 쓰기 금지, 네이버는 outputs/naver/ 원고만. 이 저장소 외의 기존 발행 작업이 같은 계정을 쓰는 경우도 같은 동결 정책이 적용됐는지 확인한다. 이 패치는 다른 작업의 권한·스케줄을 변경하지 않는다. 제휴는 주석으로 숨기지 말고 본문/테마/가젯/검색 설명에서 해당 블록 자체를 제거한다. APPROVED 확인 전 제휴 활성화 금지.

## 공개 HTML 실측
11월 28일 일반 및 ?m=1 GET, 본문 .post-body의 텍스트 노드 사이 공백·연속 공백 정규화. 공개 HTML(본문, 링크 속성, 메타·공통 가젯 포함)에 알려진 쿠팡/Trip.com/10882341/제휴 고지 표식 없음. 보이는 본문의 주석 꼬리도 미검출. 홈 HTML도 표식 없음. 동적/개인화 렌더나 Google의 저장본까지 확인한 것은 아니다. 다음은 /2026/11/ 아래 URL. 아래 글의 ?m=1도 같은 HTTP 상태, 정상 응답의 canonical은 기본 URL. 이 조회에서 리디렉션 루프 미재현. 11/26 GSC 오류 원인은 당시 예시 URL·크롤링 기록 확인 전 미확정.

|순서|URL|HTTP/자수|조치|
|---|---|---|---|
|1|blog-post_22.html|200 / 1391|해외 구글 번역. 본문/가젯 클린, 기본 URL 실시간 검사 후 재색인 1회 후보|
|2|blog-post_15.html|200 / 1274|면도기 기내 반입. 초안 격리→공식 근거·실용 예외 보완 후 재검수|
|2|blog-post_23.html|200 / 1230|렌터카 경유지. 같은 ID로 보완 전 재색인 제외|
|2|blog-post_25.html|200 / 1085|아이폰 오프라인 지도. 같은 ID로 보완 전 재색인 제외|
|제외|blog-post_12.html|404|초안인지 삭제인지는 관리자 확인. 색인 요청하지 않음|
|제외|blog-post_28.html|404|동일. 스니펫만 보고 복원하지 않음|

## 격리
/2026/10/11-24h2-10-13-pc.html 직접 응답 200, 1655자, ID 2358790464825852127. 길이는 통과하나 여행과 무관. 관리자의 같은 글에서 백업 후 ‘초안으로 되돌리기’ → 같은 ID가 초안 목록에 남았는지 확인. 다른 블로그 자동 이전·삭제·재발행 없음.
또는 기존 승인된 환경에서 저장소 루트 기준 아래 명령 사용. 첫 명령은 읽기 전용, 두 번째만 쓰기. 실서버에서 이번 작업으로 실행하지 않았다.

    python src/quarantine_review.py 2358790464825852127
    python src/quarantine_review.py 2358790464825852127 --apply-digest <직전출력SHA256> --backup-dir <비공개백업경로>

얇은 세 글도 도구에 지정된 ID만 같은 절차로 처리. 원문·상태가 바뀌면 재검토. 쓰기 결과 불명 시 재전송 말고 관리자에서 같은 ID를 확인한다. 로컬 백업 파일은 Git에 커밋하지 않는다.

## 재색인 및 신청 체크리스트
1. Blogger 설정에서 맞춤 robots.txt와 맞춤 로봇 헤더 태그 **각각 OFF** 확인. 공개 파일만으로 토글값을 추정하지 않는다. /ads.txt 실측: google.com, pub-7605696144276072, DIRECT, f08c47fec0942fa0 한 줄.
2. 공개 글의 본문·검색 설명·레이아웃 HTML/JavaScript 및 모바일 렌더에서 제휴 문구/링크/10882341/노출 주석 찌꺼기를 확인한다. 실제 잔존 시 해당 블록만 제거하고 저장·재열람. 홈 스니펫 정상화는 11/27 사용자 관측.
3. GSC URL 검사에 ?m=1 없는 정규 URL 입력 → Google 색인 상태·선택 표준 URL·최근 크롤링일 기록 → 실제 URL 테스트에서 렌더 HTML·robots·상태 확인. 공개 의도/여행 일치/1300자 이상/클린인 경우만 색인 생성 요청 1회. 이미 수정 후 재크롤링·스니펫 갱신 확인된 URL은 반복 신청하지 않는다. 실패한 예시가 확보되면 최초/최종 URL·HTTP 상태·표준 URL을 대조한다.
4. docs/review-evidence.json 장부는 사람이 확인한 증거만 기록. 동일 canonical은 한 번만. posts 각 행에 canonical, google_canonical, status=LIVE, chars, travel_match, page_clean, indexed, snippet_clean, checked_at, inspection_evidence, snippet_evidence 기록. 실제 검색어·스니펫·확인일과 GSC URL 검사 증거를 구분한다. 소개·개인정보·홈·404·초안은 15편에서 제외한다.
5. python src/review_gate.py docs/review-evidence.json → HOLD면 보류. 클린 여행 글 15편 이상 색인과 스니펫 갱신, 설정·격리·가젯 확인까지 READY이면 Blogger → 떠나볼 가이드 → 수익 → 연결된 게시자 계정/사이트 확인 → 화면에 제공되는 심사 요청 경로로 한 번 제출. 요청 영수증과 승인 결과는 구분한다.

공식 참고: https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl?hl=ko · https://developers.google.com/search/docs/appearance/snippet · https://developers.google.com/blogger/docs/3.0/reference/posts/revert · https://support.google.com/blogger/answer/1269077

## 이후 관리자 확인 (11/28)
본문의 최초 감사 이후 얇은 글 4편 및 주제 이탈 글 2편은 실제 초안으로 전환했다. 위 명령을 재실행할 필요가 없다. 현재 공개 48편, 초안 24편. 공개 가이드 목록을 48편으로 조정했다. 두 맞춤 로봇 설정 OFF. Search Console 색인·스니펫은 아직 미확인.
