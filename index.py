import os
import json
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from telegram import (Update, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters)

# Load environment variables - Render will set BOT_TOKEN as environment variable
load_dotenv("bot_1.env")
BOT_TOKEN = os.getenv("BOT_TOKEN") or os.environ.get('BOT_TOKEN')
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.environ.get('GEMINI_API_KEY')

# Configure Gemini AI
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Gemini configuration error: {e}")

# Ensure users.json exists and has proper content
def initialize_users_file():
    try:
        with open('users.json', 'r') as f:
            json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open('users.json', 'w') as f:
            json.dump({}, f)

# Ensure conversations.json exists
def initialize_conversations_file():
    try:
        with open('conversations.json', 'r') as f:
            json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open('conversations.json', 'w') as f:
            json.dump({}, f)

# Gemini API integration using official library
def chat_with_gemini(message, user_id):
    """Send message to Gemini API and get response using official library"""
    if not GEMINI_API_KEY:
        return "❌ Gemini API key not configured. Please contact the bot administrator."
    
    try:
        # Try different available models
        models_to_try = [
            'gemini-2.0-pro',    # Higher quality
        ]
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(message)
                
                if response.text:
                    return response.text
                else:
                    continue  # Try next model if no response
                    
            except Exception as model_error:
                print(f"Model {model_name} failed: {model_error}")
                continue  # Try next model
        
        # If all models failed, try the REST API as fallback
        return chat_with_gemini_fallback(message)
        
    except Exception as e:
        return f"❌ Error connecting to Gemini: {str(e)}"

# Fallback REST API method
def chat_with_gemini_fallback(message):
    """Fallback method using REST API"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": message
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response_data = response.json()
        
        if response.status_code == 200:
            if 'candidates' in response_data and len(response_data['candidates']) > 0:
                return response_data['candidates'][0]['content']['parts'][0]['text']
            else:
                return "🤖 Sorry, I couldn't generate a response. Please try again."
        else:
            error_msg = response_data.get('error', {}).get('message', 'Unknown error occurred')
            return f"❌ API Error: {error_msg}"
            
    except Exception as e:
        return f"❌ Connection Error: {str(e)}"

# Track user conversation state
def get_user_conversation(user_id):
    try:
        with open('conversations.json', 'r') as f:
            conversations = json.load(f)
        return conversations.get(str(user_id), {"active": False, "history": []})
    except:
        return {"active": False, "history": []}

def update_user_conversation(user_id, conversation_data):
    try:
        with open('conversations.json', 'r') as f:
            conversations = json.load(f)
    except:
        conversations = {}
    
    conversations[str(user_id)] = conversation_data
    
    with open('conversations.json', 'w') as f:
        json.dump(conversations, f, indent=2)

def end_user_conversation(user_id):
    try:
        with open('conversations.json', 'r') as f:
            conversations = json.load(f)
    except:
        conversations = {}
    
    if str(user_id) in conversations:
        conversations[str(user_id)]["active"] = False
    
    with open('conversations.json', 'w') as f:
        json.dump(conversations, f, indent=2)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # End any active conversation
    end_user_conversation(user_id)
    
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
    
    welcome_text = """
🤖 **Welcome to AI Assistant Bot!**

Choose from the options below to get started:

• **Social Media Links** - Connect with us on various platforms
• **AI Tools** - Access powerful AI assistants including Gemini

