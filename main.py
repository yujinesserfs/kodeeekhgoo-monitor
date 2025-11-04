import requests
from bs4 import BeautifulSoup
import hashlib
import os

# 모니터링할 URL
URL = "https://wonyoddi.com/ccts/deog.ku"

# 텔레그램 환경변수
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def fetch_latest_position():
    """페이지에서 최근 7일간 포지션의 첫 행을 추출"""
    try:
        r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"❌ 요청 실패: {e}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    # '최근 7일간 포지션' 문구 포함된 태그 찾기 (p, div, span, h2 등 모두 탐색)
    target = None
    for tag in soup.find_all(["p", "div", "span", "h2", "h3"]):
        text = tag.get_text(strip=True)
        if "최근" in text and "포지션" in text:
            target = tag
            break

    if not target:
        print("⚠️ '최근 7일간 포지션' 문구를 찾지 못했습니다.")
        print("📄 페이지 일부 미리보기:", soup.get_text()[:500])
        return None

    # 해당 문구 다음의 테이블 찾기
    table = target.find_next("table")
    if not table:
        print("⚠️ 포지션 테이블을 찾지 못했습니다.")
        return None

    # 첫 번째 데이터 행 추출
    first_row = table.select_one("tbody tr") or table.select_one("tr:nth-of-type(2)")
    if not first_row:
        print("⚠️ 테이블 안에 데이터가 없습니다.")
        return None

    # 각 셀의 텍스트 합치기
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

    # 해시를 다음 실행에 전달하기 위해 출력 (GitHub Actions용)
    print(f"::set-output name=LAST_HASH::{new_hash}")


if __name__ == "__main__":
    main()
