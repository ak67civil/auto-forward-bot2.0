import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

# --- CONFIGS ---
API_ID = int(os.environ.get("API_ID", "33401543"))
API_HASH = os.environ.get("API_HASH", "7cdea5bbc8bd991b4a49807ce86")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MONGO_DB_URI = os.environ.get("MONGO_DB_URI")
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0"))
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

# Database Setup
db_client = AsyncIOMotorClient(MONGO_DB_URI)
db = db_client["ForwardProDB"]
users = db["premium_users"]

app = Client("LoserForwarder", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- PREMIUM CHECK ---
async def is_premium(user_id):
    if user_id == OWNER_ID: return True
    user = await users.find_one({"user_id": user_id})
    if user and user["expiry"] > datetime.now():
        return True
    return False

# --- USER COMMANDS ---
@app.on_message(filters.command("start"))
async def start(client, message):
    text = (
        "🛡️ **Welcome to Loser Premium Forwarder**\n\n"
        "📖 **Commands List:**\n"
        "🔹 /start - Bot status check\n"
        "🔹 /id - Apna ID check karein\n"
        "🔹 /live - Live forward setup\n"
        "🔹 /batch - Purane posts forward karein\n"
        "🔹 /stop - Process rokne ke liye\n"
        "🔹 /cancel - Setup hatane ke liye\n\n"
        "💎 **Premium:** " + ("Activated ✅" if await is_premium(message.from_user.id) else "Not Found ❌")
    )
    await message.reply_text(text)

@app.on_message(filters.command("id"))
async def get_id(client, message):
    await message.reply_text(f"👤 **Your ID:** `{message.from_user.id}`\n👥 **Chat ID:** `{message.chat.id}`")

# --- OWNER COMMANDS ---
@app.on_message(filters.command("add") & filters.user(OWNER_ID))
async def add_premium(client, message):
    try:
        args = message.text.split()
        u_id, days = int(args[1]), int(args[2])
        expiry = datetime.now() + timedelta(days=days)
        await users.update_one({"user_id": u_id}, {"$set": {"expiry": expiry}}, upsert=True)
        await message.reply_text(f"✅ User `{u_id}` added for {days} days.")
    except:
        await message.reply_text("Usage: `/add [ID] [Days]`")

@app.on_message(filters.command("remove") & filters.user(OWNER_ID))
async def remove_premium(client, message):
    try:
        u_id = int(message.text.split()[1])
        await users.delete_one({"user_id": u_id})
        await message.reply_text(f"❌ User `{u_id}` removed.")
    except:
        await message.reply_text("Usage: `/remove [ID]`")

@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast(client, message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a message to broadcast!")
    await message.reply_text("🚀 Broadcasting...")

# --- FORWARDING + AUTO CAPTION ---
@app.on_message((filters.video | filters.document) & ~filters.forwarded)
async def auto_forward(client, message):
    if not await is_premium(message.from_user.id): return
    caption = message.caption or ""
    new_caption = f"{caption}\n\n🎬 **Forwarded By: Loser**"
    # Destination logic for /live goes here
    pass

# --- THE CRITICAL FIX ---
async def start_bot():
    await app.start()
    print("🚀 BOT IS ONLINE!")
    await asyncio.Future()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())
        
