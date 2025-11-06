import os
import time
import hashlib
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

URL = "https://wonyoddi.com/ccts/deog.ku"
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def load_last_hash():
    """리포지토리 파일에서 이전 해시 불러오기"""
    path = "last_hash.txt"
    if os.path.exists(path):
        return open(path).read().strip()
    return ""


def save_last_hash(h):
    """해시를 파일에 저장"""
    with open("last_hash.txt", "w") as f:
        f.write(h)


def fetch_latest_position():
    """셀레니움으로 최근 포지션 테이블 1행 추출"""
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(URL)
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        target = None
        for p in soup.find_all("p"):
            if "최근 7일간 포지션" in p.get_text():
                target = p
                break
        if not target:
            return None

        table = target.find_next("table")
        if not table:
            return None

        first_row = table.select_one("tbody tr") or table.select_one("tr:nth-of-type(2)")
        if not first_row:
            return None

        cells = [td.get_text(strip=True) for td in first_row.find_all("td")]

        # 시간 KST 변환
        try:
            raw_time = cells[4]
            dt_obj = datetime.strptime(raw_time, "%Y-%m-%d %H:%M:%S")
            dt_kst = dt_obj + timedelta(hours=9)
            cells[4] = dt_kst.strftime("%Y-%m-%d %H:%M:%S KST")
        except:
            pass

        return " | ".join(cells)

    except Exception:
        return None


def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ 텔레그램 설정 없음")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


def main():
    last_hash = load_last_hash()
    latest = fetch_latest_position()
    if not latest:
        print("포지션 없음 또는 파싱 실패")
        return

    current_hash = hashlib.md5(latest.encode()).hexdigest()

    if last_hash != current_hash:
        print("🔸 포지션 변경 감지! 텔레그램 전송")
        send_telegram(f"🔔 코덕후 새 포지션 발생!\n\n{latest}\n\n👉 {URL}")
        save_last_hash(current_hash)
    else:
        print("✅ 변경 없음")


if __name__ == "__main__":
    main()
