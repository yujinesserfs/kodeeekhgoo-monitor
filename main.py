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

    # "최근 7일간 포지션" 문구를 포함한 p 태그 찾기 (속성 무시)
    target = None
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if "최근 7일간 포지션" in text:
            target = p
            break

    if not target:
        print("⚠️ '최근 7일간 포지션' 문구를 찾지 못했습니다.")
        return None

    # 그 다음 테이블 찾기
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
        return
