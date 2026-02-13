# 🔥 Firebase APK Modifier & Extractor Bot

Telegram bot for modifying and extracting Firebase configurations from APK files.

## Features

🔍 **Extract Mode** - Extract Firebase config from APK
✏️ **Inject Mode** - Inject new Firebase config into APK

## Requirements

- Python 3.11+
- Java JDK 17+
- Telegram Bot Token

## Installation

### Local Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd <repo-name>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Update bot token in `firebase_apk_bot.py`:
```python
BOT_TOKEN = "your-bot-token-here"
```

4. Run the bot:
```bash
python firebase_apk_bot.py
```

### Railway Deployment

1. Fork this repository
2. Connect to Railway
3. Deploy automatically with Dockerfile

Railway will automatically:
- Install Python 3.11
- Install Java JDK
- Install dependencies
- Start the bot

## Usage

1. Start the bot: `/start`
2. Choose mode:
   - 🔍 Extract - Get Firebase config from APK
   - ✏️ Inject - Modify APK with new Firebase config
3. Send your APK file (max 50MB)
4. For Inject mode, provide Firebase details:
   - Database URL
   - API Key
   - App ID
   - Storage Bucket
   - Project ID

## Commands

- `/start` - Main menu
- `/extract` - Direct extract mode
- `/modify` - Direct inject mode
- `/help` - Help message

## Configuration

Edit `firebase_apk_bot.py` to configure:
- `BOT_TOKEN` - Your Telegram bot token
- `ADMIN_CHANNEL_ID` - Admin channel for notifications

## Files

- `firebase_apk_bot.py` - Main bot code
- `apktool.jar` - APK decompile/recompile tool
- `uber-apk-signer.jar` - APK signing tool
- `debug.keystore` - Debug keystore for signing
- `requirements.txt` - Python dependencies
- `Dockerfile` - Docker configuration
- `railway.toml` - Railway deployment config

## License

MIT License

## Support

For issues and questions, open an issue on GitHub.
