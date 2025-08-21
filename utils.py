import json
import os
from datetime import datetime, timezone

ERROR_FILE = "error.json"
MEMORY_FILE = "dialog_memory.json"

# Получение текущей даты
def get_time_now():
    return str(datetime.now(timezone.utc)).split(".")[0].replace("-", ".")

# Логирование времени
def log_error(e):
    print(e)
    try:
        error_entry = {"time": get_time_now(), "error": str(e)}
        errors = []

        if os.path.exists("error.json"):
            with open("error.json", "r", encoding="utf-8") as f:
                try:
                    errors = json.load(f)
                except:
                    pass # Если ошибка, то просто пропускаем

        errors.append(error_entry)

        with open("error.json", "w", encoding="utf-8") as f:
            json.dump(errors, f, ensure_ascii=False, indent=4)

    except Exception as log_exc:
        print(f"Ошибка сохранения лога: {log_exc}")

# Загрузка памяти бота
def load_memory():
    user_histories = {}
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                user_histories.update(json.load(f))
                print(f"Загружено {len(user_histories)} пользователей из памяти")
                for user_id in user_histories:
                    print(f"{user_id}: {len(user_histories[user_id])}")

        except Exception as e:
            log_error(f"Не удалось загрузить память: {e}")

    return user_histories

# Сохранение памяти бота
def save_memory(user_histories):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(user_histories, f, ensure_ascii=False, indent=4)
    except Exception as e:
        log_error(f"Не удалось сохранить память: {e}")
