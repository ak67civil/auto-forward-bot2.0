import asyncio
from pyrogram import Client, filters
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

# Database Setup
db_client = AsyncIOMotorClient(Config.MONGO_URL)
db = db_client.forward_bot
collection = db.settings

app = Client(
    "forwarder_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# 1. Function: Link se Message ID nikalne ke liye
def get_id(text):
    if "t.me/c/" in text or "t.me/" in text:
        return int(text.split('/')[-1])
    try:
        return int(text)
    except:
        return None

# 2. Command: /start (Bot Help Menu)
@app.on_message(filters.command("start") & filters.user(Config.OWNER_ID))
async def start_cmd(client, message):
    help_text = (
        "👋 **Bhai, Tera Forwarder Bot Online Hai!**\n\n"
        "🛠 **Meri Commands:**\n"
        "▶️ `/add -100Source -100Dest` : Live forwarding set karein.\n"
        "▶️ `/batch [Source] [Dest] [Start] [End]` : Purani range copy karein.\n"
        "▶️ `/list` : Dekhein kaunse channels linked hain.\n\n"
        "📌 **Note:** Bot dono channels mein Admin hona chahiye!"
    )
    await message.reply_text(help_text)

# 3. Command: /batch (Tera Main Request: Range 200-400 ke liye)
@app.on_message(filters.command("batch") & filters.user(Config.OWNER_ID))
async def batch_forward(client, message):
    try:
        args = message.text.split(" ")
        if len(args) < 5:
            return await message.reply_text("❌ **Sahi Format:**\n`/batch [SourceID] [DestID] [StartID/Link] [EndID/Link]`")
        
        source, dest = int(args[1]), int(args[2])
        start_id, end_id = get_id(args[3]), get_id(args[4])

        status_msg = await message.reply_text(f"⏳ **Batch Processing Start...**\n`{start_id}` se `{end_id}` tak copy ho raha hai.")
        
        count = 0
        for msg_id in range(start_id, end_id + 1):
            try:
                await client.copy_message(chat_id=dest, from_chat_id=source, message_id=msg_id)
                count += 1
                if count % 10 == 0:
                    await status_msg.edit(f"⏳ **Processing...**\n`{count}` messages copy ho gaye.")
                await asyncio.sleep(2) # Flood wait se bachne ke liye gap
            except Exception:
                continue
        
        await status_msg.edit(f"✅ **Batch Complete!**\nTotal `{count}` messages forward hue.")
    except Exception as e:
        await message.reply_text(f"❌ Error: `{e}`")

# 4. Command: /add (Naye messages ke liye)
@app.on_message(filters.command("add") & filters.user(Config.OWNER_ID))
async def add_link(client, message):
    try:
        args = message.text.split(" ")
        source, dest = int(args[1]), int(args[2])
        await collection.update_one({"source": source}, {"$set": {"dest": dest}}, upsert=True)
        await message.reply_text("✅ **Linked!** Ab naye messages apne aap forward honge.")
    except:
        await message.reply_text("❌ `/add -100SourceID -100DestID` use karein.")

# 5. Command: /list (Saari links dekhne ke liye)
@app.on_message(filters.command("list") & filters.user(Config.OWNER_ID))
async def list_links(client, message):
    links = collection.find({})
    res = "📋 **Aapki Active Links:**\n\n"
    async for link in links:
        res += f"🔹 From: `{link['source']}` ➔ To: `{link['dest']}`\n"
    await message.reply_text(res if "🔹" in res else "❌ Koi link nahi mili.")

# 6. Live Forwarding Logic
@app.on_message(filters.chat() & ~filters.command(["add", "batch", "list", "start"]))
async def forwarder(client, message):
    data = await collection.find_one({"source": message.chat.id})
    if data:
        try:
            await message.copy(chat_id=data["dest"])
        except:
            pass

print("Bot is Starting...")
app.run()
