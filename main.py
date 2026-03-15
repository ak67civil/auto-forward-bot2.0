
import asyncio
from pyrogram import Client, filters
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

# Bot initialization
app = Client(
    "forwarder_bot", 
    api_id=Config.API_ID, 
    api_hash=Config.API_HASH, 
    bot_token=Config.BOT_TOKEN
)

# Database Setup
mongo_uri = getattr(Config, "MONGO_DB_URI", None) or getattr(Config, "MONGO_URL", None)
db_client = AsyncIOMotorClient(mongo_uri)
db = db_client["forwarder_pro_db"]
users_db = db["users"]

# Configs
OWNER_ID = int(Config.OWNER_ID)
LOG_CHANNEL = int(Config.LOG_CHANNEL)

# --- GLOBAL VARIABLES ---
user_data = {}
live_settings = {} # Stores live config for each user

# --- HELPER FUNCTIONS ---
async def is_added(user_id):
    if user_id == OWNER_ID: return True
    user = await users_db.find_one({"user_id": user_id})
    return True if user else False

async def update_stats(user_id):
    await users_db.update_one(
        {"user_id": user_id}, 
        {"$inc": {"forwarded": 1}}, 
        upsert=True
    )

# --- OWNER COMMANDS ---

@app.on_message(filters.command("add") & filters.user(OWNER_ID))
async def add_user_cmd(client, message):
    try:
        new_uid = int(message.text.split()[1])
        await users_db.update_one(
            {"user_id": new_uid}, 
            {"$set": {"user_id": new_uid, "forwarded": 0}}, 
            upsert=True
        )
        await message.reply_text(f"✅ User `{new_uid}` added to access list.")
    except:
        await message.reply_text("❌ Sahi format dalo: `/add 12345678` ")

@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_cmd(client, message):
    if not message.reply_to_message:
        return await message.reply_text("Bhai, kisi message ko reply karke `/broadcast` likho.")
    
    all_users = users_db.find({})
    count = 0
    # Adding owner to broadcast list too
    await message.reply_to_message.copy(OWNER_ID)
    async for user in all_users:
        try:
            if user["user_id"] != OWNER_ID:
                await message.reply_to_message.copy(user["user_id"])
                count += 1
        except: pass
    await message.reply_text(f"📢 Broadcast Done! `{count + 1}` users tak message pahucha.")

@app.on_message(filters.command("users") & filters.user(OWNER_ID))
async def total_users_stats(client, message):
    cursor = users_db.find({})
    text = "👥 **All Users & Stats:**\n\n"
    async for user in cursor:
        text += f"👤 `{user['user_id']}` | 📂 Sent: `{user.get('forwarded', 0)}` \n"
    await message.reply_text(text)

# --- SHARED COMMANDS (Owner + Added Users) ---

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    uid = message.from_user.id
    if not await is_added(uid):
        return await message.reply_text("❌ Access Denied. Contact Owner.")
    
    if uid == OWNER_ID:
        text = (
            "👑 **OWNER MENU**\n\n"
            "➕ `/add [ID]` - Add new user\n"
            "👥 `/users` - User list & stats\n"
            "📢 `/broadcast` - Message to all (Reply)\n\n"
            "🚀 `/batch` | 📡 `/live` | ❌ `/cancel` | 📴 `/stop`"
        )
    else:
        text = (
            "👋 **USER MENU**\n\n"
            "🚀 `/batch` - Forward old videos\n"
            "📡 `/live` - Real-time forward\n"
            "❌ `/cancel` - Stop batch\n"
            "📴 `/stop` - Stop live"
        )
    await message.reply_text(text)

# 🎯 ID CHECKER (Always On for authorized)
@app.on_message(filters.forwarded)
async def id_checker(client, message):
    if not await is_added(message.from_user.id): return
    if message.forward_from_chat:
        await message.reply_text(f"🎯 **ID:** `{message.forward_from_chat.id}`\n📌 **Msg ID:** `{message.forward_from_message_id}`")

# 📡 LIVE SETUP
@app.on_message(filters.command("live"))
async def live_setup(client, message):
    uid = message.from_user.id
    if not await is_added(uid): return
    args = message.text.split()
    if len(args) < 3: return await message.reply_text("❌ Use: `/live SourceID DestID` ")
    live_settings[uid] = {"src": int(args[1]), "dst": int(args[2]), "active": True}
    await message.reply_text(f"✅ Live Mode ON for Source `{args[1]}`")

@app.on_message(filters.command("stop"))
async def stop_live(client, message):
    uid = message.from_user.id
    if uid in live_settings:
        live_settings[uid]["active"] = False
        await message.reply_text("📴 Live Forwarding OFF.")

# 🚀 BATCH SETUP
@app.on_message(filters.command("batch"))
async def batch_init(client, message):
    uid = message.from_user.id
    if not await is_added(uid): return
    user_data[uid] = {"step": 1}
    await message.reply_text("📥 **Step 1:** Source aur Destination ID bhejo (Space dekar).")

@app.on_message(filters.text & ~filters.command(["start", "batch", "live", "users", "add", "broadcast", "stop", "cancel"]))
async def handle_text_logic(client, message):
    uid = message.from_user.id
    if uid not in user_data: return
    step = user_data[uid]["step"]

    if step == 1:
        try:
            ids = message.text.split()
            user_data[uid].update({"src": int(ids[0]), "dst": int(ids[1]), "step": 2})
            await message.reply_text("🔢 **Step 2:** Range bhejo (Start End).")
        except: await message.reply_text("❌ Format sahi dalo.")
    elif step == 2:
        try:
            r = message.text.split()
            start, end, src, dst = int(r[0]), int(r[1]), user_data[uid]["src"], user_data[uid]["dst"]
            del user_data[uid]
            status = await message.reply_text("🏎️ **Turbo Batch Started...**")
            count = 0
            for m_id in range(start, end + 1):
                try:
                    msg = await client.get_messages(src, m_id)
                    if msg and (msg.video or msg.document):
                        fid = msg.video.file_id if msg.video else msg.document.file_id
                        await client.send_video(dst, fid, caption=msg.caption or "")
                        if LOG_CHANNEL:
                            await client.send_video(LOG_CHANNEL, fid, caption=f"📂 Batch Log\nUser: `{uid}`\nID: `{m_id}`")
                        count += 1
                        await update_stats(uid)
                        if count % 10 == 0: await status.edit(f"🚀 `{count}` sent...")
                        await asyncio.sleep(1.5)
                except: continue
            await status.edit(f"🏁 Done! Sent: `{count}`")
            await client.send_message(dst, "Done ✅")
        except: await message.reply_text("❌ Range galat hai.")

# 📡 LIVE LOGIC (Real-time detection)
@app.on_message((filters.video | filters.document) & ~filters.forwarded)
async def live_forward_logic(client, message):
    for uid, setting in live_settings.items():
        if setting["active"] and message.chat.id == setting["src"]:
            fid = message.video.file_id if message.video else message.document.file_id
            await client.send_video(setting["dst"], fid, caption=message.caption or "")
            if LOG_CHANNEL:
                await client.send_video(LOG_CHANNEL, fid, caption=f"📡 Live Log\nUser: `{uid}`")
            await update_stats(uid)

@app.on_message(filters.command("cancel"))
async def cancel_batch(client, message):
    user_data.pop(message.from_user.id, None)
    await message.reply_text("❌ Batch cancelled.")

app.run()
                
