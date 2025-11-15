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
CHAT_ID_1 = os.getenv("TELEGRAM_CHAT_ID_1")
CHAT_ID_2 = os.getenv("TELEGRAM_CHAT_ID_2")

CHAT_IDS = [cid for cid in [CHAT_ID_1, CHAT_ID_2] if cid]

print("🔍 Loaded CHAT IDs:", CHAT_IDS)

def load_last_hash():
    if os.path.exists("last_hash.txt"):
        return open("last_hash.txt").read().strip()
    return ""

def save_last_hash(h):
    with open("last_hash.txt", "w") as f:
        f.write(h)

def fetch_latest_position():
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
            print("❌ 포지션 테이블 없음")
            return None

        table = target.find_next("table")
        if not table:
            print("❌ 테이블 없음")
            return None

        first_row = table.select_one("tbody tr") or table.select_one("tr:nth-of-type(2)")
        if not first_row:
            print("❌ 첫 번째 행 없음")
            return None

        cells = [td.get_text(strip=True) for td in first_row.find_all("td")]

        # 시간 UTC -> KST 변환
        try:
            raw_time = cells[4]
            dt_obj = datetime.strptime(raw_time, "%Y-%m-%d %H:%M:%S")
            dt_kst = dt_obj + timedelta(hours=9)
            cells[4] = dt_kst.strftime("%Y-%m-%d %H:%M:%S KST")
        except Exception as e:
            print("⚠️ 시간 변환 실패:", e)

        return " | ".join(cells)

    except Exception as e:
        print("❌ fetch_latest_position 에러:", e)
        return None

def send_telegram(chat_id, msg):
    if not BOT_TOKEN:
        print("⚠️ BOT_TOKEN 없음 → 전송 스킵")
        return
    if not chat_id:
        print("⚠️ CHAT_ID 없음 → 전송 스킵")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        res = requests.post(url, data={"chat_id": chat_id, "text": msg})
        print(f"📨 전송 → {chat_id} / status {res.status_code} / response: {res.text}")
    except Exception as e:
        print(f"❌ 전송 실패 → {chat_id}:", e)

def main():
    last_hash = load_last_hash()
    latest = fetch_latest_position()
    if not latest:
        print("❌ 포지션 없음 또는 파싱 실패")
        return

    current_hash = hashlib.md5(latest.encode()).hexdigest()

    if last_hash != current_hash:
        print("🔸 포지션 변경 감지! 텔레그램 전송")
        message = f"🔔 코덕후 새 포지션 발생!\n\n{latest}\n\n👉 {URL}"

        for cid in CHAT_IDS:
            send_telegram(cid, message)

        save_last_hash(current_hash)
    else:
        print("✅ 변경 없음")

if __name__ == "__main__":
    main()