Use /stop at any time to end ongoing conversations.
    """
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

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
            [InlineKeyboardButton("📞 WhatsApp", url="https://wa.me/")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="start_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🌐 **Social Media Links**\n\nConnect with us on these platforms:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    elif query.data == "ai":
        keyboard = [
            [InlineKeyboardButton("💡 ChatGPT", url="https://chat.openai.com/")],
            [InlineKeyboardButton("🧠 DeepSeek", url="https://chat.deepseek.com/")],
            [InlineKeyboardButton("🔮 Gemini", callback_data="gemini_options")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="start_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🤖 **AI Tools**\n\nExplore these powerful AI assistants:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    elif query.data == "gemini_options":
        keyboard = [
            [InlineKeyboardButton("💬 Chat in Telegram", callback_data="gemini_chat")],
            [InlineKeyboardButton("🔗 Open Gemini Website", url="https://gemini.google.com/")],
            [InlineKeyboardButton("🔙 Back to AI Tools", callback_data="ai")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🔮 **Gemini AI Options**\n\nChoose how you want to use Google's Gemini AI:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    elif query.data == "gemini_chat":
        user_id = query.from_user.id
        conversation = get_user_conversation(user_id)
        conversation["active"] = True
        update_user_conversation(user_id, conversation)
        
        keyboard = [
            [InlineKeyboardButton("❌ End Chat", callback_data="end_gemini_chat")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if not GEMINI_API_KEY:
            await query.edit_message_text(
                "❌ **Gemini API Not Configured**\n\n"
                "The Gemini chat feature is currently unavailable. "
                "Please contact the administrator to set up the API key.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
        
        await query.edit_message_text(
            "🤖 **Gemini Chat Started!**\n\n"
            "You can now chat with Gemini AI directly here! ✨\n\n"
            "**Features:**\n"
            "• Ask questions on any topic\n"
            "• Get help with writing and coding\n"
            "• Have conversations in multiple languages\n\n"
            "Type /stop or use the button below to end the chat.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    elif query.data == "end_gemini_chat":
        user_id = query.from_user.id
        end_user_conversation(user_id)
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="start_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "✅ **Gemini chat ended!**\n\nThank you for chatting with Gemini AI!",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    elif query.data == "start_main":
        user_id = query.from_user.id
        end_user_conversation(user_id)
        
        keyboard = [
            [InlineKeyboardButton("🌐 Social Media Links", callback_data="social")],
            [InlineKeyboardButton("🤖 AI Tools", callback_data="ai")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🤖 **Welcome back!**\n\nChoose a section to continue:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

# Handle regular messages for Gemini chat
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # Check if user is in active Gemini conversation
    conversation = get_user_conversation(user_id)
    
    if conversation.get("active"):
        # Send typing action
        await update.message.chat.send_action(action="typing")
        
        # Get response from Gemini
        gemini_response = chat_with_gemini(message_text, user_id)
        
        # Update conversation history
        conversation["history"].append({
            "user": message_text,
            "assistant": gemini_response
        })
        update_user_conversation(user_id, conversation)
        
        # Send response (split long messages)
        if len(gemini_response) > 4096:
            for i in range(0, len(gemini_response), 4096):
                await update.message.reply_text(gemini_response[i:i+4096])
        else:
            await update.message.reply_text(gemini_response)

# Stop command to end Gemini chat
async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    end_user_conversation(user_id)
    
    await update.message.reply_text(
        "✅ **Gemini chat ended!**\n\nUse /start to explore other features.",
        parse_mode="Markdown"
    )

# Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 **Bot Help Guide**

**Available Commands:**
/start - Start the bot and show main menu
/stop - End active Gemini chat
/help - Show this help message

**Features:**
• Social Media Links - Connect on various platforms
• AI Tools - Access different AI assistants
• Gemini Chat - Chat directly with Google's Gemini AI

**Tips:**
• Use the inline buttons for navigation
• Gemini can help with questions, writing, coding, and more
• Long responses are automatically split into multiple messages
    """
    await update.message.reply_text(help_text, parse_mode="Markdown")

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
    # Initialize files
    initialize_users_file()
    initialize_conversations_file()
    
    # Start health check server in a separate thread
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN not found. Please set it in environment variables.")
        return
    
    # Check Gemini API key
    if not GEMINI_API_KEY:
        print("⚠️  Warning: GEMINI_API_KEY not found. Gemini features will not work.")
    else:
        print("✅ Gemini API key loaded successfully")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop_chat))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

