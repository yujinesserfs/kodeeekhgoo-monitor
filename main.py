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

# 두 명의 Chat ID
CHAT_ID_1 = os.getenv("TELEGRAM_CHAT_ID_1")
CHAT_ID_2 = os.getenv("TELEGRAM_CHAT_ID_2")

print("🔍 Loaded IDs:", CHAT_ID_1, CHAT_ID_2)

def load_last_hash():
    path = "last_hash.txt"
    if os.path.exists(path):
        return open(path).read().strip()
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

    except Exception as e:
        print("❌ fetch_latest_position 에러:", e)
        return None


def send_telegram(msg):
    if not BOT_TOKEN:
        print("⚠️ BOT_TOKEN 없음")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    # 두 명에게 각각 보내기
    for cid in [CHAT_ID_1, CHAT_ID_2]:
        if not cid:
            continue
        try:
            requests.post(url, data={"chat_id": cid, "text": msg})
            print(f"📨 전송 완료 → Chat ID: {cid}")
        except Exception as e:
            print(f"❌ 전송 실패 → {cid}:", e)


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
