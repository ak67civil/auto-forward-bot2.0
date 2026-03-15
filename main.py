import os
from pyrogram import Client, filters
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

# Database Setup
db_client = AsyncIOMotorClient(Config.MONGO_URL)
db = db_client.forward_bot
collection = db.settings

app = Client("forwarder_bot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)

# Command: Add Forwarding Link
@app.on_message(filters.command("add") & filters.user(Config.OWNER_ID))
async def add_forward(client, message):
    try:
        # Format: /add -100source -100dest
        input_data = message.text.split(" ")
        source = int(input_data[1])
        dest = int(input_data[2])
        
        await collection.update_one(
            {"source": source},
            {"$set": {"dest": dest}},
            upsert=True
        )
        await message.reply_text(f"✅ **Link Added!**\n\n**From:** `{source}`\n**To:** `{dest}`")
    except Exception as e:
        await message.reply_text(f"❌ **Error:** `/add SourceID DestID`\n\n{e}")

# Command: Show all links
@app.on_message(filters.command("list") & filters.user(Config.OWNER_ID))
async def list_forwards(client, message):
    links = collection.find({})
    text = "📂 **Your Forwarding Links:**\n\n"
    async for link in links:
        text += f"• `{link['source']}` ➡️ `{link['dest']}`\n"
    await message.reply_text(text)

# The Forwarding Logic
@app.on_message(filters.chat())
async def forward_logic(client, message):
    # Skip if message is a command
    if message.text and message.text.startswith("/"):
        return

    # Check if this chat is a source in our DB
    data = await collection.find_one({"source": message.chat.id})
    if data:
        try:
            # 1. Main Forward
            await message.copy(chat_id=data["dest"])
            
            # 2. Log Channel Report
            log_msg = f"✅ **Forwarded Successfully**\n\n**From:** `{message.chat.id}`\n**To:** `{data['dest']}`"
            await message.copy(chat_id=Config.LOG_CHANNEL, caption=log_msg)
            
        except Exception as e:
            await client.send_message(Config.LOG_CHANNEL, f"❌ **Error:**\nChat: `{message.chat.id}`\nError: `{e}`")

print("Bot is Updated and Running...")
app.run()
