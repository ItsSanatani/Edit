from pyrogram import Client, filters
from pymongo import MongoClient
from config import config

# Bot Client Setup
bot = Client(
    "edit_guardian_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
)

# MongoDB Setup
mongo_client = MongoClient(config.MONGO_URI)
db = mongo_client["EditGuardian"]
logs = db["EditLogs"]
rules = db["GroupRules"]
auth_users = db["AuthorizedUsers"]

# /start command
@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("👋 Hello! I am **Edit Guardian & Moderation Bot**. I monitor edits and help with group moderation.")

# /help command
@bot.on_message(filters.command("help"))
async def help(client, message):
    await message.reply("⚙ **Available Commands:**\n"
                        "/auth - Authorize a user\n"
                        "/unauth - Unauthorize a user\n"
                        "/authusers - View authorized users\n"
                        "/delete - Delete a message\n"
                        "/purge - Delete multiple messages\n"
                        "/clearauthusers - Remove all authorized users\n"
                        "/logedits - Enable/Disable edit logging\n"
                        "/setfilter - Add a word to delete on edit\n"
                        "/warn - Warn a user\n"
                        "/ban - Ban a user after multiple warnings")

# **Edit Guardian Features**
@bot.on_message(filters.command("logedits"))
async def toggle_log(client, message):
    chat_id = message.chat.id
    current = rules.find_one({"chat_id": chat_id})
    if not current:
        rules.insert_one({"chat_id": chat_id, "log_edits": True})
        await message.reply("✅ **Edit Logging Enabled!**")
    else:
        new_status = not current["log_edits"]
        rules.update_one({"chat_id": chat_id}, {"$set": {"log_edits": new_status}})
        status_text = "Enabled" if new_status else "Disabled"
        await message.reply(f"🔄 **Edit Logging {status_text}!**")


@bot.on_message(filters.edited)
async def log_edits(client, message):
    chat_id = message.chat.id
    rule = rules.find_one({"chat_id": chat_id})
    
    if rule and rule.get("log_edits", False):
        logs.insert_one({
            "chat_id": chat_id,
            "user_id": message.from_user.id,
            "old_message": message.text or message.caption,
            "new_message": message.edit_date,
        })
        await message.reply(f"📌 **Edit Detected!**\n👤 User: {message.from_user.mention}\n📝 New Message: {message.text}")

@bot.on_message(filters.command("setfilter"))
async def set_filter(client, message):
    chat_id = message.chat.id
    if len(message.command) < 2:
        return await message.reply("❌ Please provide a word to filter.")
    
    word = message.command[1]
    rules.update_one({"chat_id": chat_id}, {"$addToSet": {"banned_words": word}}, upsert=True)
    await message.reply(f"✅ **Added Filtered Word:** `{word}`")

@bot.on_message(filters.update.edited_message)
async def auto_delete_edited(client, message):
    chat_id = message.chat.id
    rule = rules.find_one({"chat_id": chat_id})
    
    if rule and "banned_words" in rule:
        for word in rule["banned_words"]:
            if word.lower() in message.text.lower():
                await message.delete()
                await message.reply(f"🚫 **Message Deleted!** Reason: Contains `{word}`")
                return

@bot.on_message(filters.command("warn") & filters.reply)
async def warn_user(client, message):
    warned_user = message.reply_to_message.from_user
    chat_id = message.chat.id
    rules.update_one({"chat_id": chat_id}, {"$inc": {f"warns.{warned_user.id}": 1}}, upsert=True)
    count = rules.find_one({"chat_id": chat_id})["warns"].get(str(warned_user.id), 0)
    
    await message.reply(f"⚠️ **{warned_user.mention} has been warned!**\nTotal Warnings: {count}")

@bot.on_message(filters.command("ban") & filters.reply)
async def ban_user(client, message):
    user = message.reply_to_message.from_user
    chat_id = message.chat.id
    rules.update_one({"chat_id": chat_id}, {"$set": {f"warns.{user.id}": 0}})
    await bot.ban_chat_member(chat_id, user.id)
    await message.reply(f"🚨 **{user.mention} has been banned!**")

# **Admin Moderation Features**
@bot.on_message(filters.command("auth") & filters.reply)
async def auth_user(client, message):
    user_id = message.reply_to_message.from_user.id
    if not auth_users.find_one({"user_id": user_id}):
        auth_users.insert_one({"user_id": user_id})
        await message.reply(f"✅ **{user_id}** is now authorized!")
    else:
        await message.reply("⚠️ This user is already authorized.")

@bot.on_message(filters.command("unauth") & filters.reply)
async def unauth_user(client, message):
    user_id = message.reply_to_message.from_user.id
    if auth_users.find_one({"user_id": user_id}):
        auth_users.delete_one({"user_id": user_id})
        await message.reply(f"❌ **{user_id}** is now unauthorized!")
    else:
        await message.reply("⚠️ This user is already unauthorized.")

@bot.on_message(filters.command("authusers"))
async def list_auth_users(client, message):
    users = auth_users.find()
    user_list = [f"🆔 {user['user_id']}" for user in users]
    if user_list:
        await message.reply("✅ **Authorized Users:**\n" + "\n".join(user_list))
    else:
        await message.reply("❌ No users are authorized yet.")

@bot.on_message(filters.command(["delete", "del", "clean"]) & filters.reply)
async def delete_message(client, message):
    await message.reply_to_message.delete()
    await message.delete()

@bot.on_message(filters.command("purge") & filters.reply)
async def purge_messages(client, message):
    chat_id = message.chat.id
    msg_id = message.message_id
    async for msg in client.get_chat_history(chat_id, limit=100):
        if msg.message_id < msg_id:
            await msg.delete()
    await message.reply("🚀 **Purge Complete!**")

@bot.on_message(filters.command(["clearauthusers", "deleteauthusers", "rmauthusers"]))
async def clear_auth_users(client, message):
    auth_users.delete_many({})
    await message.reply("❌ All authorized users have been removed!")

# Run the bot
bot.run()
