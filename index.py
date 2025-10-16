import os
import json
from dotenv import load_dotenv
from telegram import (Update, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler, ContextTypes)

# Load environment variables - Render will set BOT_TOKEN as environment variable
load_dotenv("bot_1.env")
BOT_TOKEN = os.getenv("BOT_TOKEN") or os.environ.get('BOT_TOKEN')

# Ensure users.json exists and has proper content
def initialize_users_file():
    try:
        with open('users.json', 'r') as f:
            json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open('users.json', 'w') as f:
            json.dump({}, f)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Load users data
    try:
        with open('users.json', 'r') as f:
            users = json.load(f)
    except:
        users = {}
    
    # Track user if not exists
    if str(user_id) not in users:
        users[str(user_id)] = {
            "username": update.effective_user.username,
            "first_name": update.effective_user.first_name,
            "usage_count": 0
        }
    
    users[str(user_id)]["usage_count"] = users[str(user_id)].get("usage_count", 0) + 1
    
    # Save users data
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=2)
    
    keyboard = [
        [InlineKeyboardButton("🌐 Social Media Links", callback_data="social")],
        [InlineKeyboardButton("🤖 AI Tools", callback_data="ai")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Choose a section:", reply_markup=reply_markup)

# Handle button clicks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "social":
        keyboard = [
            [InlineKeyboardButton("📘 Facebook", url="https://facebook.com")],
            [InlineKeyboardButton("📱 Telegram", url="https://t.me")],
            [InlineKeyboardButton("💬 Messenger", url="https://messenger.com")],
            [InlineKeyboardButton("🐦 X (Twitter)", url="https://x.com")],
            [InlineKeyboardButton("💼 LinkedIn", url="https://linkedin.com")],
            [InlineKeyboardButton("📸 Instagram", url="https://instagram.com")],
            [InlineKeyboardButton("📞 WhatsApp", url="https://wa.me/")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Here are the social media links:", reply_markup=reply_markup)

    elif query.data == "ai":
        keyboard = [
            [InlineKeyboardButton("💡 ChatGPT", url="https://chat.openai.com/")],
            [InlineKeyboardButton("🧠 DeepSeek", url="https://chat.deepseek.com/")],
            [InlineKeyboardButton("🔮 Gemini", url="https://gemini.google.com/")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Explore AI tools:", reply_markup=reply_markup)

# Health check endpoint for Render
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')
    
    def log_message(self, format, *args):
        pass  # Suppress log messages

def run_health_server():
    server = HTTPServer(('0.0.0.0', 8080), HealthHandler)
    server.serve_forever()

# Main function
def main():
    # Initialize users file
    initialize_users_file()
    
    # Start health check server in a separate thread
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN not found. Please set it in environment variables.")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()