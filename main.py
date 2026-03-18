import os
from pyrogram import Client, filters

# Heroku Config Vars se uthayega
API_ID = int(os.environ.get("API_ID", "33401543"))
API_HASH = os.environ.get("API_HASH", "7cdea5bbc8bd991b4a49807ce86")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("LoserBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("💪 Dekh Bhai! Bot ab Bilkul ON hai!")

@app.on_message(filters.command("id"))
async def get_id(client, message):
    await message.reply_text(f"👤 Your ID: `{message.from_user.id}`")

# Simple execution
if __name__ == "__main__":
    print("🚀 BOT STARTING...")
    app.run()
    
