import asyncio
import os
from pyrogram import Client, filters

# --- CONFIGS ---
# Heroku se values uthayega
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL"))

# Multi-Owner Fix: Comma se IDs alag karke list banayega
RAW_OWNER = os.environ.get("OWNER_ID", "0")
OWNER_IDS = [int(i.strip()) for i in RAW_OWNER.split(",") if i.strip().isdigit()]

app = Client("loser_forwarder", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Global Variables
user_data = {}
live_settings = {} # Individual live settings for each owner

# --- START COMMAND ---
@app.on_message(filters.command("start") & filters.user(OWNER_IDS))
async def start(client, message):
    await message.reply_text(
        f"🚀 **Strong Forwarder Active!**\n\n"
        f"👤 **Author:** Loser\n"
        f"👑 **Owners:** `{len(OWNER_IDS)}` Authorized\n\n"
        "📜 **Commands:**\n"
        "🏎️ `/batch` - Bulk forward old files\n"
        "📡 `/live` - Real-time forwarding\n"
        "📴 `/stop` - Stop live forwarding\n"
        "❌ `/cancel` - Cancel current batch\n"
        "🎯 **Checker:** Forward any message here to get ID."
    )

# --- ID CHECKER (Always On) ---
@app.on_message(filters.forwarded & filters.user(OWNER_IDS))
async def checker(client, message):
    if message.forward_from_chat:
        chat_id = message.forward_from_chat.id
        msg_id = message.forward_from_message_id
        await message.reply_text(f"🎯 **Target ID:** `{chat_id}`\n📌 **Message ID:** `{msg_id}`")

# --- LIVE FORWARD LOGIC ---
@app.on_message(filters.command("live") & filters.user(OWNER_IDS))
async def live_on(client, message):
    args = message.text.split()
    if len(args) < 3:
        return await message.reply_text("❌ **Format:** `/live SourceID DestID` ")
    
    uid = message.from_user.id
    live_settings[uid] = {"src": int(args[1]), "dst": int(args[2]), "active": True}
    
    await message.reply_text(f"📡 **Live Mode ON!**\nFrom: `{args[1]}`\nTo: `{args[2]}`")
    if LOG_CHANNEL:
        await client.send_message(LOG_CHANNEL, f"✅ **Live Setup** by `{uid}`\nSource: `{args[1]}`")

@app.on_message(filters.command("stop") & filters.user(OWNER_IDS))
async def live_off(client, message):
    uid = message.from_user.id
    if uid in live_settings:
        live_settings[uid]["active"] = False
        await message.reply_text("📴 **Live Forwarding Stopped.**")

@app.on_message((filters.video | filters.document) & ~filters.forwarded)
async def live_handler(client, message):
    # Check if message is from any active source
    for uid, config in live_settings.items():
        if config["active"] and message.chat.id == config["src"]:
            file_id = message.video.file_id if message.video else message.document.file_id
            try:
                await client.send_video(config["dst"], file_id, caption=message.caption or "")
                if LOG_CHANNEL:
                    await client.send_video(LOG_CHANNEL, file_id, caption=f"📡 **Live Log**\nOwner: `{uid}`")
            except Exception as e:
                print(f"Live Error: {e}")

# --- BATCH FORWARD LOGIC ---
@app.on_message(filters.command("batch") & filters.user(OWNER_IDS))
async def batch_init(client, message):
    user_data[message.from_user.id] = {"step": 1}
    await message.reply_text("📥 **Step 1:** Source aur Destination ID bhejo (Space dekar).")

@app.on_message(filters.user(OWNER_IDS) & filters.text & ~filters.command(["start", "batch", "live", "stop", "cancel"]))
async def batch_manager(client, message):
    uid = message.from_user.id
    if uid not in user_data: return
    step = user_data[uid]["step"]

    if step == 1:
        try:
            ids = message.text.split()
            user_data[uid].update({"src": int(ids[0]), "dst": int(ids[1]), "step": 2})
            await message.reply_text("🔢 **Step 2:** Message Range (StartID EndID) bhejo.")
        except: await message.reply_text("❌ IDs sahi se dalo.")
    
    elif step == 2:
        try:
            range_data = message.text.split()
            start, end = int(range_data[0]), int(range_data[1])
            src, dst = user_data[uid]["src"], user_data[uid]["dst"]
            del user_data[uid]
            
            status = await message.reply_text("🏎️ **Turbo Batch Started...**")
            count = 0
            for m_id in range(start, end + 1):
                try:
                    m = await client.get_messages(src, m_id)
                    if m and (m.video or m.document):
                        f_id = m.video.file_id if m.video else m.document.file_id
                        await client.send_video(dst, f_id, caption=m.caption or "")
                        if LOG_CHANNEL:
                            await client.send_video(LOG_CHANNEL, f_id, caption=f"📂 **Batch Log**\nMsg ID: `{m_id}`")
                        count += 1
                        if count % 10 == 0: await status.edit(f"🚀 Sent `{count}` files...")
                        await asyncio.sleep(1.5) # Flood wait avoid karne ke liye
                except: continue
            await status.edit(f"🏁 **Batch Done, Loser!**\nTotal: `{count}` files sent.")
        except: await message.reply_text("❌ Range galat hai.")

@app.on_message(filters.command("cancel") & filters.user(OWNER_IDS))
async def cancel_op(client, message):
    user_data.pop(message.from_user.id, None)
    await message.reply_text("❌ **Operation Cancelled.**")

print("Bot is starting...")
app.run()
