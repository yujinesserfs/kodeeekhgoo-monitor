import os
import requests

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID_1 = os.getenv("TELEGRAM_CHAT_ID_1")
CHAT_ID_2 = os.getenv("TELEGRAM_CHAT_ID_2")

CHAT_IDS = [cid for cid in [CHAT_ID_1, CHAT_ID_2] if cid]

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
    test_message = "🔔 테스트 메시지입니다! 봇이 정상 작동하는지 확인합니다."
    for cid in CHAT_IDS:
        send_telegram(cid, test_message)

if __name__ == "__main__":
    print("테스트용 Telegram 메시지 전송 시작")
    main()
