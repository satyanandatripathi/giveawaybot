# Giveaway Helper Telegram Bot

A powerful bot to manage giveaways, broadcast messages, and easily maintain channel and user data!

## 🔧 Required Variables
- **`BOT_TOKEN`**: Create a bot using [@BotFather](https://t.me/BotFather) and get the API token.
- **`API_ID`**: Obtain this value from [my.telegram.org](https://my.telegram.org).
- **`API_HASH`**: Obtain this value from [my.telegram.org](https://my.telegram.org).
- **`DB_URI`**: The MongoDB URI to connect your bot to the database.
- **`DB_NAME`**: Name of your MongoDB database.
- **`ADMIN_IDS`**: A list of Telegram user IDs of the bot's administrators who will have access to admin-only commands.

## 🔄 Optional Variables
- **`SUPPORT_GROUP`**: Link to your support Telegram group.
- **`UPDATES_CHANNEL`**: Link to your updates Telegram channel.

## 🌟 Features
- **Channel Management**: 
  - Add and remove channels with simple commands. Supports both private and public channels.
  - Automatic removal of inaccessible channels during broadcasts to keep the database clean and updated.
  
- **Message Broadcasting**:
  - Broadcast messages to all users and channels.
  - Efficient handling of blocked or inaccessible users and channels with auto-removal from the database.

- **User Tracking**:
  - Automatically track users who start the bot.
  - Remove inactive or blocked users to maintain an active user base.

- **Admin Notifications**:
  - Sends notifications to admins when a channel is added or removed, keeping admins in the loop about the bot's status and actions.

## 🛠 Setup Instructions
1. **Clone the Repository**: Clone the repository to your local environment.
2. **Set Environment Variables**: Add required variables in a `.env` file or set them directly in your environment.
3. **Run the Bot**: Start the bot by executing:
   ```bash
   python main.py
## 📚 Commands

### User Commands
- **`/start`**: Start the bot and track the user.
- **`/add`**: Add the current channel or group to the database.
- **`/rem`**: Remove the current channel or group from the database.

### Admin Commands
- **`/users`**: View the total user count.
- **`/channels`**: View the list of all channels with their names and invite links.
- **`/broadcast`**: Broadcast a message to all users. Use this by replying to a message with the `/broadcast` command.
- **`/send`**: Forward a specific message to all channels in the database. Use by replying to a message with `/send`.
