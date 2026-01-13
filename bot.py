import os
import json
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pydantic import BaseModel, Field
from google import genai
from google.genai.types import GenerateContentConfig
import genanki

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
ANKI_DECK_NAME = os.getenv('ANKI_DECK_NAME', 'German Words')
ANKI_MODEL_NAME = os.getenv('ANKI_MODEL_NAME', 'German Word Learning')

# Parse allowed user IDs from environment variable (comma-separated)
ALLOWED_USER_IDS_STR = os.getenv('ALLOWED_USER_IDS', '')
ALLOWED_USER_IDS = set()
if ALLOWED_USER_IDS_STR:
    try:
        ALLOWED_USER_IDS = {int(uid.strip()) for uid in ALLOWED_USER_IDS_STR.split(',') if uid.strip()}
        logger.info(f"Loaded {len(ALLOWED_USER_IDS)} allowed user IDs")
    except ValueError as e:
        logger.error(f"Error parsing ALLOWED_USER_IDS: {e}. Expected comma-separated integers.")
        ALLOWED_USER_IDS = set()

# Initialize Gemini
client = genai.Client(api_key=GEMINI_API_KEY)


class ExampleResponse(BaseModel):
    """Response model for example sentence and translation."""
    example_sentence: str = Field(description="A natural and everyday example sentence in German")
    translation: str = Field(description="The translation of the example sentence into English")


# Global Anki deck - stores cards in memory
anki_deck_id = 2059400110  # Random ID for the deck
anki_model_id = 1091735104  # Random ID for the model

# Define Anki model with two card templates (direct and reversed)
anki_model = genanki.Model(
    anki_model_id,
    ANKI_MODEL_NAME,
    fields=[
        {'name': 'GermanWord'},
        {'name': 'ExampleSentence'},
        {'name': 'Translation'},
    ],
    templates=[
        {
            'name': 'German → English',
            'qfmt': '{{GermanWord}}<br><br>{{ExampleSentence}}',
            'afmt': '{{FrontSide}}<hr id="answer">{{Translation}}',
        },
        {
            'name': 'English → German',
            'qfmt': '{{Translation}}',
            'afmt': '{{FrontSide}}<hr id="answer">{{GermanWord}}<br><br>{{ExampleSentence}}',
        },
    ],
)

# Global deck instance
anki_deck = genanki.Deck(anki_deck_id, ANKI_DECK_NAME)

# Store for tracking cards added in this session
cards_added = []


def is_user_authorized(user_id: int) -> bool:
    """Check if a user ID is in the allowed whitelist."""
    if not ALLOWED_USER_IDS:
        # If whitelist is empty, allow all users (backward compatibility)
        return True
    return user_id in ALLOWED_USER_IDS


async def check_authorization(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the user is authorized and send a message if not."""
    user_id = update.effective_user.id
    
    if not is_user_authorized(user_id):
        logger.warning(f"Unauthorized access attempt by user {user_id} (@{update.effective_user.username})")
        await update.message.reply_text(
            '❌ Zugriff verweigert.\n\n'
            'Sie sind nicht autorisiert, diesen Bot zu verwenden.'
        )
        return False
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    if not await check_authorization(update, context):
        return
    
    await update.message.reply_text(
        'Hallo! Ich bin ein German Word Bot.\n\n'
        'Senden Sie mir ein deutsches Wort, und ich werde:\n'
        '1. Ein Beispielsatz mit diesem Wort erstellen\n'
        '2. Eine Übersetzung bereitstellen\n'
        '3. Eine Anki-Karte hinzufügen\n\n'
        'Verwenden Sie /export, um alle Karten als .apkg-Datei zu exportieren.\n'
        'Verwenden Sie /clear, um alle gesammelten Karten zu löschen.'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    if not await check_authorization(update, context):
        return
    
    await update.message.reply_text(
        'Verfügbare Befehle:\n'
        '/start - Startet den Bot\n'
        '/help - Zeigt diese Hilfe\n'
        '/export - Exportiert alle gesammelten Karten als .apkg-Datei\n'
        '/clear - Löscht alle gesammelten Karten\n\n'
        'Senden Sie einfach ein deutsches Wort, um eine Karte zu erstellen!'
    )


async def generate_example(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle German word messages and generate example sentences."""
    if not await check_authorization(update, context):
        return
    
    german_word = update.message.text.strip()
    
    if not german_word:
        await update.message.reply_text('Bitte senden Sie ein deutsches Wort.')
        return
    
    try:
        # Show "typing..." status
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action='typing'
        )
        
        # Generate example sentence and translation using Gemini with structured output        
        prompt = f"""Erstelle einen Beispielsatz auf Deutsch mit dem Wort "{german_word}". 
Der Satz sollte natürlich und alltäglich sein. 
Dann übersetze diesen Satz ins Englische."""


        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config=GenerateContentConfig(
                response_mime_type= "application/json",
                response_schema= ExampleResponse,
            ),
        )
        
        # Parse JSON response using Pydantic model
        response_json = json.loads(response.text)
        example_data = ExampleResponse(**response_json)
        example_sentence = example_data.example_sentence
        translation = example_data.translation
        
        # Create Anki note (this will generate 2 cards: direct and reversed)
        note = genanki.Note(
            model=anki_model,
            fields=[german_word, example_sentence, translation]
        )
        
        # Add note to deck (generates both cards automatically)
        anki_deck.add_note(note)
        cards_added.append({
            'word': german_word,
            'sentence': example_sentence,
            'translation': translation
        })
        
        # Send response to user
        message = f"✅ 2 Karten erstellt!\n\n"
        message += f"**Wort:** {german_word}\n"
        message += f"**Beispielsatz:** {example_sentence}\n"
        message += f"**Übersetzung:** {translation}\n\n"
        message += f"Kartenpaare gesammelt: {len(cards_added)} ({len(cards_added) * 2} Karten)\n"
        message += "Verwenden Sie /export, um die .apkg-Datei zu erhalten."
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error generating example: {e}")
        await update.message.reply_text(
            f'Ein Fehler ist aufgetreten: {str(e)}\n'
            'Bitte versuchen Sie es später erneut.'
        )


async def export_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export all collected cards as an .apkg file."""
    if not await check_authorization(update, context):
        return
    
    if len(cards_added) == 0:
        await update.message.reply_text('Keine Karten zum Exportieren. Erstellen Sie zuerst einige Karten!')
        return
    
    try:
        # Generate .apkg file
        package = genanki.Package(anki_deck)
        package.write_to_file('german_words.apkg')
        
        # Send file to user
        with open('german_words.apkg', 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename='german_words.apkg',
                caption=f'✅ {len(cards_added)} Karten exportiert!'
            )
        
        # Clean up file
        os.remove('german_words.apkg')
        
    except Exception as e:
        logger.error(f"Error exporting cards: {e}")
        await update.message.reply_text(f'Fehler beim Exportieren: {str(e)}')


async def clear_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear all collected cards."""
    if not await check_authorization(update, context):
        return
    
    global anki_deck, cards_added
    
    card_count = len(cards_added)
    cards_added.clear()
    anki_deck = genanki.Deck(anki_deck_id, ANKI_DECK_NAME)
    
    await update.message.reply_text(f'✅ {card_count} Karten gelöscht.')


def main():
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("export", export_cards))
    application.add_handler(CommandHandler("clear", clear_cards))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_example))
    
    # Start the bot
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
