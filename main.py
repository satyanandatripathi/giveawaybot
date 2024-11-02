import logging, time, asyncio
from pyrogram import Client, filters
from pyrogram.errors import RPCError, FloodWait, InputUserDeactivated, UserIsBlocked
from pymongo import MongoClient
from config import API_ID, API_HASH, BOT_TOKEN, DB_URI, DB_NAME, ADMIN_IDS
from db import (
    save_channel,
    remove_channel,
    get_channel_ids,
    save_user,
    get_total_users,
    get_channels_list
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize bot client
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# MongoDB client initialization
mongo_client = MongoClient(DB_URI)
db = mongo_client[DB_NAME]

# Define collections
users_collection = db["users"]
channels_collection = db["channels"]

# Start command handler
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    save_user(message.from_user.id)  # Save user in the database
    await message.reply("Hello! Send any message, and I'll forward it to all channels upon /send command.")
    logger.info(f"User {message.from_user.id} started the bot.")

# Admin-only: Retrieve total users
@app.on_message(filters.command("users") & filters.user(ADMIN_IDS) & filters.private)
async def get_users_count(client, message):
    total_users = get_total_users()  # Get total users from the database
    await message.reply(f"Total Users: {total_users}")
    logger.info(f"Admin {message.from_user.id} requested total user count: {total_users}")

# Admin-only: Retrieve list of channels
@app.on_message(filters.command("channels") & filters.user(ADMIN_IDS) & filters.private)
async def get_channels_info(client, message):
    channels = get_channels_list()  # Get list of channels from the database
    if not channels:
        await message.reply("No channels in the database.")
        logger.info("Admin requested channel list, but no channels found.")
    else:
        channels_info = "\n".join(f"{channel['channel_id']} - {channel['channel_name']}" for channel in channels)
        await message.reply(channels_info)
        logger.info(f"Admin {message.from_user.id} requested channel list.")

@app.on_message(filters.command("add"))
async def add_channel_command(client, message):
    """Add the current channel to the database."""
    channel_id = str(message.chat.id)
    channel_name = message.chat.title if message.chat.title else "Unknown Channel"

    # Check if the channel is already in the database
    if channels_collection.find_one({"channel_id": channel_id}):
        await message.reply(f"The channel {channel_name} ({channel_id}) is already in the database.")
        await message.delete()  # Delete the command message
        return

    # Add channel to the database
    save_channel(channel_id, channel_name)
    await message.reply("Channel successfully added!")

    # Inform the admin about the new channel
    for admin_id in ADMIN_IDS:
        await client.send_message(chat_id=admin_id, text=f"New channel added: {channel_name} ({channel_id}) by user {message.from_user.id}.")

    logger.info(f"Channel {channel_name} ({channel_id}) added by user {message.from_user.id}.")
    await message.delete()  # Delete the command message


@app.on_message(filters.command("rem"))
async def remove_channel_command(client, message):
    """Remove the current channel from the database."""
    channel_id = str(message.chat.id)

    # Remove channel from the database
    if remove_channel(channel_id):
        await message.reply("Channel successfully removed!")

        # Inform the admin about the removed channel
        for admin_id in ADMIN_IDS:
            await client.send_message(chat_id=admin_id, text=f"Channel removed: {channel_id} by user {message.from_user.id}.")
        
        logger.info(f"Channel {channel_id} removed by user {message.from_user.id}.")
    else:
        await message.reply("Channel not found in the database.")
        logger.warning(f"Attempt to remove non-existent channel {channel_id} by user {message.from_user.id}.")
    
    await message.delete()  # Delete the command message

# Forwarding messages without the "forwarded" tag
@app.on_message(filters.reply & filters.command("send") & filters.user(ADMIN_IDS))
async def forward_without_tag(client, message):
    original_message = message.reply_to_message  # Get the original message being replied to

    # Retrieve channel IDs from the database
    channel_ids = get_channel_ids()  # Use the function to get channel IDs from the database

    success_count = 0
    error_count = 0
    error_channels = []  # To keep track of channels with errors

    for channel_id in channel_ids:
        try:
            if original_message.text:
                await client.send_message(chat_id=channel_id, text=original_message.text)
            elif original_message.photo:
                await client.send_photo(chat_id=channel_id, photo=original_message.photo.file_id, caption=original_message.caption)
            elif original_message.video:
                await client.send_video(chat_id=channel_id, video=original_message.video.file_id, caption=original_message.caption)
            elif original_message.document:
                await client.send_document(chat_id=channel_id, document=original_message.document.file_id, caption=original_message.caption)
            # Increment success count for successful sends
            success_count += 1
        except Exception as e:
            error_count += 1
            logger.error(f"Failed to send message to {channel_id}: {e}")
            error_channels.append(channel_id)

            # Check for permission error
            if "Forbidden" in str(e):  # Typical error message for permission issues
                remove_channel(channel_id)  # Remove channel from the database
                logger.warning(f"Removed channel {channel_id} due to permission error.")

    # Prepare success and error messages
    success_message = f"Message successfully sent to {success_count} channels."
    error_message = f"Failed to send to {error_count} channels."
    
    await message.reply(f"{success_message}\n{error_message}")
    logger.info(f"Message sent to channels: {success_count}, Errors: {error_count}")


@app.on_message(filters.command("broadcast") & filters.user(ADMIN_IDS))
async def send_message(client, message):
    if message.reply_to_message:
        replied_message = message.reply_to_message

        success_count = 0
        error_count = 0
        messages_sent_since_last_short_wait = 0
        messages_sent_since_last_long_wait = 0

        # Get all user IDs from the database
        user_ids = [user["user_id"] for user in users_collection.find({}, {"_id": 0, "user_id": 1})]

        processing_message = await message.reply_text("Broadcast in progress...")

        last_progress_text = ""
        last_update_time = time.time()  # Store the time of the last update

        for user_id in user_ids:
            try:
                if replied_message.text:
                    await client.send_message(user_id, replied_message.text)
                elif replied_message.photo:
                    await client.send_photo(user_id, photo=replied_message.photo.file_id, caption=replied_message.caption)
                else:
                    pass

                success_count += 1
                messages_sent_since_last_short_wait += 1
                messages_sent_since_last_long_wait += 1

                # Short wait every 100 messages
                if messages_sent_since_last_short_wait >= 100:
                    await asyncio.sleep(5)
                    messages_sent_since_last_short_wait = 0

                # Long wait every 1000 messages
                if messages_sent_since_last_long_wait >= 1000:
                    await asyncio.sleep(60)
                    messages_sent_since_last_long_wait = 0

            except FloodWait as e:
                print(f"FloodWait: Waiting for {e.x} seconds.")
                await asyncio.sleep(e.x)
                messages_sent_since_last_short_wait = 0
                messages_sent_since_last_long_wait = 0

            except InputUserDeactivated:
                print(f"User {user_id} has been deleted/deactivated. Removing from database...")
                users_collection.delete_one({"user_id": user_id})  # Remove user from the database
                error_count += 1

            except UserIsBlocked:
                print(f"User {user_id} has blocked the bot. Removing from database...")
                users_collection.delete_one({"user_id": user_id})  # Remove user from the database
                error_count += 1

            except Exception as e:
                print(f"Failed to send message to user {user_id}: {str(e)}")
                error_count += 1

            # Update the processing message with current progress if at least 2 minutes have passed
            current_time = time.time()
            if current_time - last_update_time >= 120:
                progress_text = f"Broadcast in progress...\nSuccessfully sent to {success_count} users with {error_count} errors."
                if progress_text != last_progress_text:
                    await processing_message.edit_text(progress_text)
                    last_progress_text = progress_text
                    last_update_time = current_time

        # Final summary message
        success_text = f"**Message successfully sent to {success_count} users.**" if success_count > 0 else "**No users were sent the message.**"
        error_text = f"**Failed to send message to {error_count} users.**" if error_count > 0 else "**All messages sent successfully.**"
        await message.reply_text(success_text + "\n" + error_text)

# Run the bot
logger.info("[+] BOT STARTED")
if __name__ == "__main__":
    app.run()
