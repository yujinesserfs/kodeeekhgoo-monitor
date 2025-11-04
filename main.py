import requests
from bs4 import BeautifulSoup
import hashlib
import os

URL = "https://wonyoddi.com/ccts/deog.ku"
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def fetch_latest_position():
    """페이지에서 첫 번째 테이블의 첫 행 추출"""
    try:
        r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"❌ 요청 실패: {e}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    # 페이지 내 첫 번째 테이블 찾기
    table = soup.find("table")
    if not table:
        print("⚠️ 테이블을 찾지 못했습니다.")
        print("📄 페이지 일부 미리보기:", soup.get_text()[:400])
        return None

    # 첫 번째 행 추출
    first_row = table.select_one("tbody tr") or table.select_one("tr:nth-of-type(2)")
    if not first_row:
        print("⚠️ 테이블 안에 데이터가 없습니다.")
        return None

    # 각 셀의 텍스트를 합쳐서 하나의 문자열로
    cells = [td.get_text(strip=True) for td in first_row.find_all("td")]
    position_text = " | ".join(cells)
    print(f"✅ 최신 포지션: {position_text}")
    return position_text


def send_telegram(msg: str):
    """텔레그램으로 메시지 전송"""
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ TELEGRAM_BOT_TOKEN 또는 CHAT_ID 환경변수가 없습니다.")
        return

    tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg}
    try:
        r = requests.post(tg_url, data=payload, timeout=10)
        if r.status_code != 200:
            print("⚠️ 텔레그램 전송 실패:", r.text)
        else:
            print("📩 텔레그램 전송 완료")
    except Exception as e:
        print("❌ 텔레그램 오류:", e)


def main():
    print("🔹 Fetching last_hash from environment or store")
    last_hash = os.getenv("LAST_HASH", "")

    print("🔹 Fetching latest position from webpage...")
    latest = fetch_latest_position()
    if not latest:
        return

    # 해시값 생성
    new_hash = hashlib.md5(latest.encode("utf-8")).hexdigest()

    if new_hash != last_hash:
        print("🔸 포지션 변경 감지됨!")
        send_telegram(f"🔔 코덕후 새 포지션 발생!\n\n{latest}\n\n👉 {URL}")
    else:
        print("✅ 변경 없음.")

    # GitHub Actions용 출력 (다음 실행에서 이어받기 위함)
    print(f"::set-output name=LAST_HASH::{new_hash}")


if __name__ == "__main__":
    main()
