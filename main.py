# -*- coding: utf-8 -*-
import os, time, traceback
from openai import OpenAI
from telebot import TeleBot, types

# Можно заменить на базовый промпт другого персонажа
from config import base_prompt as base_prompt
from utils import log_error, load_history, save_history

from dotenv import load_dotenv
load_dotenv()

OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")
client = OpenAI(api_key=OPEN_ROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")

MAX_HISTORY_LENGTH = 7
user_histories = load_history()

# Берем id и username что бы 
me = bot.get_me()
BOT_ID = me.id
BOT_USERNAME = (me.username or "").lower()

def should_answer(message: types.Message) -> bool:
    # В личных сообщениях всегда отвечаем
    if message.chat.type == "private":
        return True

    # Если упомянули бота
    text = (message.text or message.caption or "").lower()
    if f"@{BOT_USERNAME}" in text:
        return True

    # Если ответили боту
    replied_to_bot = (
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.id == BOT_ID
    )
    return replied_to_bot


def generate_answer(history: list[dict]) -> str:
    ai_response = client.chat.completions.create(
        model="deepseek/deepseek-r1-0528:free",
        messages=[{"role": "user", "content": base_prompt}, *history]
    )

    # Убираем лишние символы .replace("*", "")
    answer = ai_response.choices[0].message.content.strip()
    print(f"Ответ нейросети: {answer}")
    return answer


@bot.message_handler(content_types=["text"])
def on_text(message: types.Message):
    # Проверяем должен ли ответить бот
    if not should_answer(message):
        return

    chat_id = message.chat.id
    user_name = message.from_user.full_name if message.from_user else "Пользователь"
    user_id = str(message.from_user.id)

    print(f"Генерация ответа на сообщение: \"{user_name}: {message.text}\"")

    # Инициализируем историю пользователя, если её нет
    if user_id not in user_histories:
        user_histories[user_id] = []
    
    # Добавляем новое сообщение в историю
    user_histories[user_id].append({"role": "user", "content": f"{user_name}: {message.text}"})

    # Обрезаем историю при необходимости
    if len(user_histories[user_id]) > MAX_HISTORY_LENGTH:
        print("MAX_HISTORY_LENGTH сработал")
        user_histories[user_id] = user_histories[user_id][-MAX_HISTORY_LENGTH:]

    try:
        # Индикация "Печатает..."
        bot.send_chat_action(chat_id, "typing", message_thread_id=message.message_thread_id)
        answer = generate_answer(user_histories[user_id])

        # Добавляем ответ ИИ в историю
        user_histories[user_id].append({"role": "assistant", "content": answer})
        save_history(user_histories)

        if len(answer) >= 4000:
            answer = answer[:4000]
            print(f"Ответ больше 4000 символов!")

        bot.reply_to(message, answer)

    except Exception as e:
        if e.code == 429: # Ошибка если закончились токены
            log_error(f"Ошибка, закончились токены: {e}")
        else:
            log_error(e)
            traceback.print_exc()

if __name__ == "__main__":
    print("Бот запущен")
    # Важно: threaded=False — чтобы всё шло в одном потоке
    # skip_pending=True — чтобы не разгребать старую очередь после рестарта
    bot.infinity_polling(
        timeout=30,
        long_polling_timeout=30,
        skip_pending=True,
        allowed_updates=["message"],
        logger_level=None,
    )
