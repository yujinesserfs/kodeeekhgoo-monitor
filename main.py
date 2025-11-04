import requests
from bs4 import BeautifulSoup
import hashlib
import os

# ===== 설정 =====
URL = "https://wonyoddi.com/ccts/deog.ku"
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"
HASH_FILE = "last_hash.txt"
# =================

def get_latest_position():
    r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # “최근 7일간 포지션” 섹션 찾기
    section = soup.find("h3", string=lambda x: x and "최근 7일간 포지션" in x)
    if not section:
        return None, None

    table = section.find_next("table")
    rows = table.find_all("tr")[1:]  # 헤더 제외

    if not rows:
        return None, None

    # 🔹 가장 최근 1개 행만 추출
    first_row = rows[0]
    cols = [c.get_text(strip=True) for c in first_row.find_all("td")]
    if len(cols) < 7:
        return None, None

    symbol, size, avg_price, market_price, time, action, pnl = cols[:7]
    position_text = f"{symbol} | {action} | {pnl} | {time}"
    hash_val = hashlib.sha256(position_text.encode("utf-8")).hexdigest()

    # 메시지 구성
    formatted = (
        f"📢 코덕후 새 포지션 감지!\n"
        f"심볼: {symbol}\n"
        f"액션: {action}\n"
        f"PNL: {pnl}\n"
        f"시간: {time}\n\n"
        f"👉 [워뇨띠 바로가기]({URL})"
    )

    return hash_val, formatted


def send_telegram(msg):
    tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    requests.post(tg_url, data=payload)


def main():
    current_hash, msg = get_latest_position()
    if not current_hash:
        print("⚠️ 최근 7일간 포지션을 찾지 못함.")
        return

    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            last_hash = f.read().strip()
    else:
        last_hash = ""

    if last_hash != current_hash:
        send_telegram(msg)
        with open(HASH_FILE, "w") as f:
            f.write(current_hash)
        print("✅ 새 포지션 감지 → 텔레그램 전송 완료")
    else:
        print("변화 없음.")


if __name__ == "__main__":
    main()
