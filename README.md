# gemini_blog_autopub_v1_0 설치 및 실행 가이드

1. GitHub 저장소 생성 후 이 ZIP 파일의 압축을 풀어 전체 파일을 업로드합니다.
2. `config/blogs.json`의 `YOUR_TRAVEL_GUIDE_BLOG_ID`에 떠나볼 가이드의 Blogger ID를 입력합니다.
3. GitHub 저장소 `Settings -> Secrets and variables -> Actions -> Secrets`에 아래 3가지를 등록합니다.
   - `GEMINI_API_KEY`: Google AI Studio 무료 티어 API 키
   - `PEXELS_API_KEY`: Pexels 무료 API 키
   - `BLOGGER_CREDENTIALS_JSON`: Blogger OAuth 인증 JSON 문자열
4. `Actions` 탭에서 `Gemini Blog Autopub v1.0` -> `Run workflow`를 눌러 1회 테스트합니다.
