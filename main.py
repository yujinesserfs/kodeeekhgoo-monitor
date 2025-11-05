import os
import hashlib
import requests
from bs4 import BeautifulSoup

URL = "https://wonyoddi.com/ccts/deog.ku"
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HASH_FILE = "last_hash.txt"  # 런 간 저장 파일

def fetch_latest_position():
    try:
        r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        target = None
        for p in soup.find_all("p"):
            if "최근 7일간 포지션" in p.get_text():
                target = p
                break

        if not target:
            print("⚠️ '최근 7일간 포지션' 문구를 찾지 못했습니다.")
            return None

        table = target.find_next("table")
        if not table:
            print("⚠️ 포지션 테이블을 찾지 못했습니다.")
            return None

        first_row = table.select_one("tbody tr") or table.select_one("tr:nth-of-type(2)")
        if not first_row:
            print("⚠️ 테이블 안에 데이터가 없습니다.")
            return None

        cells = [td.get_text(strip=True) for td in first_row.find_all("td")]
        position_text = " | ".join(cells)
        print(f"✅ 최신 포지션: {position_text}")
        return position_text

    except Exception as e:
        print("❌ 오류:", e)
        return None

def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ TELEGRAM 환경변수 없음")
        return
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=10
        )
        if r.status_code == 200:
            print("📩 텔레그램 전송 완료")
        else:
            print("⚠️ 텔레그램 전송 실패:", r.text)
    except Exception as e:
        print("❌ 텔레그램 오류:", e)

def main():
    # 이전 해시 읽기
    last_hash = ""
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            last_hash = f.read().strip()
    print("🔹 이전 해시:", last_hash)

    # 최신 포지션 가져오기
    latest = fetch_latest_position()
    if not latest:
        return

    new_hash = hashlib.md5(latest.encode("utf-8")).hexdigest()
    print("🔹 새로운 해시:", new_hash)

    # 변경 감지
    if new_hash != last_hash:
        print("🔸 포지션 변경 감지!")
        send_telegram(f"🔔 코덕후 새 포지션 발생!\n\n{latest}\n\n👉 {URL}")
        # 해시 저장
        with open(HASH_FILE, "w") as f:
            f.write(new_hash)
    else:
        print("✅ 변경 없음.")

if __name__ == "__main__":
    main()
