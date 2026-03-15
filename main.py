import asyncio
from pyrogram import Client, filters
from config import Config

app = Client("forwarder_bot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)

# 1. ID Checker (Forward karo aur ID pao)
@app.on_message(filters.forwarded & filters.user(Config.OWNER_ID))
async def get_info(client, message):
    c_id = message.forward_from_chat.id
    m_id = message.forward_from_message_id
    await message.reply_text(f"✅ **Sahi Data Mil Gaya!**\n\n📌 Channel ID: `{c_id}`\n📌 Message ID: `{m_id}`\n\nAb `/batch` chalao aur yahi details dalo.")

# 2. Simple Batch Command
@app.on_message(filters.command("batch") & filters.user(Config.OWNER_ID))
async def batch_forward(client, message):
    try:
        args = message.text.split(" ")
        if len(args) < 5:
            return await message.reply_text("❌ `/batch [SourceID] [DestID] [StartID] [EndID]`")
        
        source, dest = int(args[1]), int(args[2])
        start, end = int(args[3]), int(args[4])
        
        status = await message.reply_text("⏳ **Force Forwarding Shuru...**")
        count = 0
        for m_id in range(start, end + 1):
            try:
                # Direct copy (sabse powerful tarika)
                await client.copy_message(chat_id=dest, from_chat_id=source, message_id=m_id)
                count += 1
                if count % 5 == 0:
                    await status.edit(f"🚀 `{count}` messages bhej diye...")
                await asyncio.sleep(2)
            except Exception: continue
            
        await status.edit(f"✅ Kaam Khatam! Total `{count}` messages forward hue.")
    except Exception as e: await message.reply_text(f"❌ Error: {e}")

app.run()
