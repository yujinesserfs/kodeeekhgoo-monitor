import requests
from bs4 import BeautifulSoup
import hashlib
import os

URL = "https://wonyoddi.com/ccts/deog.ku"
TELEGRAM_BOT_TOKEN = "7224032782:AAHBXmnjmA35snzrAILttCX18Tkf2B6okeg"
TELEGRAM_CHAT_ID = "6906316966"
HASH_FILE = "last_hash.txt"


def get_page_hash():
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
            positions.append(f"{symbol}|{size}|{entry}")

    key_text = "\n".join(positions)
    return hashlib.sha256(key_text.encode("utf-8")).hexdigest(), key_text


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    requests.post(url, data=payload)


def main():
    current_hash, content = get_page_hash()

    # 이전 해시 불러오기
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            last_hash = f.read().strip()
    else:
        last_hash = ""

    if last_hash != current_hash:
        send_telegram(f"📈 코덕후 포지션 변경 감지!\n\n{content}")
        with open(HASH_FILE, "w") as f:
            f.write(current_hash)
        print("✅ 변경 감지됨 → 텔레그램 전송 완료")
    else:
        print("변화 없음.")


if __name__ == "__main__":
    main()
