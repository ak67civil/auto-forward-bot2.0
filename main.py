import asyncio
from pyrogram import Client, filters
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

# Bot Setup
app = Client(
    "forwarder_bot", 
    api_id=Config.API_ID, 
    api_hash=Config.API_HASH, 
    bot_token=Config.BOT_TOKEN
)

# MongoDB Setup
db_client = AsyncIOMotorClient(Config.MONGO_DB_URI)
db = db_client["forwarder_bot"]
users_db = db["users"]
stats_db = db["stats"]

# Variables
LOG_CHANNEL = Config.LOG_CHANNEL
user_data = {}
live_settings = {"active": False, "source": None, "dest": None}

# --- Database Helpers ---
async def add_user(user_id):
    await users_db.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)

async def update_stats(count=1):
    await stats_db.update_one({"id": "total_files"}, {"$inc": {"count": count}}, upsert=True)

async def get_total_files():
    data = await stats_db.find_one({"id": "total_files"})
    return data["count"] if data else 0

# --- Commands ---

@app.on_message(filters.command("start") & filters.user(Config.OWNER_ID))
async def start_cmd(client, message):
    await add_user(message.from_user.id)
    menu = (
        "🛠 **Forwarder Pro Dashboard**\n\n"
        "🚀 `/batch` - Purani videos forward karein (Range)\n"
        "📡 `/live` - Nayi videos turant forward karein\n"
        "📊 `/stats` - Abhi tak total kitni files gayi\n"
        "👥 `/users` - Kitne log bot use kar rahe hain\n"
        "🎯 **ID Check:** Koi bhi message forward karo ID mil jayegi\n"
        "❌ `/cancel` - Chalte kaam ko rokne ke liye\n"
        "📴 `/stop_live` - Live forwarding band karne ke liye"
    )
    await message.reply_text(menu)

# 1. ID Checker (Wapas Add Kar Diya)
@app.on_message(filters.forwarded & filters.user(Config.OWNER_ID))
async def get_id_info(client, message):
    if message.forward_from_chat:
        c_id = message.forward_from_chat.id
        m_id = message.forward_from_message_id
        await message.reply_text(f"🎯 **Data Mil Gaya!**\n\nChannel ID: `{c_id}`\nMessage ID: `{m_id}`")

# 2. Live Forwarding Setup
@app.on_message(filters.command("live") & filters.user(Config.OWNER_ID))
async def setup_live(client, message):
    args = message.text.split(" ")
    if len(args) < 3:
        return await message.reply_text("❌ **Format:** `/live [SourceID] [DestID]`")
    
    live_settings["source"] = int(args[1])
    live_settings["dest"] = int(args[2])
    live_settings["active"] = True
    await message.reply_text(f"📡 **Live Mode ON!**\nSource: `{live_settings['source']}`\nTarget: `{live_settings['dest']}`")

@app.on_message(filters.command("stop_live") & filters.user(Config.OWNER_ID))
async def stop_live(client, message):
    live_settings["active"] = False
    await message.reply_text("📴 Live Forwarding band kar di gayi hai.")

# 3. Live Logic (Nayi video aate hi forward)
@app.on_message((filters.video | filters.document))
async def handle_live(client, message):
    if live_settings["active"] and message.chat.id == live_settings["source"]:
        file_id = message.video.file_id if message.video else message.document.file_id
        cap = message.caption or ""
        
        # Target mein bhejo
        await client.send_video(chat_id=live_settings["dest"], video=file_id, caption=cap)
        # Log mein copy bhejo
        if LOG_CHANNEL:
            await client.send_video(chat_id=LOG_CHANNEL, video=file_id, caption=f"📡 **Live Log**\n{cap}")
        
        await update_stats(1)

# 4. Batch Forwarding (Turbo Speed)
@app.on_message(filters.command("batch") & filters.user(Config.OWNER_ID))
async def start_batch(client, message):
    user_data[message.from_user.id] = {"step": 1}
    await message.reply_text("📥 **Step 1:**\nSource aur Dest ID bhejo (Space dekar):\n`-100123 -100456` ")

@app.on_message(filters.user(Config.OWNER_ID) & filters.text & ~filters.command(["start", "batch", "live", "stats", "users", "stop_live", "cancel"]))
async def handle_batch_steps(client, message):
    user_id = message.from_user.id
    if user_id not in user_data: return
    
    step = user_data[user_id]["step"]

    if step == 1:
        try:
            ids = message.text.split(" ")
            user_data[user_id]["source"], user_data[user_id]["dest"] = int(ids[0]), int(ids[1])
            user_data[user_id]["step"] = 2
            await message.reply_text("🔢 **Step 2:**\nRange bhejo (Start End):\n`200 500` ")
        except: await message.reply_text("❌ IDs sahi se dalo!")

    elif step == 2:
        try:
            r = message.text.split(" ")
            start, end = int(r[0]), int(r[1])
            source, dest = user_data[user_id]["source"], user_data[user_id]["dest"]
            del user_data[user_id]

            status = await message.reply_text("🏎️ **Turbo Batch Started...**")
            count = 0

            for m_id in range(start, end + 1):
                try:
                    msg = await client.get_messages(source, m_id)
                    if msg and (msg.video or msg.document):
                        f_id = msg.video.file_id if msg.video else msg.document.file_id
                        # Dest mein bhej
                        await client.send_video(chat_id=dest, video=f_id, caption=msg.caption or "")
                        # Log mein bhej
                        if LOG_CHANNEL:
                            await client.send_video(chat_id=LOG_CHANNEL, video=f_id, caption=f"📂 Log: `{m_id}`")
                        
                        count += 1
                        await update_stats(1)
                        if count % 10 == 0:
                            await status.edit(f"🚀 `{count}` items processed...")
                        await asyncio.sleep(1.5) # Fast but safe
                except: continue
            
            await client.send_message(chat_id=dest, text="Done ✅")
            await status.edit(f"🏁 **Batch Complete!** Total: `{count}`")
        except: await message.reply_text("❌ Range galat hai!")

# 5. Stats & Users
@app.on_message(filters.command("stats") & filters.user(Config.OWNER_ID))
async def show_stats(client, message):
    total = await get_total_files()
    await message.reply_text(f"📊 **Total Forwarded Files:** `{total}`")

@app.on_message(filters.command("users") & filters.user(Config.OWNER_ID))
async def show_users(client, message):
    count = await users_db.count_documents({})
    await message.reply_text(f"👥 **Bot Users:** `{count}`")

@app.on_message(filters.command("cancel") & filters.user(Config.OWNER_ID))
async def cancel(client, message):
    user_data.pop(message.from_user.id, None)
    await message.reply_text("❌ Kaam rok diya gaya hai.")

app.run()
            
