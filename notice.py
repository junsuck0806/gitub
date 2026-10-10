import json
import os
import requests
from bs4 import BeautifulSoup

# ===== 설정 (본인 학교에 맞게 수정) =====
NOTICE_URL = "https://여기에-공지-게시판-주소"   # 학교 공지 목록 페이지
BASE_URL = "https://여기에-학교-도메인"           # 링크가 상대경로일 때 앞에 붙일 주소
ROW_SELECTOR = "table tbody tr"                  # 게시글 한 줄을 가리키는 선택자
TITLE_SELECTOR = "a"                             # 줄 안에서 제목/링크 선택자
# ======================================

WEBHOOK = os.environ["DISCORD_WEBHOOK"]
STATE_FILE = "last_seen.json"


def fetch_notices():
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(NOTICE_URL, headers=headers, timeout=15)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    notices = []
    for row in soup.select(ROW_SELECTOR):
        a = row.select_one(TITLE_SELECTOR)
        if not a or not a.get("href"):
            continue
        title = a.get_text(strip=True)
        link = a["href"]
        if link.startswith("/"):
            link = BASE_URL + link
        notices.append({"title": title, "link": link})
    return notices


def load_seen():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    return None  # 첫 실행


def save_seen(links):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(links), f, ensure_ascii=False, indent=2)


def send_discord(n):
    requests.post(
        WEBHOOK,
        json={"content": f"📢 **새 공지**\n{n['title']}\n{n['link']}"},
        timeout=15,
    )


def main():
    notices = fetch_notices()
    seen = load_seen()
    current = {n["link"] for n in notices}

    if seen is None:
        # 첫 실행: 기존 글은 전부 '본 것'으로 처리 (알림 폭탄 방지)
        save_seen(current)
        print("첫 실행: 현재 공지를 저장만 했습니다.")
        return

    new = [n for n in notices if n["link"] not in seen]
    for n in reversed(new):  # 오래된 글부터 전송
        send_discord(n)

    save_seen(seen | current)
    print(f"새 공지 {len(new)}개 전송")


if __name__ == "__main__":
    main()
