# ---------------------------------------------------
# Project: Multi-Owner Forwarder Pro
# Author: Loser
# Status: Strong & Optimized
# ---------------------------------------------------

import asyncio
from pyrogram import Client, filters
from config import Config

# Bot Initialization
app = Client(
    "forwarder_pro", 
    api_id=Config.API_ID, 
    api_hash=Config.API_HASH, 
    bot_token=Config.BOT_TOKEN
)

# --- MULTI-OWNER LOGIC ---
# Heroku mein OWNER_ID aise dalo: 123456,876543,999888
RAW_OWNERS = str(Config.OWNER_ID).split(",")
OWNER_IDS = [int(i.strip()) for i in RAW_OWNERS]

LOG_CHANNEL = int(Config.LOG_CHANNEL)

# Global Storage
user_data = {}
live_settings = {"active": False, "src": None, "dst": None}

# --- START COMMAND ---
@app.on_message(filters.command("start") & filters.user(OWNER_IDS))
async def start_cmd(client, message):
    await message.reply_text(
        f"🚀 **Strong Forwarder Active!**\n\n"
        f"👤 **Author:** Loser\n"
        f"👑 **Access:** {len(OWNER_IDS)} Owners Authorized\n\n"
        "Commands:\n"
        "▶️ `/live [Source] [Dest]`\n"
        "🏎️ `/batch` (Turbo Mode)\n"
        "🎯 Forward any msg for ID\n"
        "📴 `/stop` | ❌ `/cancel`"
    )

# --- ID CHECKER ---
@app.on_message(filters.forwarded & filters.user(OWNER_IDS))
async def get_id(client, message):
    if message.forward_from_chat:
        await message.reply_text(
            f"🎯 **Target ID:** `{message.forward_from_chat.id}`\n"
            f"📌 **Message ID:** `{message.forward_from_message_id}`"
        )

# --- LIVE LOGIC ---
@app.on_message(filters.command("live") & filters.user(OWNER_IDS))
async def live_on(client, message):
    args = message.text.split()
    if len(args) < 3:
        return await message.reply_text("❌ Format: `/live SourceID DestID` ")
    
    live_settings.update({"src": int(args[1]), "dst": int(args[2]), "active": True})
    await message.reply_text(f"📡 **Live Mode ON**\nSource: `{args[1]}`\nDest: `{args[2]}`")
    if LOG_CHANNEL:
        await client.send_message(LOG_CHANNEL, f"✅ **Live Forwarding Started** by `{message.from_user.id}`")

@app.on_message(filters.command("stop") & filters.user(OWNER_IDS))
async def live_off(client, message):
    live_settings["active"] = False
    await message.reply_text("📴 **Live Mode Stopped!**")

@app.on_message((filters.video | filters.document) & ~filters.forwarded)
async def handle_live(client, message):
    if live_settings["active"] and message.chat.id == live_settings["src"]:
        # Safety: Don't forward back to source
        if message.chat.id == live_settings["dst"]: return

        f_id = message.video.file_id if message.video else message.document.file_id
        try:
            await client.send_video(live_settings["dst"], f_id, caption=message.caption or "")
            if LOG_CHANNEL:
                await client.send_video(LOG_CHANNEL, f_id, caption="📡 **Live Forward Log**")
        except Exception as e:
            print(f"Live Error: {e}")

# --- BATCH LOGIC ---
@app.on_message(filters.command("batch") & filters.user(OWNER_IDS))
async def batch_start(client, message):
    user_data[message.from_user.id] = {"step": 1}
    await message.reply_text("📥 **Step 1:** Source aur Destination ID bhejo (Space dekar).")

@app.on_message(filters.user(OWNER_IDS) & filters.text & ~filters.command(["start", "batch", "live", "stop", "cancel"]))
async def batch_steps(client, message):
    uid = message.from_user.id
    if uid not in user_data: return
    step = user_data[uid]["step"]

    if step == 1:
        try:
            ids = message.text.split()
            user_data[uid].update({"src": int(ids[0]), "dst": int(ids[1]), "step": 2})
            await message.reply_text("🔢 **Step 2:** Message Range (StartID EndID) bhejo.")
        except: await message.reply_text("❌ IDs format galat hai.")
    
    elif step == 2:
        try:
            r = message.text.split()
            start, end = int(r[0]), int(r[1])
            src, dst = user_data[uid]["src"], user_data[uid]["dst"]
            del user_data[uid]
            
            status = await message.reply_text("🏎️ **Batch Shuru...**")
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
                        if count % 10 == 0: await status.edit(f"🚀 Processing: `{count}` files...")
                        await asyncio.sleep(1.5)
                except: continue
            await status.edit(f"🏁 **Batch Done!**\nTotal: `{count}` files forwarded.")
        except: await message.reply_text("❌ Range format galat hai.")

@app.on_message(filters.command("cancel") & filters.user(OWNER_IDS))
async def cancel_batch(client, message):
    user_data.pop(message.from_user.id, None)
    await message.reply_text("❌ **Operation Cancelled.**")

app.run()
    
