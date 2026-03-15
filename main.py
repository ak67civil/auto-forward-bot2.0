import asyncio
from pyrogram import Client, filters
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

# Bot setup
app = Client("forwarder_bot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)

# --- DATABASE SETUP (SUPER SAFE VERSION) ---
db_client = None
users_db = None

mongo_uri = getattr(Config, "MONGO_DB_URI", None) or getattr(Config, "MONGO_URL", None)

if mongo_uri:
    try:
        # Link check kar raha hai, agar format galat hai toh skip karega
        db_client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Check if link is actually valid
        db_client.get_io_loop() 
        users_db = db_client["forwarder_pro_db"]["users"]
        print("✅ MongoDB Connected Successfully!")
    except Exception as e:
        print(f"⚠️ MongoDB Link Error: {e}. Bot will run without Database.")
        db_client = None

OWNER_ID = int(Config.OWNER_ID)
LOG_CHANNEL = int(Config.LOG_CHANNEL)
user_data = {}
live_settings = {}

# --- HELPERS ---
async def is_added(user_id):
    if user_id == OWNER_ID: return True
    if users_db is not None:
        try:
            user = await users_db.find_one({"user_id": user_id})
            return True if user else False
        except: return False
    return False

async def update_stats(user_id):
    if users_db is not None:
        try: await users_db.update_one({"user_id": user_id}, {"$inc": {"forwarded": 1}}, upsert=True)
        except: pass

# --- COMMANDS ---

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    uid = message.from_user.id
    if not await is_added(uid):
        return await message.reply_text("❌ Access Denied. Contact Owner.")
    
    if uid == OWNER_ID:
        menu = "👑 **OWNER MENU**\n\n➕ `/add [ID]`, 📊 `/users`, 📢 `/broadcast`\n🚀 `/batch`, 📡 `/live`, ❌ `/cancel`, 📴 `/stop`"
    else:
        menu = "👋 **USER MENU**\n\n🚀 `/batch`, 📡 `/live`, 🎯 ID Check, ❌ `/cancel`"
    await message.reply_text(menu)

@app.on_message(filters.command("add") & filters.user(OWNER_ID))
async def add_user_cmd(client, message):
    if users_db is None: return await message.reply_text("❌ Database not connected. Check MONGO_DB_URI.")
    try:
        new_uid = int(message.text.split()[1])
        await users_db.update_one({"user_id": new_uid}, {"$set": {"user_id": new_uid, "forwarded": 0}}, upsert=True)
        await message.reply_text(f"✅ User `{new_uid}` Added!")
    except: await message.reply_text("Format: `/add 12345` ")

@app.on_message(filters.forwarded)
async def id_checker(client, message):
    if not await is_added(message.from_user.id): return
    if message.forward_from_chat:
        await message.reply_text(f"🎯 **ID:** `{message.forward_from_chat.id}`\n📌 **Msg ID:** `{message.forward_from_message_id}`")

@app.on_message(filters.command("batch"))
async def batch_init(client, message):
    uid = message.from_user.id
    if not await is_added(uid): return
    user_data[uid] = {"step": 1}
    await message.reply_text("📥 **Step 1:** Source aur Destination ID bhejo (Space dekar).")

@app.on_message(filters.text & ~filters.command(["start", "batch", "live", "users", "add", "broadcast", "stop", "cancel"]))
async def handle_text(client, message):
    uid = message.from_user.id
    if uid not in user_data: return
    step = user_data[uid]["step"]
    if step == 1:
        try:
            ids = message.text.split()
            user_data[uid].update({"src": int(ids[0]), "dst": int(ids[1]), "step": 2})
            await message.reply_text("🔢 **Step 2:** Range bhejo (Start End).")
        except: await message.reply_text("❌ IDs sahi dalo.")
    elif step == 2:
        try:
            r = message.text.split()
            start, end, src, dst = int(r[0]), int(r[1]), user_data[uid]["src"], user_data[uid]["dst"]
            del user_data[uid]
            status = await message.reply_text("🚀 Starting Batch...")
            count = 0
            for m_id in range(start, end + 1):
                try:
                    msg = await client.get_messages(src, m_id)
                    if msg and (msg.video or msg.document):
                        fid = msg.video.file_id if msg.video else msg.document.file_id
                        await client.send_video(dst, fid, caption=msg.caption or "")
                        if LOG_CHANNEL: await client.send_video(LOG_CHANNEL, fid, caption=f"📂 Log | User: `{uid}`")
                        count += 1
                        await update_stats(uid)
                        await asyncio.sleep(1.5)
                except: continue
            await status.edit(f"🏁 Done! Total: `{count}`")
        except: pass

@app.on_message(filters.command("live"))
async def live_setup(client, message):
    uid = message.from_user.id
    if not await is_added(uid): return
    args = message.text.split()
    if len(args) < 3: return
    live_settings[uid] = {"src": int(args[1]), "dst": int(args[2]), "active": True}
    await message.reply_text(f"📡 Live Mode ON for Source `{args[1]}`")

@app.on_message((filters.video | filters.document) & ~filters.forwarded)
async def live_logic(client, message):
    for uid, setting in live_settings.items():
        if setting["active"] and message.chat.id == setting["src"]:
            fid = message.video.file_id if message.video else message.document.file_id
            await client.send_video(setting["dst"], fid, caption=message.caption or "")
            if LOG_CHANNEL: await client.send_video(LOG_CHANNEL, fid, caption="📡 Live Log")
            await update_stats(uid)

app.run()
