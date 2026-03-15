import asyncio
from pyrogram import Client, filters
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

app = Client("forwarder_bot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)

# MongoDB Handle
try:
    MONGO_URL = getattr(Config, "MONGO_DB_URI", None) or getattr(Config, "MONGO_URL", None)
    db_client = AsyncIOMotorClient(MONGO_URL) if MONGO_URL else None
    if db_client:
        stats_db = db_client["forwarder_bot"]["stats"]
except: db_client = None

LOG_CHANNEL = Config.LOG_CHANNEL
live_settings = {"active": False, "source": None, "dest": None}
user_data = {}

async def update_stats():
    if db_client: await stats_db.update_one({"id": "total_files"}, {"$inc": {"count": 1}}, upsert=True)

@app.on_message(filters.command("start") & filters.user(Config.OWNER_ID))
async def start_cmd(client, message):
    await message.reply_text("✨ **Bot Fixed!** Ab loop nahi banega.\nCommands: `/batch`, `/live`, `/stats`, `/stop_live` ")

@app.on_message(filters.command("live") & filters.user(Config.OWNER_ID))
async def setup_live(client, message):
    args = message.text.split(" ")
    if len(args) < 3: return await message.reply_text("❌ `/live [SourceID] [DestID]`")
    live_settings.update({"source": int(args[1]), "dest": int(args[2]), "active": True})
    await message.reply_text(f"📡 **Live Mode ON!**\nLoop protection enabled.")

@app.on_message(filters.command("stop_live") & filters.user(Config.OWNER_ID))
async def stop_live(client, message):
    live_settings["active"] = False
    await message.reply_text("📴 Live Mode OFF.")

# --- FIXED LIVE LOGIC (Loop Protection) ---
@app.on_message((filters.video | filters.document))
async def handle_live(client, message):
    # Sirf tabhi kaam karega jab message SOURCE channel se aaye
    if live_settings["active"] and message.chat.id == live_settings["source"]:
        # Agar ye video bot ne khud bheji hai (Target ya Log mein), toh ignore karega
        if message.chat.id == live_settings["dest"] or message.chat.id == LOG_CHANNEL:
            return

        f_id = message.video.file_id if message.video else message.document.file_id
        cap = message.caption or ""
        
        try:
            # Target mein send
            await client.send_video(chat_id=live_settings["dest"], video=f_id, caption=cap)
            # Log mein send
            if LOG_CHANNEL and LOG_CHANNEL != live_settings["source"]:
                await client.send_video(chat_id=LOG_CHANNEL, video=f_id, caption=f"📡 **Live Log**")
            await update_stats()
        except Exception as e: print(f"Live Error: {e}")

# Batch Logic (Turbo)
@app.on_message(filters.command("batch") & filters.user(Config.OWNER_ID))
async def start_batch(client, message):
    user_data[message.from_user.id] = {"step": 1}
    await message.reply_text("📥 **Step 1:** Source & Dest ID bhejo.")

@app.on_message(filters.user(Config.OWNER_ID) & filters.text & ~filters.command(["start", "batch", "live", "stats", "stop_live"]))
async def handle_batch_steps(client, message):
    user_id = message.from_user.id
    if user_id not in user_data: return
    step = user_data[user_id]["step"]

    if step == 1:
        ids = message.text.split(" ")
        user_data[user_id].update({"source": int(ids[0]), "dest": int(ids[1]), "step": 2})
        await message.reply_text("🔢 **Step 2:** Range (Start End).")
    elif step == 2:
        r = message.text.split(" ")
        start, end, src, dst = int(r[0]), int(r[1]), user_data[user_id]["source"], user_data[user_id]["dest"]
        del user_data[user_id]
        status = await message.reply_text("🏎️ Turbo Forwarding...")
        count = 0
        for m_id in range(start, end + 1):
            try:
                msg = await client.get_messages(src, m_id)
                if msg and (msg.video or msg.document):
                    fid = msg.video.file_id if msg.video else msg.document.file_id
                    await client.send_video(dst, fid, caption=msg.caption or "")
                    if LOG_CHANNEL and LOG_CHANNEL != src:
                        await client.send_video(LOG_CHANNEL, fid, caption=f"📂 Log: `{m_id}`")
                    count += 1
                    await update_stats()
                    await asyncio.sleep(1.5)
            except: continue
        await status.edit(f"🏁 Done! Total: `{count}`")

app.run()
                
