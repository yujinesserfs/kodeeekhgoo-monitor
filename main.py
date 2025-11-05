import os
import time
import hashlib
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

URL = "https://wonyoddi.com/ccts/deog.ku"
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def fetch_latest_position():
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(URL)
        time.sleep(5)  # JS 렌더링 대기

        html = driver.page_source
        driver.quit()

        soup = BeautifulSoup(html, "html.parser")
        target = None
        for p in soup.find_all("p"):
            if "최근 7일간 포지션" in p.get_text():
                target = p
                break

        if not target:
            print("⚠️ '최근 7일간 포지션' 문구를 찾지 못했습니다.")
            print("📄 페이지 일부 미리보기:", soup.get_text()[:300])
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
        print(f"❌ Selenium 에러: {e}")
        return None

def send_telegram(msg):
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
    last_hash = os.getenv("LAST_HASH", "")
    print("🔹 이전 해시:", repr(last_hash))

    latest = fetch_latest_position()
    if not latest:
        return

    current_hash = hashlib.md5(latest.encode("utf-8")).hexdigest()
    print("🔹 현재 해시:", current_hash)

    if last_hash != current_hash:
        print("🔸 포지션 변경 감지!")
        send_telegram(f"🔔 코덕후 새 포지션!\n\n{latest}\n\n👉 {URL}")
    else:
        print("✅ 변경 없음.")

    # GitHub Actions용 artifact 업로드 시 사용
    os.makedirs("artifact", exist_ok=True)
    with open("artifact/last-hash.txt", "w") as f:
        f.write(current_hash)
    print(f"🔹 새로운 LAST_HASH 기록: {current_hash}")

if __name__ == "__main__":
    main()
