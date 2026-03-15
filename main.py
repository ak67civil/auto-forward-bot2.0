import asyncio
from pyrogram import Client, filters
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

# Bot Setup
app = Client("forwarder_bot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)

# MongoDB Setup with Error Handling
try:
    # Agar Heroku mein MONGO_DB_URI nahi hai, toh ye crash nahi karega
    MONGO_URL = getattr(Config, "MONGO_DB_URI", None) or getattr(Config, "MONGO_URL", None)
    if MONGO_URL:
        db_client = AsyncIOMotorClient(MONGO_URL)
        db = db_client["forwarder_bot"]
        users_db = db["users"]
        stats_db = db["stats"]
    else:
        db_client = None
except:
    db_client = None

LOG_CHANNEL = Config.LOG_CHANNEL
user_data = {}
live_settings = {"active": False, "source": None, "dest": None}

# --- Database Helpers ---
async def update_stats(count=1):
    if db_client:
        await stats_db.update_one({"id": "total_files"}, {"$inc": {"count": count}}, upsert=True)

async def get_total_files():
    if db_client:
        data = await stats_db.find_one({"id": "total_files"})
        return data["count"] if data else 0
    return "N/A (No DB)"

# --- Commands ---

@app.on_message(filters.command("start") & filters.user(Config.OWNER_ID))
async def start_cmd(client, message):
    menu = (
        "✨ **Forwarder Pro Dashboard** ✨\n\n"
        "🚀 `/batch` - Start Batch Forwarding\n"
        "📡 `/live` - Start Live Forwarding (Source Dest)\n"
        "📴 `/stop_live` - Stop Live Mode\n"
        "📊 `/stats` - Check Total Forwards\n"
        "👥 `/users` - Check Total Users\n"
        "❌ `/cancel` - Stop current batch\n\n"
        "🎯 **ID Check:** Forward any message here."
    )
    await message.reply_text(menu)

@app.on_message(filters.forwarded & filters.user(Config.OWNER_ID))
async def get_id_info(client, message):
    if message.forward_from_chat:
        await message.reply_text(f"🎯 **Data:**\nID: `{message.forward_from_chat.id}`\nMsg ID: `{message.forward_from_message_id}`")

@app.on_message(filters.command("live") & filters.user(Config.OWNER_ID))
async def setup_live(client, message):
    args = message.text.split(" ")
    if len(args) < 3: return await message.reply_text("❌ `/live [SourceID] [DestID]`")
    live_settings.update({"source": int(args[1]), "dest": int(args[2]), "active": True})
    await message.reply_text(f"📡 **Live Mode ON!**")

@app.on_message(filters.command("stop_live") & filters.user(Config.OWNER_ID))
async def stop_live(client, message):
    live_settings["active"] = False
    await message.reply_text("📴 Live Mode OFF.")

@app.on_message((filters.video | filters.document))
async def handle_live(client, message):
    if live_settings["active"] and message.chat.id == live_settings["source"]:
        f_id = message.video.file_id if message.video else message.document.file_id
        await client.send_video(chat_id=live_settings["dest"], video=f_id, caption=message.caption or "")
        if LOG_CHANNEL: await client.send_video(chat_id=LOG_CHANNEL, video=f_id, caption="📡 Live Log")
        await update_stats(1)

@app.on_message(filters.command("batch") & filters.user(Config.OWNER_ID))
async def start_batch(client, message):
    user_data[message.from_user.id] = {"step": 1}
    await message.reply_text("📥 **Step 1:** Source & Dest ID bhejo (Space dekar).")

@app.on_message(filters.user(Config.OWNER_ID) & filters.text & ~filters.command(["start", "batch", "live", "stats", "users", "stop_live", "cancel"]))
async def handle_batch_steps(client, message):
    user_id = message.from_user.id
    if user_id not in user_data: return
    step = user_data[user_id]["step"]

    if step == 1:
        try:
            ids = message.text.split(" ")
            user_data[user_id].update({"source": int(ids[0]), "dest": int(ids[1]), "step": 2})
            await message.reply_text("🔢 **Step 2:** Range bhejo (Start End).")
        except: await message.reply_text("❌ Galat IDs!")
    elif step == 2:
        try:
            r = message.text.split(" ")
            start, end, source, dest = int(r[0]), int(r[1]), user_data[user_id]["source"], user_data[user_id]["dest"]
            del user_data[user_id]
            status = await message.reply_text("🏎️ Turbo Forwarding...")
            count = 0
            for m_id in range(start, end + 1):
                try:
                    msg = await client.get_messages(source, m_id)
                    if msg and (msg.video or msg.document):
                        f_id = msg.video.file_id if msg.video else msg.document.file_id
                        await client.send_video(chat_id=dest, video=f_id, caption=msg.caption or "")
                        if LOG_CHANNEL: await client.send_video(chat_id=LOG_CHANNEL, video=f_id, caption=f"📂 Log: `{m_id}`")
                        count += 1
                        await update_stats(1)
                        if count % 10 == 0: await status.edit(f"🚀 `{count}` processed...")
                        await asyncio.sleep(1.5)
                except: continue
            await status.edit(f"🏁 Done! Total: `{count}`. Target channel mein 'Done ✅' bhej diya.")
            await client.send_message(dest, "Done ✅")
        except: await message.reply_text("❌ Range error!")

@app.on_message(filters.command("stats") & filters.user(Config.OWNER_ID))
async def show_stats(client, message):
    total = await get_total_files()
    await message.reply_text(f"📊 **Total Forwarded:** `{total}`")

app.run()
