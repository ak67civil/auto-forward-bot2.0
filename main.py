import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

app = Client("forwarder_bot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)

# DB Setup
db_client = AsyncIOMotorClient(Config.MONGO_URL)
db = db_client.forward_bot
collection = db.settings

# Global dictionary to store temporary data for batch
batch_data = {}

def get_id(text):
    if "t.me/c/" in text or "t.me/" in text:
        return int(text.split('/')[-1])
    try: return int(text)
    except: return None

@app.on_message(filters.command("start") & filters.user(Config.OWNER_ID))
async def start_cmd(client, message):
    await message.reply_text("👋 **Bhai, Forwarder Pro ready hai!**\n\nCommands:\n1️⃣ `/batch` - Purane videos bhejni ke liye (Step-by-step)\n2️⃣ `/add` - Naye videos auto-forward ke liye\n3️⃣ `/cancel` - Kisi bhi waqt process rokne ke liye")

# --- Interactive Batch Logic ---

@app.on_message(filters.command("batch") & filters.user(Config.OWNER_ID))
async def start_batch(client, message):
    batch_data[message.from_user.id] = {"step": 1}
    await message.reply_text("📥 **Step 1:**\nJis channel se video uthani hai (Source), uski **ID** ya uske kisi message ka **Link** bhejo.")

@app.on_message(filters.user(Config.OWNER_ID) & filters.text & ~filters.command(["start", "batch", "add", "cancel", "list"]))
async def handle_steps(client, message):
    user_id = message.from_user.id
    if user_id not in batch_data: return

    step = batch_data[user_id].get("step")

    if step == 1:
        # Source ID lena
        source = get_id(message.text)
        if not source: return await message.reply_text("❌ Galat ID/Link! Phir se bhejo.")
        batch_data[user_id]["source"] = source
        batch_data[user_id]["step"] = 2
        await message.reply_text("📤 **Step 2:**\nAb jis channel mein video bhejni hai (Destination), uski **ID** bhejo.")

    elif step == 2:
        # Destination ID lena
        dest = get_id(message.text)
        if not dest: return await message.reply_text("❌ Galat ID! Phir se bhejo.")
        batch_data[user_id]["dest"] = dest
        batch_data[user_id]["step"] = 3
        await message.reply_text("🔢 **Step 3:**\nKahan se shuru karna hai? **(Start Message Link/ID)** bhejo.")

    elif step == 3:
        # Start ID lena
        start = get_id(message.text)
        batch_data[user_id]["start"] = start
        batch_data[user_id]["step"] = 4
        await message.reply_text("🏁 **Step 4:**\nKahan tak forward karna hai? **(End Message Link/ID)** bhejo.")

    elif step == 4:
        # End ID aur Final Forwarding
        end = get_id(message.text)
        source = batch_data[user_id]["source"]
        dest = batch_data[user_id]["dest"]
        start = batch_data[user_id]["start"]
        
        await message.reply_text(f"✅ **Sab tayyar hai!**\nSource: `{source}`\nDest: `{dest}`\nRange: `{start}` to `{end}`\n\n**Forwarding shuru kar raha hoon...**")
        
        count = 0
        status = await message.reply_text("⏳ Processing...")
        
        # Data delete kar do batch shuru hone se pehle
        del batch_data[user_id]

        for msg_id in range(start, end + 1):
            try:
                msg = await client.get_messages(source, msg_id)
                if msg and not msg.empty:
                    await msg.copy(chat_id=dest)
                    count += 1
                    if count % 10 == 0:
                        await status.edit(f"🚀 `{count}` messages bhej diye hain...")
                    await asyncio.sleep(2)
            except Exception: continue
        
        await status.edit(f"🏁 **Mission Successful!**\nTotal `{count}` videos forward ho gayi hain.")

@app.on_message(filters.command("cancel") & filters.user(Config.OWNER_ID))
async def cancel_batch(client, message):
    if message.from_user.id in batch_data:
        del batch_data[message.from_user.id]
        await message.reply_text("❌ Process cancel kar diya gaya hai.")

# --- Live Forwarding (As it is) ---
@app.on_message(filters.chat() & ~filters.command(["start", "batch", "add", "cancel", "list"]))
async def forwarder(client, message):
    data = await collection.find_one({"source": message.chat.id})
    if data:
        try: await message.copy(chat_id=data["dest"])
        except: pass

app.run()
    
