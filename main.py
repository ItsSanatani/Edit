from pyrogram import Client, filters
from pymongo import MongoClient
from config import config

# Bot client setup
bot = Client(
    "admin_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
)

# MongoDB setup
mongo_client = MongoClient(config.MONGO_URI)
db = mongo_client["AdminBot"]
auth_users = db["AuthorizedUsers"]

# /start command
@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("👋 Hello! I am an **Admin Moderation Bot**. Use /help to see available commands.")

# /help command
@bot.on_message(filters.command("help"))
async def help(client, message):
    await message.reply("⚙ **Available Commands:**\n"
                        "/auth - Authorize a user\n"
                        "/unauth - Unauthorize a user\n"
                        "/authusers - View authorized users\n"
                        "/delete - Delete a message\n"
                        "/purge - Delete multiple messages\n"
                        "/clearauthusers - Remove all authorized users")

# /auth - Authorize a user
@bot.on_message(filters.command("auth") & filters.reply)
async def auth_user(client, message):
    user_id = message.reply_to_message.from_user.id
    if not auth_users.find_one({"user_id": user_id}):
        auth_users.insert_one({"user_id": user_id})
        await message.reply(f"✅ **{user_id}** is now authorized!")
    else:
        await message.reply("⚠️ This user is already authorized.")

# /unauth - Unauthorize a user
@bot.on_message(filters.command("unauth") & filters.reply)
async def unauth_user(client, message):
    user_id = message.reply_to_message.from_user.id
    if auth_users.find_one({"user_id": user_id}):
        auth_users.delete_one({"user_id": user_id})
        await message.reply(f"❌ **{user_id}** is now unauthorized!")
    else:
        await message.reply("⚠️ This user is already unauthorized.")

# /authusers - List authorized users
@bot.on_message(filters.command("authusers"))
async def list_auth_users(client, message):
    users = auth_users.find()
    user_list = [f"🆔 {user['user_id']}" for user in users]
    if user_list:
        await message.reply("✅ **Authorized Users:**\n" + "\n".join(user_list))
    else:
        await message.reply("❌ No users are authorized yet.")

# /delete - Delete a specific message
@bot.on_message(filters.command(["delete", "del", "clean"]) & filters.reply)
async def delete_message(client, message):
    await message.reply_to_message.delete()
    await message.delete()

# /purge - Delete multiple messages
@bot.on_message(filters.command("purge") & filters.reply)
async def purge_messages(client, message):
    chat_id = message.chat.id
    msg_id = message.message_id
    async for msg in client.get_chat_history(chat_id, limit=100):
        if msg.message_id < msg_id:
            await msg.delete()
    await message.reply("🚀 **Purge Complete!**")

# /clearauthusers - Remove all authorized users
@bot.on_message(filters.command(["clearauthusers", "deleteauthusers", "rmauthusers"]))
async def clear_auth_users(client, message):
    auth_users.delete_many({})
    await message.reply("❌ All authorized users have been removed!")

# Run the bot
bot.run()
