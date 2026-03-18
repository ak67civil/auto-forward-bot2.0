# ---------------------------------------------------
# Project: Lite Forwarder Bot
# Author: Loser
# Mode: Single User (No Database)
# ---------------------------------------------------

import asyncio
from pyrogram import Client, filters
from config import Config

# Bot Setup
app = Client(
    "forwarder_bot", 
    api_id=Config.API_ID, 
    api_hash=Config.API_HASH, 
    bot_token=Config.BOT_TOKEN
)

# Configs (Heroku se aayenge)
OWNER_ID = int(Config.OWNER_ID)
LOG_CHANNEL = int(Config.LOG_CHANNEL)

# Globals (Temporary storage)
user_data = {}
live_settings = {"active": False, "src": None, "dst": None}

# --- COMMANDS ---

@app.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start(client, message):
    menu = (
        "👑 **Loser's Forwarder (Lite)**\n\n"
        "🚀 `/batch` - Purani videos ke liye\n"
        "📡 `/live` - Nayi videos ke liye\n"
        "📴 `/stop` - Live band karne ke liye\n"
        "❌ `/cancel` - Batch rokne ke liye\n\n"
        "🎯 **ID Check:** Koi bhi message forward karo ID mil jayegi."
    )
    await message.reply_text(menu)

# 🎯 ID Checker (Always On for Owner)
@app.on_message(filters.forwarded & filters.user(OWNER_ID))
async def id_check(client, message):
    if message.forward_from_chat:
        await message.reply_text(f"🎯 **Channel ID:** `{message.forward_from_chat.id}`\n📌 **Msg ID:** `{message.forward_from_message_id}`")

# --- LIVE FORWARDING ---

@app.on_message(filters.command("live") & filters.user(OWNER_ID))
async def live_on(client, message):
    args = message.text.split()
    if len(args) < 3:
        return await message.reply_text("❌ Format: `/live SourceID DestID` ")
    live_settings.update({"src": int(args[1]), "dst": int(args[2]), "active": True})
    await message.reply_text(f"📡 **Live Mode ON**\nSource: `{args[1]}`\nTarget: `{args[2]}`")

@app.on_message(filters.command("stop") & filters.user(OWNER_ID))
async def live_off(client, message):
    live_settings["active"] = False
    await message.reply_text("📴 Live Mode OFF ho gaya.")

@app.on_message((filters.video | filters.document) & ~filters.forwarded)
async def live_logic(client, message):
    # Sirf tab chalega jab Source se message aaye aur setup Active ho
    if live_settings["active"] and message.chat.id == live_settings["src"]:
        # Loop Protection: Log ya Target channel se khud ko forward nahi karega
        if message.chat.id == live_settings["dst"] or message.chat.id == LOG_CHANNEL:
            return

        fid = message.video.file_id if message.video else message.document.file_id
        try:
            await client.send_video(live_settings["dst"], fid, caption=message.caption or "")
            if LOG_CHANNEL:
                await client.send_video(LOG_CHANNEL, fid, caption="📡 **Live Log Record**")
        except Exception as e:
            print(f"Error: {e}")

# --- BATCH FORWARDING ---

@app.on_message(filters.command("batch") & filters.user(OWNER_ID))
async def batch_cmd(client, message):
    user_data[OWNER_ID] = {"step": 1}
    await message.reply_text("📥 **Step 1:** Source aur Destination ID bhejo (Space dekar).")

@app.on_message(filters.user(OWNER_ID) & filters.text & ~filters.command(["start", "batch", "live", "stop", "cancel"]))
async def batch_handler(client, message):
    if OWNER_ID not in user_data: return
    step = user_data[OWNER_ID]["step"]
    
    if step == 1:
        try:
            ids = message.text.split()
            user_data[OWNER_ID].update({"src": int(ids[0]), "dst": int(ids[1]), "step": 2})
            await message.reply_text("🔢 **Step 2:** Message Range bhejo (StartID EndID).")
        except: await message.reply_text("❌ Sahi IDs dalo.")
    elif step == 2:
        try:
            r = message.text.split()
            start, end = int(r[0]), int(r[1])
            src, dst = user_data[OWNER_ID]["src"], user_data[OWNER_ID]["dst"]
            del user_data[OWNER_ID]
            
            status = await message.reply_text("🚀 **Batch Processing...**")
            count = 0
            for m_id in range(start, end + 1):
                try:
                    m = await client.get_messages(src, m_id)
                    if m and (m.video or m.document):
                        fid = m.video.file_id if m.video else m.document.file_id
                        await client.send_video(dst, fid, caption=m.caption or "")
                        if LOG_CHANNEL:
                            await client.send_video(LOG_CHANNEL, fid, caption=f"📂 Log: `{m_id}`")
                        count += 1
                        if count % 10 == 0: await status.edit(f"🚀 `{count}` processed...")
                        await asyncio.sleep(1.5)
                except: continue
            await status.edit(f"🏁 **Done Loser!** Total sent: `{count}`")
        except: await message.reply_text("❌ Range galat hai.")

@app.on_message(filters.command("cancel") & filters.user(OWNER_ID))
async def cancel(client, message):
    user_data.pop(OWNER_ID, None)
    await message.reply_text("❌ Batch cancelled.")

app.run()
    
