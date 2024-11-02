from pymongo import MongoClient
from config import DB_URI, DB_NAME
import logging

# Establish MongoDB connection
client = MongoClient(DB_URI)
db = client[DB_NAME]

# Define collections
users_collection = db["users"]
channels_collection = db["channels"]

# Configure logging
logger = logging.getLogger(__name__)

def save_user(user_id):
    """Save a user ID if it doesn't already exist in the database."""
    try:
        if not users_collection.find_one({"user_id": user_id}):
            users_collection.insert_one({"user_id": user_id})
            logger.info(f"User {user_id} added to the database.")
    except Exception as e:
        logger.error(f"Error saving user {user_id}: {e}")

def save_channel(channel_id, channel_name):
    """Save a channel ID and name if it doesn't already exist in the database."""
    try:
        if not channels_collection.find_one({"channel_id": channel_id}):
            channels_collection.insert_one({"channel_id": channel_id, "channel_name": channel_name})
            logger.info(f"Channel {channel_name} ({channel_id}) added to the database.")
        else:
            logger.info(f"Channel {channel_name} ({channel_id}) already exists in the database.")
    except Exception as e:
        logger.error(f"Error saving channel {channel_name} ({channel_id}): {e}")

def remove_channel(channel_id):
    """Remove a channel from the database by its ID."""
    try:
        result = channels_collection.delete_one({"channel_id": channel_id})
        if result.deleted_count > 0:
            logger.info(f"Channel ID {channel_id} removed from the database.")
            return True
        else:
            logger.warning(f"Channel ID {channel_id} not found in the database.")
            return False
    except Exception as e:
        logger.error(f"Error removing channel {channel_id}: {e}")
        return False

def get_total_users():
    """Return the total number of users in the database."""
    return users_collection.count_documents({})

def get_channels_list():
    """Return a list of all channels in the database, excluding the _id field."""
    return list(channels_collection.find({}, {"_id": 0}))  # Exclude the _id field

def get_channel_ids():
    """Return a list of all channel IDs from the database."""
    return [channel['channel_id'] for channel in channels_collection.find({}, {"_id": 0, "channel_id": 1})]
