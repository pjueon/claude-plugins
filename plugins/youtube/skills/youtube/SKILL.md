---
name: youtube
description: >-
  yt-dlp를 호출해 유튜브 영상을 검색·요약·다운로드한다. 사용자가 "이 유튜브 영상 요약해줘",
  "유튜브 링크 내용 정리", "유튜브에서 ~ 검색해줘", "이 영상 다운로드/오디오만 추출" 처럼
  유튜브 URL·키워드를 다루거나 영상 내용을 알고 싶어 할 때 사용한다. 수집(yt-dlp)과
  가공(요약)을 분리하고, 조회수·날짜 등 수치는 LLM을 거치지 않고 yt-dlp로 직출력한다.
  멤버십(로그인 필요) 영상은 Firefox 전용 프로파일 쿠키로 인증한다.
---

# youtube

`yt-dlp` CLI를 bash로 호출해 유튜브를 다룬다. 핵심 3종은 **검색 · 내용 파악(자막→요약)
· 다운로드**다. MCP나 별도 서버 없이 SKILL.md + bash 호출로 충분하다.

## 핵심 원칙

1. **수집과 가공을 분리한다.** yt-dlp는 데이터(자막·메타·파일)를 가져오는 데만 쓰고,
   요약·번역 같은 가공은 Claude가 한 뒤 처리한다.
2. **수치·메타는 LLM을 거치지 않는다.** 조회수·좋아요·업로드일·제목 등은 `--print`로
   yt-dlp가 직출력한 값을 그대로 쓴다. 환각 금지.
3. **긴 텍스트(자막)만 요약한다.** 자막을 받아 Claude가 직접 요약한다.
4. **항상 쿠키를 사용한다.** 모든 yt-dlp 호출에 Firefox 전용 프로파일 쿠키를 붙여,
   공개/멤버십 구분 없이 동일하게 동작하게 한다(아래 "사전 준비" 참조).
5. **에러는 삼키지 않는다.** 미설치·인증 만료·자막 없음 등은 추측으로 넘어가지 말고
   실제 종료코드·에러 메시지를 근거로 사용자에게 안내한다.

## 사전 준비 — 전용 Firefox 프로파일 (`YT_FIREFOX_PROFILE`)

멤버십 영상 인증과 안정적 접근을 위해, **메인 브라우저와 분리된 yt-dlp 전용 Firefox
프로파일**의 절대 경로를 환경변수 `YT_FIREFOX_PROFILE`에 등록해 둔다. (브라우저를
열어둔 채 yt-dlp를 돌려도 `cookies.sqlite` 잠금 충돌이 없게 하려면 전용 프로파일이
필수다. Chrome은 App-Bound Encryption으로 외부 복호화가 막혀 있어 Firefox를 쓴다.)

**값 확인:** 작업 시작 시 `echo "$YT_FIREFOX_PROFILE"`로 설정 여부를 본다.

- **이미 설정돼 있으면** 그대로 사용한다. 바로 작업 진행.
- **비어 있으면**, 아래 1회성 셋업을 안내하고 사용자가 마치면 진행한다. 임의 경로를
  추측하지 말 것.

### 1회성 셋업 (사용자가 GUI에서 직접)

1. 전용 프로파일 생성 (PowerShell):
   ```powershell
   & "C:\Program Files\Mozilla Firefox\firefox.exe" -CreateProfile "ytdlp $env:USERPROFILE\firefox-ytdlp"
   ```
2. 그 프로파일로 Firefox를 띄워 **유튜브에 로그인**(멤버십 계정):
   ```powershell
   & "C:\Program Files\Mozilla Firefox\firefox.exe" -P "ytdlp" -no-remote
   ```
3. 경로를 환경변수로 영구 등록:
   ```powershell
   [Environment]::SetEnvironmentVariable("YT_FIREFOX_PROFILE", "$env:USERPROFILE\firefox-ytdlp", "User")
   ```
   → 등록 후에는 **터미널/IDE를 재시작**해야 새 값이 잡힌다. 단, 지금 세션에서는
   사용자가 알려준 경로를 변수에 바로 넣어 이어서 작업하면 된다.

