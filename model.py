import openai
import dotenv
import logging

logger = logging.getLogger(__name__)

# Загружаем переменные окружения из файла .env
try:
    env = dotenv.dotenv_values(".env")
    YA_API_KEY = env["YA_API_KEY"]
    YA_FOLDER_ID = env["YA_FOLDER_ID"]
except FileNotFoundError:
    raise FileNotFoundError("Файл .env не найден.")
except KeyError as e:
    raise KeyError(f"Переменная окружения {str(e)} не найдена в файле .env.")


class LLMService:
    """
    Класс для общения с YandexGPT (через OpenAI-совместимый клиент).
    """
    def __init__(self, prompt_file):
        # Загружаем системный промпт
        with open(prompt_file, encoding='utf-8') as f:
            self.sys_prompt = f.read()

        try:
            self.client = openai.OpenAI(
                api_key=YA_API_KEY,
                base_url="https://llm.api.cloud.yandex.net/v1",
            )
            self.model = f"gpt://{YA_FOLDER_ID}/yandexgpt-lite"
        except Exception as e:
            logger.error(f"Ошибка при инициализации LLM клиента: {str(e)}")

    def chat(self, message, history):
        # Берём последние 20 сообщений для контекста
        messages = [{"role": "system", "content": self.sys_prompt}] + history[-20:] + [
            {"role": "user", "content": message}
        ]
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=256,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Произошла ошибка при работе с моделью: {str(e)}"


# Инициализация LLM
llm_1 = LLMService("prompts/prompt_gavrich.txt")


def chat_with_llm(user_message, history):
    """
    Чат с LLM — просто добавление сообщений пользователя и ассистента.
    Контроль приветствий осуществляется в bot.py.
    """
    llm_response = llm_1.chat(user_message, history)
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": llm_response})
    return llm_response
