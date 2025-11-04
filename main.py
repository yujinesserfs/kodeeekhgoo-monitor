import requests
from bs4 import BeautifulSoup
import hashlib
import os

URL = "https://wonyoddi.com/ccts/deog.ku"
TELEGRAM_BOT_TOKEN = "7224032782:AAHBXmnjmA35snzrAILttCX18Tkf2B6okeg"
TELEGRAM_CHAT_ID = "6906316966"
HASH_FILE = "last_hash.txt"


def get_page_hash_and_text():
    r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    rows = soup.select("table tr")[1:]  # 헤더 제외
    positions = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 3:
            symbol = cells[0].get_text(strip=True)
            size = cells[1].get_text(strip=True)
            entry = cells[2].get_text(strip=True)
            positions.append((symbol, size, entry))

    # 표 형태의 텍스트 생성
    formatted = "심볼 | 수량 | 진입가\n" + "-"*25 + "\n"
    for p in positions:
        formatted += f"{p[0]:<8} | {p[1]:<8} | {p[2]}\n"

    key_text = "\n".join([f"{p[0]}|{p[1]}|{p[2]}" for p in positions])
    page_hash = hashlib.sha256(key_text.encode("utf-8")).hexdigest()
    return page_hash, formatted


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"  # 코드블록, 줄바꿈 적용
    }
    requests.post(url, data=payload)


def main():
    current_hash, table_text = get_page_hash_and_text()

    # 이전 해시 불러오기
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            last_hash = f.read().strip()
    else:
        last_hash = ""

    if last_hash != current_hash:
        msg = f"📈 *코덕후 포지션 변경 감지!*\n```\n{table_text}\n```"
        send_telegram(msg)
        with open(HASH_FILE, "w") as f:
            f.write(current_hash)
        print("✅ 변경 감지 → 텔레그램 전송 완료")
    else:
        print("변화 없음.")


if __name__ == "__main__":
    main()
