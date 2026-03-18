import os
import asyncio
from pyrogram import Client, filters

# Configs - Heroku Config Vars
API_ID = int(os.environ.get("API_ID", "33401543"))
API_HASH = os.environ.get("API_HASH", "7cdea5bbc8bd991b4a49807ce86")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("LoserBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("✅ Bhai! Bot ab Bilkul ON hai aur kaam kar raha hai!")

@app.on_message(filters.command("id"))
async def get_id(client, message):
    await message.reply_text(f"👤 Your ID: `{message.from_user.id}`")

async def main():
    async with app:
        print("🚀 BOT IS RUNNING!")
        await asyncio.Future()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
    
