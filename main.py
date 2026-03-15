import asyncio
from pyrogram import Client, filters
from config import Config

app = Client("forwarder_bot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)

# Heroku ke Config Vars se Log Channel ID uthana
LOG_CHANNEL = Config.LOG_CHANNEL 

user_data = {}

@app.on_message(filters.command("start") & filters.user(Config.OWNER_ID))
async def start_cmd(client, message):
    await message.reply_text("👋 **Forwarder Pro + Auto-Log Ready!**\n\nAb har forward hone wali video ki ek copy tere Log Channel mein bhi jayegi.")

@app.on_message(filters.command("batch") & filters.user(Config.OWNER_ID))
async def start_batch(client, message):
    user_data[message.from_user.id] = {"step": 1}
    await message.reply_text("📥 **Step 1:** Source aur Dest ID bhejo:\n`-100Source -100Dest` ")

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
            await message.reply_text("🔢 **Step 2:** Message Range bhejo:\n`200 400` ")
        except: await message.reply_text("❌ Sahi format mein IDs dalo (Space dekar).")

    elif step == 2:
        try:
            range_ids = message.text.split(" ")
            start, end = int(range_ids[0]), int(range_ids[1])
            source, dest = user_data[user_id]["source"], user_data[user_id]["dest"]
            del user_data[user_id]
            
            status = await message.reply_text("🚀 **Forwarding with Auto-Logging...**")
            count = 0

            for m_id in range(start, end + 1):
                try:
                    msg = await client.get_messages(source, m_id)
                    if msg and (msg.video or msg.document):
                        file_id = msg.video.file_id if msg.video else msg.document.file_id
                        cap = msg.caption if msg.caption else ""

                        # 1. Target Channel mein bhejna
                        await client.send_video(chat_id=dest, video=file_id, caption=cap)
                        
                        # 2. Log Channel mein Copy bhejna (Heroku ID se)
                        if LOG_CHANNEL:
                            try:
                                await client.send_video(
                                    chat_id=LOG_CHANNEL, 
                                    video=file_id, 
                                    caption=f"📂 **Log Record**\n📌 From ID: `{m_id}`\n\n{cap}"
                                )
                            except: pass
                        
                        count += 1
                        if count % 10 == 0:
                            await status.edit(f"🚀 `{count}` items dono jagah bhej diye hain...")
                        await asyncio.sleep(3) # Safe delay
                except: continue
            
            await client.send_message(chat_id=dest, text="Done ✅")
            if LOG_CHANNEL:
                await client.send_message(chat_id=LOG_CHANNEL, text=f"🏁 **Batch Finished!** Total `{count}` videos logged.")
            
            await status.edit(f"🏁 **Kaam Ho Gaya!** Total `{count}` videos forward aur log ho gayi hain.")
            
        except Exception as e: await message.reply_text(f"❌ Error: {e}")

app.run()
                            
