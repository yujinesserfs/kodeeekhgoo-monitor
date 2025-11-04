import requests
from bs4 import BeautifulSoup
import hashlib
import os

URL = "https://wonyoddi.com/ccts/deog.ku"
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def fetch_latest_position():
    r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # "최근 7일간 포지션" 문구 찾기
    target = soup.find("p", string=lambda t: t and "최근 7일간 포지션" in t)
    if not target:
        print("⚠️ '최근 7일간 포지션' 문구를 찾지 못했습니다.")
        return None

    # 그 다음 나오는 테이블 찾기
    table = target.find_next("table")
    if not table:
        print("⚠️ 포지션 테이블을 찾지 못했습니다.")
        return None

    # 첫 번째 데이터 행만 추출
    first_row = table.select_one("tbody tr")
    if not first_row:
        print("⚠️ 테이블 안에 데이터가 없습니다.")
        return None

    cells = [td.get_text(strip=True) for td in first_row.find_all("td")]
    position_text = " | ".join(cells)
    print(f"✅ 최신 포지션: {position_text}")
    return position_text

def send_telegram(msg):
    tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg}
    requests.post(tg_url, data=payload)

def main():
    print("🔹 Fetching last_hash from environment or store")
    last_hash = os.getenv("LAST_HASH", "")

    print("🔹 Fetching latest position from webpage...")
    latest = fetch_latest_position()
    if not latest:
        return {"last_hash": last_hash}

    current_hash = hashlib.sha256(latest.encode()).hexdigest()

    if current_hash != last_hash:
        print("📢 변경 감지됨! 텔레그램 발송 중...")
        message = f"📊 코덕후 신규 포지션 감지!\n\n{latest}\n\n👉 {URL}"
        send_telegram(message)
        print("✅ 전송 완료!")
        return {"last_hash": current_hash}
    else:
        print("🔸 변화 없음.")
        return {"last_hash": last_hash}

if __name__ == "__main__":
    main()