> 로그인 상태는 프로파일에 저장되므로, 한 번 로그인해 두면 이후 호출은 무인으로 동작한다.
> 쿠키는 수주~수개월 유지되며 사이트 재방문 시 자동 갱신된다. 만료되면 2단계 GUI 로그인만
> 다시 한 번 하면 된다(headless로는 재로그인 불가).

### 공통 인자 (쿠키 + JS 런타임) — `$COMMON`

YouTube는 영상 포맷을 내주기 전에 **JS "n 챌린지"** 를 요구한다. 이를 풀려면 (1) JS
런타임과 (2) yt-dlp의 EJS 솔버 스크립트가 둘 다 있어야 한다. 따라서 **모든 yt-dlp
호출**에 쿠키 + 아래 두 플래그를 함께 붙인다:

```bash
COMMON="--cookies-from-browser firefox:$YT_FIREFOX_PROFILE/ --js-runtimes node --remote-components ejs:github"
```

- `--cookies-from-browser firefox:<프로파일경로>/` — 멤버십/일반 공통 인증. `firefox:`
  뒤에 프로파일 디렉터리 절대 경로(끝에 `/` 권장).
- `--js-runtimes node` — 시스템 PATH의 `node`를 챌린지 솔버 런타임으로 쓴다(node 설치돼
  있음). **전체 경로를 쓰지 말 것**(경로 공백이 단어분리로 깨진다). 이름 `node`만 주면
  yt-dlp가 PATH에서 `node.exe`를 찾는다.
- `--remote-components ejs:github` — 챌린지 솔버 스크립트(EJS)를 GitHub에서 받아 캐시한다.
  이게 없으면 `n challenge solving failed` → "Only images are available"로 실패한다.

> 이 두 플래그가 없으면 인증이 통과해도(`members-only` 거부는 안 떠도) 포맷 추출이 실패해
> `Requested format is not available`가 난다. 셋 다 항상 함께 쓴다.
>
> 사용 예: `yt-dlp $COMMON <기능별 인자> "URL"`. (`YT_FIREFOX_PROFILE` 경로에 공백이
> 없다는 전제 — 있으면 배열 `"${COMMON[@]}"` 형태로 바꾼다.)

(`YT_FIREFOX_PROFILE`이 비어 있으면 위 셋업을 먼저 안내한다.)

## 입력 판별

- `youtube.com/watch?v=` · `youtu.be/` 단일 영상 URL → **내용 파악** 또는 **다운로드**
- `youtube.com/playlist?list=` · `&list=` → 플레이리스트 다운로드(기능 3-3, N번째부터/범위 지원)
- URL이 아닌 자연어 → **검색**

요청 동사로 의도를 가른다: "요약/정리/무슨 내용" → 내용 파악, "받아줘/다운로드/오디오" →
다운로드, "찾아줘/검색" → 검색.

## 기능 1 — 검색

키워드로 후보를 뽑아 제목·조회수·길이와 함께 보여준다. 메타는 `--print` 직출력.

```bash
yt-dlp $COMMON "ytsearch8:키워드" \
  --print "%(title)s | %(id)s | 조회수:%(view_count)s | %(duration_string)s | %(uploader)s" \
  --skip-download
```

- 개수는 `ytsearchN:`의 N으로 조절(기본 8 정도).
- 결과를 표/목록으로 정리해 보여주고, 사용자가 고르면 그 URL로 내용 파악·다운로드로 넘어간다.

## 기능 2 — 내용 파악 (자막 → 요약)

자막을 받아 Claude가 직접 요약한다. **수치 컨텍스트(제목·조회수·업로드일)는 먼저
`--print`로 뽑아 두고**, 자막 본문만 요약에 쓴다.

### 2-1. 메타 직출력 (요약 머리말용)

```bash
yt-dlp $COMMON --skip-download \
  --print "제목:%(title)s\n채널:%(uploader)s\n조회수:%(view_count)s\n업로드:%(upload_date)s\n길이:%(duration_string)s" \
  "URL"
```

### 2-2. 자막 확보 (폴백 3단계)

