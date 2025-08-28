import logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

from telegram import ForceReply, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from model import chat_with_llm, llm_1

import dotenv

# Загружаем переменные окружения
try:
    env = dotenv.dotenv_values(".env")
    TELEGRAM_BOT_TOKEN = env["TELEGRAM_BOT_TOKEN"]
except FileNotFoundError:
    raise FileNotFoundError("Файл .env не найден.")
except KeyError as e:
    raise KeyError(f"Переменная {str(e)} не найдена в .env.")


# === Фильтр для удаления повторных приветствий ===
def clean_response(text: str, greeted: bool) -> str:
    """
    Убираем повторные приветствия, если пользователь уже здоровался.
    """
    if greeted:
        greetings = [
            "Здравствуйте", "Привет", "Добрый день", "Добрый вечер", "Доброе утро"
        ]
        for g in greetings:
            if text.strip().startswith(g):
                # Отрезаем первое предложение
                parts = text.split("!", 1) if "!" in text else text.split(".", 1)
                if len(parts) > 1:
                    text = parts[1].strip()
                else:
                    text = text.replace(g, "").strip()
                break
    return text


# === Обработчик команды /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        rf"Привет, {user.mention_html()}! 👋 Я продавец-консультант садового центра «Гавриш». Чем могу помочь?",
        reply_markup=ForceReply(selective=True),
    )
    # Устанавливаем флаг приветствия
    context.chat_data["greeted"] = True
    context.chat_data["history"] = []


# === Основной чат ===
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    user = update.effective_user.mention_html()

    history = context.chat_data.get("history", [])
    greeted = context.chat_data.get("greeted", False)

    # Добавляем сообщение пользователя
    user_message = f"Пользователь: {user}, Вопрос: {user_message}"
    history.append({"role": "user", "content": user_message})

    # Если приветствие уже было — меняем системный промпт
    if greeted:
        llm_1.sys_prompt = llm_1.sys_prompt.replace(
            "Приветствуй клиента только один раз",
            "Не приветствуй повторно, просто продолжай разговор."
        )
    else:
        context.chat_data["greeted"] = True

    # Получаем ответ от модели
    llm_response = llm_1.chat(user_message, history)

    # Чистим от повторных приветствий
    llm_response = clean_response(llm_response, context.chat_data["greeted"])

    # Сохраняем в историю
    history.append({"role": "assistant", "content": llm_response})
    context.chat_data["history"] = history

    await update.message.reply_text(llm_response)


# === Запуск ===
def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    chat_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, chat)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(chat_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
