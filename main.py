import os
import asyncio
from pyrogram import Client, filters, errors
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
settings = db["bot_settings"]

app = Client("LoserForwarder", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- MIDDLEWARE: Check Premium ---
async def is_premium(user_id):
    if user_id == OWNER_ID: return True
    user = await users.find_one({"user_id": user_id})
    if user and user["expiry"] > datetime.now():
        return True
    return False

# --- COMMANDS ---

@app.on_message(filters.command("start"))
async def start(client, message):
    text = (
        "🌟 **Welcome to Loser Premium Forwarder**\n\n"
        "🚀 **User Commands:**\n"
        "🔹 /start - Check if bot is alive\n"
        "🔹 /id - Get your Telegram ID\n"
        "🔹 /live - Start Live Forwarding (New Posts)\n"
        "🔹 /batch - Forward Old Posts (Range)\n"
        "🔹 /stop - Stop any active process\n"
        "🔹 /cancel - Cancel current setup\n\n"
        "💎 *Status: Premium Activated*" if await is_premium(message.from_user.id) else "❌ *Status: No Access*"
    )
    await message.reply_text(text)

@app.on_message(filters.command("id"))
async def get_id(client, message):
    await message.reply_text(f"Your ID: `{message.from_user.id}`\nChat ID: `{message.chat.id}`")

# --- OWNER COMMANDS ---

@app.on_message(filters.command("add") & filters.user(OWNER_ID))
async def add_user(client, message):
    try:
        args = message.text.split()
        target_id, days = int(args[1]), int(args[2])
        expiry = datetime.now() + timedelta(days=days)
        await users.update_one({"user_id": target_id}, {"$set": {"expiry": expiry}}, upsert=True)
        await message.reply_text(f"✅ User `{target_id}` added for {days} days.")
        if LOG_CHANNEL:
            await client.send_message(LOG_CHANNEL, f"👤 New Premium User: `{target_id}` for {days} days.")
    except:
        await message.reply_text("Usage: `/add 123456 30` (ID then Days)")

@app.on_message(filters.command("remove") & filters.user(OWNER_ID))
async def remove_user(client, message):
    try:
        target_id = int(message.text.split()[1])
        await users.delete_one({"user_id": target_id})
        await message.reply_text("❌ User Access Removed.")
    except:
        await message.reply_text("Usage: `/remove 123456` ")

# --- FORWARDING LOGIC (With Auto Caption) ---

@app.on_message((filters.video | filters.document) & ~filters.forwarded)
async def handle_forward(client, message):
    if not await is_premium(message.from_user.id): return
    
    # Auto Caption: Loser Name Addition
    original_caption = message.caption or ""
    new_caption = f"{original_caption}\n\n🎬 **Forwarded By: Loser**"
    
    # Logic to find destination from DB (assuming linked via /live setup)
    # This part needs your /live linking logic to be active
    pass

@app.on_message(filters.command("batch") & filters.private)
async def batch_forward(client, message):
    if not await is_premium(message.from_user.id):
        return await message.reply_text("❌ Buy Premium to use Batch.")
    await message.reply_text("Send me the **Starting Message Link** of the channel.")

# --- BROADCAST ---
@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast(client, message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a message to broadcast.")
    
    all_users = users.find({})
    count = 0
    async for u in all_users:
        try:
            await message.reply_to_message.copy(u["user_id"])
            count += 1
        except: pass
    await message.reply_text(f"✅ Broadcast Done to {count} users.")

# --- THE CRITICAL FIX FOR RUNTIME ERROR ---
async def start_bot():
    await app.start()
    print("🚀 LOSER FORWARDER IS ONLINE!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())
    