수동 자막 → 자동생성 자막 → (둘 다 없으면) Whisper 전사 순으로 폴백한다.

```bash
# (a) 가용 자막 확인
yt-dlp $COMMON --list-subs --skip-download "URL"

# (b) 한국어/영어 수동 자막 우선, 없으면 자동생성까지 허용해 현재 폴더에 받기
yt-dlp $COMMON --skip-download \
  --write-subs --write-auto-subs \
  --sub-langs "ko,en" --sub-format "vtt/srt/best" \
  -o "%(title)s.%(ext)s" "URL"
```

- 받은 `.vtt`/`.srt` 파일을 Read로 읽어 타임스탬프·중복 라인을 정리한 뒤 요약한다.
- **자막이 전혀 없으면** Whisper 폴백: 오디오만 받아 전사한다(추가 의존성·시간 소요가
  크므로, 진행 전 사용자에게 "자막이 없어 음성 전사를 시도할까요?"라고 확인한다).
  ```bash
  yt-dlp $COMMON -x --audio-format mp3 -o "%(title)s.%(ext)s" "URL"
  # 이후 whisper / faster-whisper로 전사
  ```

### 2-3. 요약

자막 본문을 Claude가 요약한다. 길이가 매우 길면 단락 단위로 나눠 부분 요약 후 통합한다.
출력 머리말에 2-1의 메타(제목·채널·조회수·업로드일·길이)를 붙여 맥락을 준다.

## 기능 3 — 다운로드

저작권상 받을 권리가 있는 콘텐츠(본인 멤버십 포함) 전제로만 사용한다.

### 3-0. 백그라운드가 기본

영상 다운로드는 오래 걸릴 수 있으므로 **Bash 도구의 `run_in_background: true`로 띄우는
것을 기본**으로 한다. 시작했음을 사용자에게 알리고, 완료 알림이 오면 최종 경로를 보고한다.
짧은 메타 조회·자막 받기 등은 포그라운드로 해도 된다.

### 3-1. 기본 다운로드 (다국어 음성트랙 선호 순서 적용)

영상에 여러 음성트랙(더빙)이 있을 때 **한국어 → 일본어 → 영어 → 그 외(원본/베스트)**
순으로 고른다. `lang:` *정렬*은 듣지 않으므로, **언어 *필터* + 폴백 체인**으로 한다
(`language^=` 은 `pt-BR` 같은 지역변형도 접두 매칭):

```bash
# 화질 1080p 이하, 음성트랙 ko>ja>en>기타 우선
yt-dlp $COMMON \
  -f "bv*[height<=1080]+ba[language^=ko]/bv*[height<=1080]+ba[language^=ja]/bv*[height<=1080]+ba[language^=en]/bv*[height<=1080]+ba/b[height<=1080]" \
  -o "%(title)s.%(ext)s" "URL"
```

- 화질만 바꾸려면 `height<=720` 등으로. 단순 다운로드(트랙 신경 안 씀)면 기존처럼
  `-S "res:1080"`만 써도 된다.
- **사용자가 특정 언어를 지정하면** 그 언어를 체인 맨 앞에 둔다. 예: 프랑스어 우선 →
  맨 앞에 `bv*+ba[language^=fr]/` 를 붙인다. "프랑스어 음성으로"처럼 단일 지정이면
  `-f "bv*+ba[language^=fr]/bv*+ba"` 로 그 트랙만.
- 가용 음성 언어를 먼저 보려면: `yt-dlp $COMMON -F "URL"` 출력의 `[ko]`,`[ja]` 등 태그
  또는 `--print "%(language)s"`로 확인한다.

### 3-2. 오디오만 추출

```bash
yt-dlp $COMMON -x --audio-format mp3 \
  -f "ba[language^=ko]/ba[language^=ja]/ba[language^=en]/ba" \
  -o "%(title)s.%(ext)s" "URL"
```

### 3-3. 재생목록 — N번째부터 / 범위

`-I`(items)로 시작 지점·범위를 지정한다. 사용자가 "N번째부터"라고 하면 `-I N:`.

