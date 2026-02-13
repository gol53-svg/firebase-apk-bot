# 🚀 GitHub & Railway Deployment Guide

## Step 1: GitHub Repository Setup

### Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `firebase-apk-bot` (ya koi bhi naam)
3. Description: "Telegram bot for Firebase APK modification"
4. Keep it **Public** or **Private** (your choice)
5. **DO NOT** initialize with README (already hai)
6. Click "Create repository"

### Push Code to GitHub

GitHub pe repository banne ke baad ye commands run karo:

```bash
git remote add origin https://github.com/YOUR_USERNAME/firebase-apk-bot.git
git branch -M main
git push -u origin main
```

**Replace `YOUR_USERNAME`** with your GitHub username!

## Step 2: Railway Deployment

### Connect Railway to GitHub

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `firebase-apk-bot` repository
5. Railway automatically detect karega Dockerfile
6. Click "Deploy"

### Railway Environment Variables (Optional)

Agar bot token environment variable se lena hai:

1. Railway dashboard → Variables tab
2. Add variable:
   - Key: `BOT_TOKEN`
   - Value: `your-telegram-bot-token`

3. Update `firebase_apk_bot.py`:
```python
import os
BOT_TOKEN = os.getenv("BOT_TOKEN", "8442989333:AAHKTjaacGUl0MOAaOJ4ae0zGd7tFI8_-dA")
```

## Step 3: Verify Deployment

### Check Railway Logs

1. Railway dashboard → Deployments
2. Click on latest deployment
3. Check "Deploy Logs" tab
4. Look for:
   - ✅ "openjdk version" (Java installed)
   - ✅ "Starting Container"
   - ✅ Bot running message

### Test Bot

1. Open Telegram
2. Search your bot
3. Send `/start`
4. Test Extract or Inject mode

## Troubleshooting

### Java Not Found Error

If you still see "Java not found":
1. Check Railway Build Logs
2. Verify Dockerfile is being used
3. Check for "Installing Java" in logs

### Bot Not Responding

1. Check bot token is correct
2. Verify Railway deployment is "Active"
3. Check Deploy Logs for errors

### APK Processing Fails

1. Check APK size (max 50MB recommended)
2. Verify Java is installed (check logs)
3. Check disk space on Railway

## Files Structure

```
.
├── .dockerignore          # Docker ignore file
├── .gitignore            # Git ignore file
├── Dockerfile            # Docker configuration
├── railway.toml          # Railway configuration
├── README.md             # Project documentation
├── DEPLOYMENT_GUIDE.md   # This file
├── requirements.txt      # Python dependencies
├── firebase_apk_bot.py   # Main bot code
├── apktool.jar          # APK tool
├── uber-apk-signer.jar  # APK signer
├── debug.keystore       # Signing keystore
└── BOT_FEATURES.md      # Features documentation
```

## Important Notes

⚠️ **Bot Token Security**
- Never commit bot token to public repositories
- Use environment variables for sensitive data
- Update token in code or use Railway variables

⚠️ **Railway Free Tier**
- 500 hours/month free
- $5 credit for new users
- Bot will sleep after inactivity

⚠️ **APK Size Limits**
- Recommended: < 15MB (fast processing)
- Maximum: 50MB (slower processing)
- Large APKs may timeout

## Support

Issues? Check:
1. Railway Deploy Logs
2. GitHub Issues
3. Bot error messages

Happy Deploying! 🚀
