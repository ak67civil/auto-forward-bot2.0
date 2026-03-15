import asyncio
from pyrogram import Client, filters
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

# Bot Setup
app = Client("forwarder_bot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)

# MongoDB Setup (Crash-proof)
db_client = None
stats_db = None
try:
    mongo_uri = getattr(Config, "MONGO_DB_URI", None) or getattr(Config, "MONGO_URL", None)
    if mongo_uri:
        db_client = AsyncIOMotorClient(mongo_uri)
        stats_db = db_client["forwarder_bot"]["stats"]
except:
    pass

LOG_CHANNEL = Config.LOG_CHANNEL
user_data = {}
live_settings = {"active": False, "source": None, "dest": None}

# Helper to Update Stats
async def update_stats():
    if stats_db is not None:
        try:
            await stats_db.update_one({"id": "total_files"}, {"$inc": {"count": 1}}, upsert=True)
        except: pass

# --- COMMANDS ---

@app.on_message(filters.command("start") & filters.user(Config.OWNER_ID))
async def start_cmd(client, message):
    menu = (
        "👑 **Forwarder Master Bot**\n\n"
        "🚀 `/batch` - Range forwarding (Purani videos)\n"
        "📡 `/live` - Real-time forwarding (Nayi videos)\n"
        "📊 `/stats` - Total kitna forward hua\n"
        "📴 `/stop_live` - Live mode band karein\n"
        "❌ `/cancel` - Batch beech mein rokein\n\n"
        "💡 **ID Check:** Kisi bhi channel ka message mujhe forward karo."
    )
    await message.reply_text(menu)

# ID Checker Fix (Always Active)
@app.on_message(filters.forwarded & filters.user(Config.OWNER_ID))
async def id_checker(client, message):
    if message.forward_from_chat:
        await message.reply_text(f"🎯 **Channel ID:** `{message.forward_from_chat.id}`\n📌 **Msg ID:** `{message.forward_from_message_id}`")
    else:
        await message.reply_text("❌ ID nahi nikal payi. Message channel se forward karein.")

# Live Forwarding with Loop Protection
@app.on_message(filters.command("live") & filters.user(Config.OWNER_ID))
async def live_on(client, message):
    args = message.text.split()
    if len(args) < 3:
        return await message.reply_text("❌ Format: `/live [SourceID] [DestID]`")
    live_settings.update({"source": int(args[1]), "dest": int(args[2]), "active": True})
    await message.reply_text(f"✅ **Live Forwarding ON**\nSource: `{args[1]}`\nTarget: `{args[2]}`")

@app.on_message(filters.command("stop_live") & filters.user(Config.OWNER_ID))
async def live_off(client, message):
    live_settings["active"] = False
    await message.reply_text("📴 Live Mode OFF ho gaya.")

# --- LIVE LOGIC ---
@app.on_message((filters.video | filters.document) & ~filters.forwarded)
async def on_new_video(client, message):
    if live_settings["active"] and message.chat.id == live_settings["source"]:
        # Safety: Bot khud ke bheje messages ko wapas forward nahi karega
        file_id = message.video.file_id if message.video else message.document.file_id
        try:
            await client.send_video(chat_id=live_settings["dest"], video=file_id, caption=message.caption or "")
            if LOG_CHANNEL:
                await client.send_video(chat_id=LOG_CHANNEL, video=file_id, caption="📡 Live Log Record")
            await update_stats()
        except Exception as e: print(f"Error: {e}")

# --- BATCH LOGIC ---
@app.on_message(filters.command("batch") & filters.user(Config.OWNER_ID))
async def batch_start(client, message):
    user_data[message.from_user.id] = {"step": 1}
    await message.reply_text("📥 **Step 1:** Source aur Dest ID bhejo (Space dekar).")

@app.on_message(filters.user(Config.OWNER_ID) & filters.text & ~filters.command(["start", "batch", "live", "stats", "stop_live", "cancel"]))
async def batch_handler(client, message):
    uid = message.from_user.id
    if uid not in user_data: return
    step = user_data[uid]["step"]

    if step == 1:
        try:
            ids = message.text.split()
            user_data[uid].update({"src": int(ids[0]), "dst": int(ids[1]), "step": 2})
            await message.reply_text("🔢 **Step 2:** Range bhejo (Start End).")
        except: await message.reply_text("❌ IDs sahi format mein dalo.")
    elif step == 2:
        try:
            r = message.text.split()
            start, end, src, dst = int(r[0]), int(r[1]), user_data[uid]["src"], user_data[uid]["dst"]
            del user_data[uid]
            status = await message.reply_text("🏎️ **Turbo Batch Shuru...**")
            count = 0
            for m_id in range(start, end + 1):
                try:
                    msg = await client.get_messages(src, m_id)
                    if msg and (msg.video or msg.document):
                        fid = msg.video.file_id if msg.video else msg.document.file_id
                        await client.send_video(dst, fid, caption=msg.caption or "")
                        if LOG_CHANNEL:
                            await client.send_video(LOG_CHANNEL, fid, caption=f"📂 Log: `{m_id}`")
                        count += 1
                        await update_stats()
                        if count % 10 == 0: await status.edit(f"🚀 `{count}` processed...")
                        await asyncio.sleep(1.5)
                except: continue
            await status.edit(f"🏁 Done! Total: `{count}`")
            await client.send_message(dst, "Done ✅")
        except: await message.reply_text("❌ Range galat hai.")

@app.on_message(filters.command("stats") & filters.user(Config.OWNER_ID))
async def show_stats(client, message):
    if stats_db is not None:
        data = await stats_db.find_one({"id": "total_files"})
        count = data["count"] if data else 0
        await message.reply_text(f"📊 **Total Files Forwarded:** `{count}`")
    else:
        await message.reply_text("❌ MongoDB link nahi mila, stats save nahi ho rahe.")

@app.on_message(filters.command("cancel") & filters.user(Config.OWNER_ID))
async def cancel_action(client, message):
    user_data.pop(message.from_user.id, None)
    await message.reply_text("❌ Kaam cancel kar diya.")

app.run()
    
