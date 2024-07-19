import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Вставьте ваш токен сюда
TOKEN = '7381059744:AAEwmguHOJ-36rM2ze3Urne_eWIiWagRu8E'

# Вопросы и ответы для викторины
questions = [
    {"text": "Какое ваше любимое место отдыха?", "options": ["Лес", "Пляж", "Горы", "Дом"]},
    {"text": "Что вам нравится больше всего?", "options": ["Спать", "Есть", "Играть", "Путешествовать"]},
]

# Изображения животных
animal_images = {
    "Медведь": "animal_images/bear_image.jpeg",
    "Фламинго": "animal_images/flamingo_image.jpeg",
    "Козерог": "animal_images/ibex_image.jpg",
    "Кошка": "animal_images/cat_image.jpg",
    "Коала": "animal_images/koala_image.jpg",
    "Панда": "animal_images/panda_image.jpg",
    "Обезьяна": "animal_images/monkey_image.jpg",
    "Черепаха": "animal_images/turtle_image.jpg",
}

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

feedback_storage = []  # Хранилище для отзывов

# Стартовая команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['questions'] = questions
    context.user_data['current_question'] = 0
    context.user_data['answers'] = []
    welcome_message = "Привет! Давайте начнем викторину 'Какое у вас тотемное животное?'"
    privacy_message = "Мы собираем только необходимые данные и обеспечиваем их конфиденциальность."
    if update.message:
        await update.message.reply_text(f"{welcome_message}\n\n{privacy_message}")
        await ask_question(update, context)

# Задать вопрос
async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    question = context.user_data['questions'][context.user_data['current_question']]
    options = [InlineKeyboardButton(opt, callback_data=str(i)) for i, opt in enumerate(question['options'])]
    reply_markup = InlineKeyboardMarkup([options])
    if update.callback_query:
        await update.callback_query.message.reply_text(question['text'], reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(question['text'], reply_markup=reply_markup)

# Обработка ответов
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        answer_index = int(query.data)
        context.user_data['answers'].append(answer_index)
        if context.user_data['current_question'] + 1 < len(context.user_data['questions']):
            context.user_data['current_question'] += 1
            await ask_question(update, context)
        else:
            await send_result(update, context)
    except ValueError:
        await restart_quiz(update, context)

# Определение тотемного животного
def determine_totem_animal(answers):
    # Система баллов
    scores = {
        "Медведь": 0, "Фламинго": 0, "Козерог": 0, "Кошка": 0,
        "Коала": 0, "Панда": 0, "Обезьяна": 0, "Черепаха": 0
    }
    mapping = [("Лес", "Медведь"), ("Пляж", "Фламинго"), ("Горы", "Козерог"), ("Дом", "Кошка"),
               ("Спать", "Коала"), ("Есть", "Панда"), ("Играть", "Обезьяна"), ("Путешествовать", "Черепаха")]

    for idx in answers:
        if 0 <= idx < len(mapping):
            animal = mapping[idx][1]
            scores[animal] += 1

    max_animal = max(scores, key=scores.get)
    return max_animal, scores

# Отправка результата
async def send_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result, scores = determine_totem_animal(context.user_data['answers'])
    image_path = animal_images.get(result)

    # Определите URL вашего бота
    bot_url = "https://t.me/your_bot_username"  # Замените на URL вашего бота

    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, 'rb') as image_file:
                # Сначала отправляем изображение
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_file)

                # Добавляем текст с результатами и баллами
                scores_message = "\n".join([f"{animal}: {score}" for animal, score in scores.items()])
                result_message = f"Ваше тотемное животное - {result}!\n\nБаллы:\n{scores_message}"

                # Отправляем сообщение с результатом и кнопками для социальных сетей и перезапуска
                share_keyboard = [
                    [InlineKeyboardButton("Поделиться в VK", url=f"https://vk.com/share.php?url={bot_url}")],
                    [InlineKeyboardButton("Поделиться в Facebook", url=f"https://www.facebook.com/sharer/sharer.php?u={bot_url}")],
                    [InlineKeyboardButton("Попробовать ещё раз?", callback_data='restart_quiz')]
                ]
                share_reply_markup = InlineKeyboardMarkup(share_keyboard)
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"{result_message}\n\nУзнайте больше о программе опеки на нашем сайте.",
                    reply_markup=share_reply_markup
                )
        except Exception as e:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=f"Ошибка при загрузке изображения для {result}: {e}")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Изображение для {result} не найдено.")

# Обработчик кнопки перезапуска викторины
async def restart_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Очищаем данные пользователя
    context.user_data.clear()

    # Отправляем сообщение о перезапуске викторины
    await query.edit_message_text(
        text="Викторина перезапущена. Начнем с начала!",
        reply_markup=None
    )

    # Начинаем викторину заново
    await start(update, context)

# Контактная информация
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    contact_info = (
        "Связаться с нами можно по следующим контактам:\n"
        "Email: bogatyirskiy@yandex.ru\n"
        "Телефон: +7 952 099 88 22\n"
        "Больше информации о животных: https://moscowzoo.ru/animals/kinds"
    )
    await update.message.reply_text(contact_info)

# Обратная связь
async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Спасибо за ваши отзывы! Напишите, что вам понравилось или что можно улучшить.")
    context.user_data['feedback'] = True

async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('feedback'):
        feedback_text = update.message.text
        feedback_storage.append(feedback_text)  # Сохраняем отзывы
        context.user_data['feedback'] = False
        await update.message.reply_text("Спасибо за ваш отзыв!")
        logger.info("Feedback received: %s", feedback_text)

# Справка
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = "Этот бот поможет вам узнать ваше тотемное животное и расскажет о программе опеки Московского зоопарка. Используйте команду /start для начала викторины."
    await update.message.reply_text(help_text)

# Обработчик ошибок
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a Telegram message to notify the user."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    if isinstance(update, Update):
        try:
            await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте снова позже.")
        except Exception as e:
            logger.error(f"Failed to send error message to user: {e}")

    logger.error(f"Update: {update} caused error: {context.error}")

def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("contact", contact))
    application.add_handler(CommandHandler("feedback", feedback))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback))
    application.add_handler(CallbackQueryHandler(handle_answer))
    application.add_handler(CallbackQueryHandler(restart_quiz, pattern='^restart_quiz$'))

    application.add_error_handler(error_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
