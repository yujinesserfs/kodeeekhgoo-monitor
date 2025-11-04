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

        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        # "최근 7일간 포지션" 첫 행 추출
        target = next((p for p in soup.find_all("p") if "최근 7일간 포지션" in p.get_text()), None)
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
        return " | ".join(cells)

    except Exception as e:
        print("❌ Selenium 에러:", e)
        return None

def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ TELEGRAM_BOT_TOKEN 또는 CHAT_ID 환경변수가 없습니다.")
        return

    payload = {"chat_id": CHAT_ID, "text": msg}
    try:
        r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data=payload, timeout=10)
        if r.status_code == 200:
            print("📩 텔레그램 전송 완료")
        else:
            print("⚠️ 텔레그램 전송 실패:", r.text)
    except Exception as e:
        print("❌ 텔레그램 오류:", e)

def main():
    last_hash = os.getenv("LAST_HASH", "")
    latest = fetch_latest_position()
    if not latest:
        return

    new_hash = hashlib.md5(latest.encode("utf-8")).hexdigest()

    if new_hash != last_hash:
        print("🔸 포지션 변경 감지됨!")
        send_telegram(f"🔔 코덕후 새 포지션 발생!\n\n{latest}\n\n👉 {URL}")
    else:
        print("✅ 변경 없음.")

    # GitHub Actions 환경에 다음 단계에서 사용할 LAST_HASH 기록
    with open(os.environ['GITHUB_ENV'], 'a') as f:
        f.write(f"LAST_HASH={new_hash}\n")
    print(f"🔹 새로운 LAST_HASH 기록: {new_hash}")

if __name__ == "__main__":
    main()
