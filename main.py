import asyncio
from pyrogram import Client, filters
from config import Config

app = Client("forwarder_bot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)

# Heroku se Log Channel ID uthana
LOG_CHANNEL = Config.LOG_CHANNEL 

user_data = {}

# 1. Sabse Mast Start Menu
@app.on_message(filters.command("start") & filters.user(Config.OWNER_ID))
async def start_cmd(client, message):
    help_text = (
        "✨ **Forwarder Pro Bot Menu** ✨\n\n"
        "Bhai, ye rahi teri saari commands:\n\n"
        "🚀 `/batch` - Step-by-step videos forward karne ke liye.\n"
        "❌ `/cancel` - Chalte huye batch ko beech mein rokne ke liye.\n"
        "🎯 **ID Checker:** Kisi bhi channel ka message mujhe **Forward** karo, main uski ID bata dunga.\n\n"
        "⚙️ **Status:** Bot Online hai aur Log Channel linked hai!"
    )
    await message.reply_text(help_text)

# 2. ID Checker (Forwarded message se ID nikalne ke liye)
@app.on_message(filters.forwarded & filters.user(Config.OWNER_ID))
async def get_info(client, message):
    try:
        # Check if forward_from_chat is available
        if message.forward_from_chat:
            c_id = message.forward_from_chat.id
            m_id = message.forward_from_message_id
            await message.reply_text(f"🎯 **Data Mil Gaya!**\n\n📌 Channel ID: `{c_id}`\n📌 Message ID: `{m_id}`\n\nAb iska use `/batch` mein karo.")
        else:
            await message.reply_text("❌ Bhai, is message ki ID nahi nikal rahi. Shayad user ne privacy lagayi hai ya ye channel message nahi hai.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# 3. Interactive Batch Logic
@app.on_message(filters.command("batch") & filters.user(Config.OWNER_ID))
async def start_batch(client, message):
    user_data[message.from_user.id] = {"step": 1}
    await message.reply_text("📥 **Step 1:**\nSource aur Dest ID bhejo (Space dekar):\nExample: `-100123 -100456` ")

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
            await message.reply_text("🔢 **Step 2:**\nRange bhejo (Kha se kha tak):\nExample: `200 400` ")
        except: await message.reply_text("❌ IDs sahi format mein dalo (Example: -100123 -100456).")

    elif step == 2:
        try:
            range_ids = message.text.split(" ")
            start, end = int(range_ids[0]), int(range_ids[1])
            source, dest = user_data[user_id]["source"], user_data[user_id]["dest"]
            del user_data[user_id]
            
            status = await message.reply_text("🚀 **Forwarding Shuru...**")
            count = 0

            for m_id in range(start, end + 1):
                try:
                    msg = await client.get_messages(source, m_id)
                    # Sirf Video ya Document hi forward honge
                    if msg and (msg.video or msg.document):
                        file_id = msg.video.file_id if msg.video else msg.document.file_id
                        cap = msg.caption if msg.caption else ""

                        # Target Channel mein send karna (New post feel)
                        await client.send_video(chat_id=dest, video=file_id, caption=cap)
                        
                        # Log Channel mein copy bhejna
                        if LOG_CHANNEL:
                            try:
                                await client.send_video(chat_id=LOG_CHANNEL, video=file_id, caption=f"📂 Log: `{m_id}`\n\n{cap}")
                            except: pass
                        
                        count += 1
                        if count % 10 == 0:
                            await status.edit(f"🚀 `{count}` items bhej diye hain...")
                        await asyncio.sleep(3) 
                except: continue
            
            await client.send_message(chat_id=dest, text="Done ✅")
            await status.edit(f"🏁 **Batch Complete!**\nTotal `{count}` videos forward hui aur Log Channel mein copy bhi ho gayi.")
            
        except Exception as e: await message.reply_text(f"❌ Error: {e}")

# 4. Cancel Command
@app.on_message(filters.command("cancel") & filters.user(Config.OWNER_ID))
async def cancel_process(client, message):
    if message.from_user.id in user_data:
        del user_data[message.from_user.id]
        await message.reply_text("❌ Process cancel kar diya gaya hai.")
    else:
        await message.reply_text("Bhai, abhi koi process chal hi nahi raha.")

app.run()
