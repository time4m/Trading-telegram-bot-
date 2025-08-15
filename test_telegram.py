import aiohttp
import asyncio

BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

async def send_test():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": "✅ Test message from bot", "parse_mode": "Markdown"}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload) as resp:
            print(await resp.text())

asyncio.run(send_test())
