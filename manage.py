import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
from telegram.utils.request import Request

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
bot_token = '7492960869:AAHByj6rrPEaJh1nEYT81pFjirg_hMfVdV4'  # Replace with your Telegram Bot Token

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Welcome to the GitHub Codespace Manager Bot!\n'
                              'Use /on <github_token> to manage your Codespaces.')

def on(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 1:
        update.message.reply_text('Usage: /on <github_token>')
        return

    github_token = context.args[0]
    headers = {'Authorization': f'token {github_token}'}
    response = requests.get(f'{GITHUB_API_BASE}/user/codespaces', headers=headers)

    if response.status_code == 200:
        codespaces = response.json()
        if not codespaces:
            update.message.reply_text('No Codespaces available.')
            return
            
        keyboard = []
        for codespace in codespaces:
            state = codespace['state']
            button_text = 'STOP' if state == 'active' else 'ON'
            keyboard.append([InlineKeyboardButton(f"{codespace['name']} ({state})", callback_data=f"{codespace['name']}:{button_text}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Select a Codespace:', reply_markup=reply_markup)
    else:
        update.message.reply_text('Failed to authenticate with GitHub. Check your token.')

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    # Retrieve the GitHub token from the context (session state not implemented here)
    github_token = context.args[0]  # In a real-world app, consider other ways to manage the token's state

    codespace_name, action = query.data.split(':')

    headers = {'Authorization': f'token {github_token}'}
    if action == 'STOP':
        response = requests.delete(f'{GITHUB_API_BASE}/user/codespaces/{codespace_name}', headers=headers)
        if response.status_code == 204:
            query.edit_message_text(text=f"Codespace {codespace_name} stopped.")
        else:
            query.edit_message_text(text=f"Failed to stop Codespace {codespace_name}.")
    else:  # action == 'ON'
        response = requests.post(f'{GITHUB_API_BASE}/codespaces/{codespace_name}/start', headers=headers)
        if response.status_code == 201:
            query.edit_message_text(text=f"Codespace {codespace_name} started.")
        else:
            query.edit_message_text(text=f"Failed to start Codespace {codespace_name}.")

def main() -> None:
    # Create a request queue
    request_queue = Request(
        con_pool_size=8,
        read_timeout=20,
        connect_timeout=15,
        use_fast_mode=True
    )

    # Create an Updater with the request queue
    updater = Updater(bot_token, request_queue=request_queue)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("on", on))
    dispatcher.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
