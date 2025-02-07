from datetime import datetime, timedelta
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Define stages in the conversation
DATE, CATEGORY, SUBCATEGORY, AMOUNT, DESCRIPTION = range(5)

# Store data for the transaction
user_data = {}

# Function to get today's date and yesterday's date
def get_date_string(days_offset=0):
    return (datetime.today() + timedelta(days=days_offset)).strftime('%Y-%m-%d')

# Start the transaction flow
def start(update: Update, context: CallbackContext) -> int:
    # print("Received /addtransaction command")
    update.message.reply_text(
        "Please select a date for the transaction:",
        reply_markup=ReplyKeyboardMarkup([
            ['Today', 'Yesterday', 'Enter Date']
        ], one_time_keyboard=True)
    )
    return DATE

# Handle the date selection
def date_selection(update: Update, context: CallbackContext) -> int:
    user_choice = update.message.text
    today_date = get_date_string()  # Get today's date
    
    if user_choice == 'Today':
        user_data[update.message.from_user.id] = {'date': today_date}
        update.message.reply_text(f"Selected Date: {today_date}. Now, please select a category to add a transaction.",
                                  reply_markup=ReplyKeyboardMarkup([
                                      ['Grocery', 'Vehicle', 'Utilities', 'Home'],
                                      ['Mehdi', 'Elaheh', 'Sana', 'Sameen']
                                  ], one_time_keyboard=True))
        return CATEGORY
    
    elif user_choice == 'Yesterday':
        yesterday_date = get_date_string(-1)  # Get yesterday's date
        user_data[update.message.from_user.id] = {'date': yesterday_date}
        update.message.reply_text(f"Selected Date: {yesterday_date}. Now, please select a category to add a transaction.",
                                  reply_markup=ReplyKeyboardMarkup([
                                      ['Grocery', 'Vehicle', 'Utilities', 'Home'],
                                      ['Mehdi', 'Elaheh', 'Sana', 'Sameen']
                                  ], one_time_keyboard=True))
        return CATEGORY

    elif user_choice == 'Enter Date':
        update.message.reply_text(
            "Please enter the date in the format 'DD MM YYYY' (e.g., 06 02 2025). The default is today's date, which is {today_date}.",
            reply_markup=ReplyKeyboardMarkup([['Cancel']], one_time_keyboard=True)
        )
        return CATEGORY

# Handle custom date input
def custom_date(update: Update, context: CallbackContext) -> int:
    try:
        # Try to parse the date in the format 'DD MM YYYY'
        date_str = update.message.text.strip()
        custom_date = datetime.strptime(date_str, '%d %m %Y').strftime('%Y-%m-%d')
        user_data[update.message.from_user.id]['date'] = custom_date
        update.message.reply_text(f"Selected Date: {custom_date}. Now, please select a category to add a transaction.",
                                  reply_markup=ReplyKeyboardMarkup([
                                      ['Grocery', 'Vehicle', 'Utilities', 'Home'],
                                      ['Mehdi', 'Elaheh', 'Sana', 'Sameen']
                                  ], one_time_keyboard=True))
        return CATEGORY
    except ValueError:
        update.message.reply_text("Invalid date format. Please try again in the format 'DD MM YYYY'.")
        return CATEGORY

# Handle category selection
def category(update: Update, context: CallbackContext) -> int:
    selected_category = update.message.text
    user_data[update.message.from_user.id]['category'] = selected_category
    
    categories = {
        'Grocery': None,
        'Utilities': ['Gas', 'Electricity', 'Others'],
        'Vehicle': ['Gas', 'Financial', 'Maintenance'],
        'Home': ['Rent', 'Other'],
        'Mehdi': ['Cloth', 'Other'],
        'Elaheh': ['Cloth', 'Other'],
        'Sana': ['Cloth', 'Other'],
        'Sameen': ['Cloth', 'Other']
    }

    subcategories = categories.get(selected_category, None)
    
    if subcategories:
        user_data[update.message.from_user.id]['subcategory'] = subcategories
        update.message.reply_text(
            f"Select a subcategory under {selected_category}:",
            reply_markup=ReplyKeyboardMarkup([[x] for x in subcategories], one_time_keyboard=True)
        )
        return SUBCATEGORY
    else:
        update.message.reply_text(f"Please enter the amount and description for {selected_category}:")
        return AMOUNT

# Handle subcategory selection
def subcategory(update: Update, context: CallbackContext) -> int:
    selected_subcategory = update.message.text
    user_data[update.message.from_user.id]['subcategory'] = selected_subcategory
    update.message.reply_text("Please enter the amount for this transaction:")
    return AMOUNT

# Handle amount input
def amount(update: Update, context: CallbackContext) -> int:
    user_data[update.message.from_user.id]['amount'] = update.message.text
    update.message.reply_text("Please enter a description for this transaction:")
    return DESCRIPTION

# Handle description input
def description(update: Update, context: CallbackContext) -> int:
    user_data[update.message.from_user.id]['description'] = update.message.text
    update.message.reply_text("Your transaction has been recorded. Would you like to submit it?",
                                 reply_markup=ReplyKeyboardMarkup([['Submit']], one_time_keyboard=True))
    return ConversationHandler.END

# Handle submission of the transaction
def submit(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in user_data:
        transaction = user_data[user_id]
        category = transaction.get('category')
        subcategory = transaction.get('subcategory')
        amount = transaction.get('amount')
        description = transaction.get('description')
        date = transaction.get('date')
        message = f"Transaction: {date} - {category} - {subcategory} - {amount} - {description}"
        update.message.reply_text(message)

        # Clear the stored data after submission
        del user_data[user_id]


def unknown(update: Update, context: CallbackContext):
    print(f"Received message: {update.message.text}")  # Debugging
    update.message.reply_text("I didn't understand that command.")

# Start the bot and register handlers
def main() -> None:
    updater = Updater("7183125146:AAHEbAkYWDOCfcKof3m-PWDxDMNaYqP5z6c", use_context=True)
    dp = updater.dispatcher
    
    # Define conversation handler with /addtransaction as entry point
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            DATE: [MessageHandler(Filters.text, date_selection)],
            CATEGORY: [MessageHandler(Filters.text, category)],
            SUBCATEGORY: [MessageHandler(Filters.text, subcategory)],
            AMOUNT: [MessageHandler(Filters.text & ~Filters.command, amount)],
            DESCRIPTION: [MessageHandler(Filters.text & ~Filters.command, description)],
        },
        fallbacks=[MessageHandler(Filters.text & ~Filters.command, submit)],
    )

    dp.add_handler(conversation_handler)
    dp.add_handler(MessageHandler(Filters.regex('^Submit$'), submit))  # Submit button handler
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, unknown))


    updater.start_polling()
    updater.idle()



if __name__ == '__main__':
    main()