import os
import json
import random
import logging
from dotenv import load_dotenv
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Каталог с изображениями
IMAGE_DIR = "images"
# Файл с подписями
CAPTIONS_FILE = "captions.json"

def load_tiger_data():
    """Загружает данные о тиграх из файлов."""
    image_files = [f for f in os.listdir(IMAGE_DIR) if os.path.isfile(os.path.join(IMAGE_DIR, f))]
    if not image_files:
        logger.error(f"В каталоге нет изображений: {IMAGE_DIR}")
        return [], []  # Возвращаем пустые списки

    try:
        with open(CAPTIONS_FILE, "r", encoding="utf-8") as f:
            captions = json.load(f)
    except FileNotFoundError:
        logger.error(f"Файл с подписями не найден: {CAPTIONS_FILE}")
        return [], [] # Возвращаем пустые списки
    except json.JSONDecodeError:
        logger.error(f"Ошибка при чтении JSON файла: {CAPTIONS_FILE}")
        return [], [] # Возвращаем пустые списки

    return image_files, captions

image_files, captions = load_tiger_data()  # Получаем списки файлов и подписей
used_image_indices = set()  # Множество для отслеживания использованных индексов изображений

def get_random_image():
    """Получает случайное изображение без повторов до исчерпания всех."""
    global used_image_indices

    if len(used_image_indices) == len(image_files):
        # Все изображения показаны, начинаем сначала
        used_image_indices.clear()
        logger.info("Все изображения показаны, начинаем сначала.")

    available_indices = set(range(len(image_files))) - used_image_indices
    index = random.choice(list(available_indices))
    used_image_indices.add(index)
    return image_files[index]

def get_random_caption():
    """Получает случайную подпись (с повторами)."""
    return random.choice(captions)  # Просто выбираем случайную подпись

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает команду /start."""
    keyboard = [
        [InlineKeyboardButton("Какой тигр я сегодня?", callback_data="random_tiger")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Нажми кнопку, чтобы узнать, какой ты тигр сегодня:", reply_markup=reply_markup)

async def send_random_tiger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет случайного тигра."""
    query = update.callback_query
    await query.answer()

    if not image_files or not captions:
        await context.bot.send_message(chat_id=query.message.chat_id, text="Нет доступных данных о тиграх.")
        return

    image_file = get_random_image()  # Получаем случайное изображение (без повторов)
    caption = get_random_caption()  # Получаем случайную подпись (с повторами)

    photo_path = os.path.join(IMAGE_DIR, image_file) # Build the full path
    try:
        with open(photo_path, "rb") as photo_file:
            await context.bot.send_photo(chat_id=query.message.chat_id, photo=photo_file, caption=caption)
    except FileNotFoundError:
        logger.error(f"Файл не найден: {photo_path}")
        await context.bot.send_message(chat_id=query.message.chat_id, text="Ошибка: изображение не найдено.")

    # Добавляем кнопку после каждого сообщения
    keyboard = [
        [InlineKeyboardButton("Какой тигр я сегодня?", callback_data="random_tiger")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=query.message.chat_id, text="Хочешь еще одного тигра?", reply_markup=reply_markup)



async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Логирует ошибки."""
    logger.error(msg="Ошибка при обработке обновления:", exc_info=context.error)
    if update and isinstance(update, Update):
        try:
            await update.message.reply_text("Произошла ошибка. Попробуйте позже.")
        except Exception as e:
            logger.error(msg="Ошибка при отправке сообщения:", exc_info=e)

def main():
    """Запуск бота."""
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(send_random_tiger, pattern="random_tiger"))
    application.add_error_handler(error_handler)

    application.run_polling()

if __name__ == "__main__":
    main()