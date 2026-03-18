import os
import asyncio
from pyrogram import Client, filters, errors
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

# --- CONFIGS ---
API_ID = int(os.environ.get("API_ID", "33401543"))
API_HASH = os.environ.get("API_HASH", "7cdea5bbc8bd991b4a49807ce86")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MONGO_DB_URI = os.environ.get("MONGO_DB_URI")
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0"))
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

db_client = AsyncIOMotorClient(MONGO_DB_URI)
db = db_client["ForwardProDB"]
users = db["premium_users"]

app = Client("LoserForwarder", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- PREMIUM CHECK ---
async def is_premium(user_id):
    if user_id == OWNER_ID: return True
    user = await users.find_one({"user_id": user_id})
    return user and user["expiry"] > datetime.now()

# --- COMMANDS ---
@app.on_message(filters.command("start"))
async def start(client, message):
    text = (
        "🛡️ **Loser Premium Forwarder v4.0**\n\n"
        "🚀 **Commands:**\n"
        "🔹 /start - Check Bot Status\n"
        "🔹 /id - Get Your Telegram ID\n"
        "🔹 /live - Setup Live Forwarding\n"
        "🔹 /batch - Start Old Posts Forwarding\n"
        "🔹 /stop - Stop Process\n"
        "🔹 /cancel - Cancel Setup\n\n"
        "💎 **Status:** " + ("Premium Activated ✅" if await is_premium(message.from_user.id) else "No Access ❌")
    )
    await message.reply_text(text)

@app.on_message(filters.command("id"))
async def get_id(client, message):
    await message.reply_text(f"👤 **ID:** `{message.from_user.id}`\n👥 **Chat ID:** `{message.chat.id}`")

@app.on_message(filters.command("add") & filters.user(OWNER_ID))
async def add_user(client, message):
    try:
        args = message.text.split()
        u_id, days = int(args[1]), int(args[2])
        expiry = datetime.now() + timedelta(days=days)
        await users.update_one({"user_id": u_id}, {"$set": {"expiry": expiry}}, upsert=True)
        await message.reply_text(f"✅ User `{u_id}` added for {days} days.")
    except:
        await message.reply_text("Usage: `/add [ID] [Days]`")

# --- AUTO CAPTION (Loser Branding) ---
@app.on_message((filters.video | filters.document) & ~filters.forwarded)
async def auto_caption(client, message):
    if not await is_premium(message.from_user.id): return
    caption = message.caption or ""
    # Branding add karna
    new_caption = f"{caption}\n\n🎬 **Forwarded By: Loser**"
    # Forwarding logic yahan aayegi jab aap /live setup karoge
    pass

# --- THE REAL FIX FOR NO RESPONSE ---
async def start_bot():
    try:
        await app.start()
        print("🚀 BOT IS ONLINE AND RESPONDING!")
        if LOG_CHANNEL:
            await app.send_message(LOG_CHANNEL, "🚀 **Bot Started Successfully!**")
        await asyncio.Event().wait() # Yeh line bot ko silent crash se bachayegi
    except errors.FloodWait as e:
        await asyncio.sleep(e.value)
        await start_bot()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())
