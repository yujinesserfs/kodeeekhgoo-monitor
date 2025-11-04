import requests
from bs4 import BeautifulSoup
import hashlib
import os
import sys

URL = "https://wonyoddi.com/ccts/deog.ku"
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def fetch_latest_position():
    r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # "최근"과 "포지션" 문구 포함한 <p> 찾기
    target = None
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if "최근" in text and "포지션" in text:
            target = p
            break

    if not target:
        print("⚠️ '최근 7일간 포지션' 문구를 찾지 못했습니다.")
        return None

    # 바로 다음 table 탐색
    table = target.find_next("table")
    if not table:
        print("⚠️ 포지션 테이블을 찾지 못했습니다.")
        return None

    # 첫 번째 데이터 행 (tbody 없을 수도 있으니 유연하게)
    first_row = table.select_one("tbody tr") or table.select_one("tr:nth-of-type(2)")
    if not first_row:
        print("⚠️ 테이블 안에 데이터가 없습니다.")
        return None

    # 셀 내용 추출
    cells = [td.get_text(strip=True) for td in first_row.find_all("td")]
    position_text = " | ".join(cells)
    print(f"✅ 최신 포지션: {position_text}")
    return position_text

def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ TELEGRAM 설정이 누락되었습니다.")
        return
    tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg}
    requests.post(tg_url, data=payload)

def main():
    print("🔹 Fetching last_hash from environment or store")
    last_hash = os.getenv("LAST_HASH", "").strip()

    print("🔹 Fetching latest position from webpage...")
    latest = fetch_latest_position()
    if not latest:
        sys.exit(0)

    # 새 해시 생성
    new_hash = hashlib.sha256(latest.encode()).hexdigest()

    if new_hash == last_hash:
        print("✅ 변경 없음. (same hash)")
    else:
        print("🚨 새로운 포지션 감지됨!")
        send_telegram(f"📢 새로운 포지션 발견!\n\n{latest}\n\n🔗 {URL}")
        # GitHub Action에서 환경 저장용 출력
        print(f"::set-output name=last_hash::{new_hash}")

if __name__ == "__main__":
    main()
