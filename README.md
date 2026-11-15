# 코레일 일정 등록

코레일톡 승차권의 공유 문구를 읽어 iPhone 기본 캘린더에 저장하는 Apple 단축어입니다. 공유 메뉴에서 **코레일 일정 등록**을 선택하면 출발·도착역과 출발 시각으로 제목을 만들고, 출발부터 도착까지의 시간을 일정으로 등록합니다.

**[단축어 다운로드](https://github.com/jaeyoung103/korail-calendar-shortcut/releases/latest/download/Korail-Calendar.shortcut)** · [릴리스 페이지](https://github.com/jaeyoung103/korail-calendar-shortcut/releases/latest)

## 설치 및 사용

1. iPhone에서 단축어 파일을 내려받고 파일 앱에서 엽니다. 단축어 앱에서 **단축어 추가**를 탭합니다. 가져온 이름이 **Korail-Calendar**로 표시되면 편집 화면에서 **코레일 일정 등록**으로 바꿀 수 있습니다.
2. 코레일톡에서 승차권을 열고 **일정 공유 → 코레일 일정 등록**을 탭합니다. 공유 메뉴에는 가져온 단축어 이름이 표시됩니다.
3. 첫 실행에서 캘린더 접근을 요청하면 허용합니다. 일정은 기기의 기본 캘린더에 저장됩니다.

공유 메뉴에 단축어가 안 보이면 단축어 편집 화면의 **세부사항 → 공유 시트에서 보기**를 확인하세요. 코레일톡에서 공유 문구를 복사한 경우에는 단축어 앱에서 직접 실행해 붙여넣을 수도 있습니다. Mac에서 파일을 가져온 뒤 [iCloud 단축어 동기화](https://support.apple.com/ko-kr/guide/shortcuts-mac/apdb3a4240b0/mac)로 iPhone에 추가하는 방법도 있습니다.

## 동작 예시

아래는 설명용 승차권 문구입니다.

~~~text
2027년 1월 18일
부산(09:20)출발 -> 서울(12:05)도착
~~~

| 캘린더 항목 | 저장되는 값 |
| --- | --- |
| 제목 | 부산 → 서울 (09:20) |
| 시작 | 2027년 1월 18일 09:20 |
| 종료 | 2027년 1월 18일 12:05 |

출발과 도착 시각은 한국 시간으로 처리합니다. 도착 시각이 출발 시각보다 이르면 종료 날짜를 다음 날로 잡습니다. 여러 건이 한 번에 전달되면 인식한 첫 승차권을 등록합니다. 같은 승차권을 다시 공유하면 일정이 추가로 생성될 수 있습니다.

## Codex로 만들어보기

[복사해서 쓸 Codex 프롬프트](PROMPT.md)를 준비했습니다. 여기에 날짜와 구간이 들어 있는 본인의 공유 문구 형식을 예시로 넣으면 됩니다.

## 소스에서 빌드

[생성 스크립트](scripts/build_shortcut.py)는 Python 표준 라이브러리로 단축어 파일 두 개를 만듭니다. 일반 파일은 캘린더에 일정을 추가하고, 이름에 Check가 붙은 파일은 제목과 시작·종료 시각을 출력합니다.

~~~sh
python3 scripts/build_shortcut.py
shortcuts sign --mode anyone \
  --input "scripts/Korail Calendar.shortcut" \
  --output "Korail-Calendar.shortcut"
~~~

파일 서명에는 Mac의 [Apple 단축어 명령줄 도구](https://support.apple.com/guide/shortcuts-mac/run-shortcuts-from-the-command-line-apd455c82f02/mac)가 필요합니다.

코레일톡 공유 문구가 바뀌어 일정이 등록되지 않으면 [GitHub Issues](https://github.com/jaeyoung103/korail-calendar-shortcut/issues)에 예약번호와 QR을 지운 텍스트 예시를 남겨 주세요. 코레일과 제휴하지 않은 개인 프로젝트입니다.