```bash
yt-dlp $COMMON -I 5:   -o "%(playlist_index)03d_%(title)s.%(ext)s" "PLAYLIST_URL"   # 5번째부터 끝까지
yt-dlp $COMMON -I 5:10 -o "%(playlist_index)03d_%(title)s.%(ext)s" "PLAYLIST_URL"   # 5~10번째
yt-dlp $COMMON -I 3,7,9 ...                                                          # 특정 항목만
```

- `%(playlist_index)03d_`로 순서 번호를 파일명 앞에 붙이면 정렬이 쉽다.
- 항목이 많으면 시간이 오래 걸리니 **반드시 백그라운드로**.

### 3-4. (옵션) 다국어 음성을 한 파일에 — 멀티오디오 트랙 mkv

여러 음성트랙을 **모두 받아 하나의 멀티오디오 영상**으로 만들 수 있다. **기본이 아닌
옵션**이며, 사용자가 명시적으로 원할 때만 쓴다. `--audio-multistreams`로 여러 오디오를
머지하고 컨테이너는 **mkv 권장**(여러 트랙·코덱을 안전하게 담음; 언어 메타데이터 보존).

```bash
# ko + ja + en 3개 음성트랙을 한 mkv에 (맨 앞 트랙이 기본 트랙이 됨)
yt-dlp $COMMON --audio-multistreams --merge-output-format mkv \
  -f "bv*+ba[language^=ko]+ba[language^=ja]+ba[language^=en]" \
  -o "%(title)s.%(ext)s" "URL"
```

- **난이도: 낮음.** 표준 플래그 조합으로 동작하며 mkv에 트랙별 언어가 들어간다.
- **유일한 수고:** "전부 다" 받으려면 단일 와일드카드가 없어서, 먼저 `-F`/`--print
  "%(language)s"`로 존재하는 언어를 열거한 뒤 `+ba[language^=..]`를 언어 수만큼 이어
  붙여 셀렉터를 만들어야 한다.
- 트랙이 늘수록 용량이 커진다. mp4도 다중 오디오가 되긴 하나 코덱 호환 이슈가 있어 mkv가 안전.

> 모든 다운로드의 포맷 머지·오디오 추출·mkv muxing에 `ffmpeg`가 쓰인다(설치됨).

## 출력 규칙

- 검색·요약·메타 결과 및 다운로드 파일은 모두 **현재 작업 디렉터리**에 저장하고,
  최종 경로를 사용자에게 알린다. 별도 vault/폴더로 옮기지 않는다(사용자가 요청하면 그때).
- 요약을 파일로 남길 때는 `<영상 제목>.md`로 현재 폴더에 저장한다.

## 인증·에러 처리

판정은 **종료코드와 에러 메시지**를 근거로 한다. 추측 금지.

- **미설치** (`command not found`): yt-dlp/ffmpeg 미설치를 알리고 설치 안내.
- **인증 만료 / 멤버십 접근 실패** (`Sign in`, `members-only`, `This video is
  available to members`, HTTP 403 등): 쿠키 만료로 보고, 사전 준비 2단계(GUI 재로그인)를
  안내한다. headless로는 재로그인 불가.
- **`YT_FIREFOX_PROFILE` 미설정**: "사전 준비" 셋업을 먼저 안내한다.
- **JS 챌린지 실패** (`n challenge solving failed`, `Only images are available`,
  `Requested format is not available`): 공통 인자의 `--js-runtimes node
  --remote-components ejs:github`가 빠졌거나 node 미설치다. 두 플래그를 붙였는지 먼저
  확인하고, `node --version`으로 런타임 존재를 본다.
- **자막 없음** (`There are no subtitles`): 위 2-2 Whisper 폴백 여부를 사용자에게 확인.
- 그 외 실패는 yt-dlp의 에러 원문을 그대로 인용해 보여주고, 단정하지 않는다.

## 주의

- 다운로드는 본인이 저작권상 받을 권리가 있는 콘텐츠(본인 멤버십 포함) 전제로만 한다.
- 댓글 수집은 범위 밖이다. 필요하면 사용자에게 알리고 별도로 확장한다.
