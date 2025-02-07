from datetime import datetime, timedelta
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Define stages in the conversation
DATE, CATEGORY, SUBCATEGORY, AMOUNT, DESCRIPTION, CONFIRMATION = range(6)

# Store data for the transaction
user_data = {}

def get_date_string(days_offset=0):
    return (datetime.today() + timedelta(days=days_offset)).strftime('%Y-%m-%d')

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Please select a date for the transaction:",
        reply_markup=ReplyKeyboardMarkup([
            ['Today', 'Yesterday', 'Enter Date']
        ], one_time_keyboard=True)
    )
    return DATE

def date_selection(update: Update, context: CallbackContext) -> int:
    user_choice = update.message.text
    today_date = get_date_string()
    
    if user_choice == 'Today':
        user_data[update.message.from_user.id] = {'date': today_date}
    elif user_choice == 'Yesterday':
        user_data[update.message.from_user.id] = {'date': get_date_string(-1)}
    elif user_choice == 'Enter Date':
        update.message.reply_text("Please enter the date in the format 'DD MM YYYY' (e.g., 06 02 2025).", 
                                  reply_markup=ReplyKeyboardMarkup([['Cancel']], one_time_keyboard=True))
        return DATE
    
    update.message.reply_text("Now, please select a category:",
                              reply_markup=ReplyKeyboardMarkup([
                                  ['Grocery', 'Vehicle', 'Utilities', 'Home'],
                                  ['Mehdi', 'Elaheh', 'Sana', 'Sameen']
                              ], one_time_keyboard=True))
    return CATEGORY

def custom_date(update: Update, context: CallbackContext) -> int:
    try:
        date_str = update.message.text.strip()
        custom_date = datetime.strptime(date_str, '%d %m %Y').strftime('%Y-%m-%d')
        user_data[update.message.from_user.id]['date'] = custom_date
        update.message.reply_text("Now, please select a category:",
                                  reply_markup=ReplyKeyboardMarkup([
                                      ['Grocery', 'Vehicle', 'Utilities', 'Home'],
                                      ['Mehdi', 'Elaheh', 'Sana', 'Sameen']
                                  ], one_time_keyboard=True))
        return CATEGORY
    except ValueError:
        update.message.reply_text("Invalid date format. Please enter the date in 'DD MM YYYY' format.")
        return DATE

def category(update: Update, context: CallbackContext) -> int:
    selected_category = update.message.text
    user_data[update.message.from_user.id]['category'] = selected_category
    
    subcategories = {
        'Grocery': None,
        'Utilities': ['Gas', 'Electricity', 'Others'],
        'Vehicle': ['Gas', 'Financial', 'Maintenance'],
        'Home': ['Rent', 'Other'],
        'Mehdi': ['Cloth', 'Other'],
        'Elaheh': ['Cloth', 'Other'],
        'Sana': ['Cloth', 'Other'],
        'Sameen': ['Cloth', 'Other']
    }
    
    if selected_category in subcategories and subcategories[selected_category]:
        update.message.reply_text("Select a subcategory:",
                                  reply_markup=ReplyKeyboardMarkup(
                                      [[x] for x in subcategories[selected_category]], one_time_keyboard=True))
        return SUBCATEGORY
    else:
        update.message.reply_text("Please enter the amount:")
        return AMOUNT

def subcategory(update: Update, context: CallbackContext) -> int:
    user_data[update.message.from_user.id]['subcategory'] = update.message.text
    update.message.reply_text("Please enter the amount:")
    return AMOUNT

def amount(update: Update, context: CallbackContext) -> int:
    user_data[update.message.from_user.id]['amount'] = update.message.text
    update.message.reply_text("Please enter a description:")
    return DESCRIPTION

def description(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    user_data[user_id]['description'] = update.message.text
    
    date = user_data[user_id]['date']
    category = user_data[user_id]['category']
    subcategory = user_data[user_id].get('subcategory', 'N/A')
    amount = user_data[user_id]['amount']
    description = user_data[user_id]['description']
    
    confirmation_message = f"This is your record: {date} - {category} - {subcategory} - {amount} - {description}. Do you want to submit it?"
    update.message.reply_text(confirmation_message, 
                              reply_markup=ReplyKeyboardMarkup([['Submit', 'Cancel']], one_time_keyboard=True))
    return CONFIRMATION

def submit(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    if user_id in user_data:
        transaction = user_data[user_id]
        message = f"Submitted: {transaction['date']} - {transaction['category']} - {transaction.get('subcategory', 'N/A')} - {transaction['amount']} - {transaction['description']}"
        update.message.reply_text(message)
        del user_data[user_id]
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    if user_id in user_data:
        del user_data[user_id]
    update.message.reply_text("Your record is canceled.")
    return ConversationHandler.END

def unknown(update: Update, context: CallbackContext):
    update.message.reply_text("I didn't understand that command.")

def main() -> None:
    updater = Updater("7183125146:AAHEbAkYWDOCfcKof3m-PWDxDMNaYqP5z6c", use_context=True)
    dp = updater.dispatcher
    
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            DATE: [MessageHandler(Filters.text, date_selection)],
            CATEGORY: [MessageHandler(Filters.text, category)],
            SUBCATEGORY: [MessageHandler(Filters.text, subcategory)],
            AMOUNT: [MessageHandler(Filters.text & ~Filters.command, amount)],
            DESCRIPTION: [MessageHandler(Filters.text & ~Filters.command, description)],
            CONFIRMATION: [
                MessageHandler(Filters.regex('^Submit$'), submit),
                MessageHandler(Filters.regex('^Cancel$'), cancel)
            ]
        },
        fallbacks=[MessageHandler(Filters.text & ~Filters.command, unknown)],
    )

    dp.add_handler(conversation_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
