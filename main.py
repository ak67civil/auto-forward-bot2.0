import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config

app = Client("forwarder_bot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)

user_data = {}

@app.on_message(filters.command("start") & filters.user(Config.OWNER_ID))
async def start_cmd(client, message):
    await message.reply_text("👋 **Forwarder Pro (Notification Mode) Ready!**\n\nAb /batch se jo bhi jayega, uska notification members ko milega.")

@app.on_message(filters.forwarded & filters.user(Config.OWNER_ID))
async def get_info(client, message):
    c_id = message.forward_from_chat.id
    m_id = message.forward_from_message_id
    await message.reply_text(f"🎯 **Data Mil Gaya!**\nChannel ID: `{c_id}`\nMessage ID: `{m_id}`")

@app.on_message(filters.command("batch") & filters.user(Config.OWNER_ID))
async def start_batch(client, message):
    user_data[message.from_user.id] = {"step": 1}
    await message.reply_text("📥 **Step 1:**\nSource aur Dest ID bhejo: `-100Source -100Dest` ")

@app.on_message(filters.user(Config.OWNER_ID) & filters.text & ~filters.command(["start", "batch", "cancel"]))
async def handle_steps(client, message):
    user_id = message.from_user.id
    if user_id not in user_data: return
    step = user_data[user_id].get("step")

    if step == 1:
        try:
            ids = message.text.split(" ")
            user_data[user_id]["source"], user_data[user_id]["dest"] = int(ids[0]), int(ids[1])
            user_data[user_id]["step"] = 2
            await message.reply_text("🔢 **Step 2:** Range bhejo: `200 400` ")
        except: await message.reply_text("❌ IDs sahi format mein dalo.")

    elif step == 2:
        try:
            range_ids = message.text.split(" ")
            start, end = int(range_ids[0]), int(range_ids[1])
            source, dest = user_data[user_id]["source"], user_data[user_id]["dest"]
            del user_data[user_id]
            
            status = await message.reply_text("🚀 **Fresh Forwarding Shuru...**")
            count = 0

            for m_id in range(start, end + 1):
                try:
                    msg = await client.get_messages(source, m_id)
                    if msg and (msg.video or msg.document):
                        # Ye method video ko 'New Post' ki tarah bhejta hai
                        if msg.video:
                            await client.send_video(chat_id=dest, video=msg.video.file_id, caption=msg.caption)
                        elif msg.document:
                            await client.send_document(chat_id=dest, document=msg.document.file_id, caption=msg.caption)
                        
                        count += 1
                        if count % 10 == 0:
                            await status.edit(f"🚀 `{count}` videos post ho chuki hain...")
                        await asyncio.sleep(3) # Notification mode mein thoda gap zaroori hai
                except Exception as e:
                    print(f"Error: {e}")
                    continue
            
            await client.send_message(chat_id=dest, text="Done ✅")
            await status.edit(f"🏁 **Batch Complete!** `{count}` videos naye post ki tarah bhej di gayi hain.")
            
        except Exception as e: await message.reply_text(f"❌ Error: {e}")

app.run()
