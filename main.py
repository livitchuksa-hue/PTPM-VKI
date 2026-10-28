import logging
import sys
import re
import os
import traceback
from datetime import datetime


log_format = "%(asctime)s | [%(levelname)-7s] | %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"

# 1. Создаем папку logs, если её нет
if not os.path.exists("logs"):
    os.makedirs("logs")

# 2. Генерируем имя файла с текущей датой и временем
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"logs/app_{timestamp}.log"

# 3. Настраиваем логгер
logging.basicConfig(
    level=logging.DEBUG,
    format=log_format,
    datefmt=date_format,
    handlers=[
        logging.StreamHandler(sys.stdout),                   # Вывод в консоль
        logging.FileHandler(log_filename, encoding="utf-8")  # Вывод в файл
    ]
)

logging.info("Логгер успешно сконфигурирован")
logging.info("Приложение запущено")



def mask_password(password: str) -> str:

    if not password:
        return "<empty>"

    h = 0
    for i, ch in enumerate(password):
        h = (h * 131 + ord(ch) + i) & 0xFFFFFFFF
    return f"<hidden:{h:08x}>"



BLACKLIST_LOGINS = {
    "admin", "root", "user", "test", "guest",
    "administrator", "moderator", "support", "sysadmin", "qwerty"
}



# Телефон: +x-xxx-xxx-xxxx  (например +7-123-456-7890)
PHONE_PATTERN = r"^\+\d-\d{3}-\d{3}-\d{4}$"

# Email — стандартная маска
EMAIL_PATTERN = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

# Обычный логин: минимум 5 символов, только латиница, цифры, _
LOGIN_PATTERN = r"^[A-Za-z0-9_]{5,}$"

# Пароль: минимум 7 символов, кириллица + цифры + спецсимволы,
# минимум 1 буква в верхнем и нижнем регистре, 1 цифра и 1 спецсимвол
# Разрешённые символы: кириллица (а-яА-Я), цифры, спецсимволы
PASSWORD_PATTERN = (
    r"^(?=.*[а-я])(?=.*[А-Я])(?=.*\d)(?=.*[!@#$%^&*()_\-+=\[\]{};:'\",.<>/?\\|`~])"
    r"[а-яА-Я\d!@#$%^&*()_\-+=\[\]{};:'\",.<>/?\\|`~]{7,}$"
)



def validate_login(login: str):

    if login is None or login == "":
        return False, "Логин не может быть пустым"

    # Попытка интерпретировать как телефон
    if login.startswith("+"):
        if not re.fullmatch(PHONE_PATTERN, login):
            return False, "Неверный формат телефона (ожидается +x-xxx-xxx-xxxx)"
        return True, None

    # Попытка интерпретировать как email (содержит @)
    if "@" in login:
        if not re.fullmatch(EMAIL_PATTERN, login):
            return False, "Неверный формат email"
        if login.lower() in BLACKLIST_LOGINS:
            return False, "Email находится в чёрном списке"
        return True, None

    # Обычный логин
    if not re.fullmatch(LOGIN_PATTERN, login):
        # Разделим причины для наглядности
        if len(login) < 5:
            return False, "Логин должен содержать минимум 5 символов"
        if not re.fullmatch(r"^[A-Za-z0-9_]+$", login):
            return False, "Логин может содержать только латиницу, цифры и _"
        return False, "Неверный формат логина"

    if login.lower() in BLACKLIST_LOGINS:
        return False, "Логин находится в чёрном списке"

    return True, None


def validate_password(password: str):

    if password is None or password == "":
        return False, "Пароль не может быть пустым"

    if len(password) < 7:
        return False, "Пароль должен содержать минимум 7 символов"

    if not re.search(r"[а-я]", password):
        return False, "Пароль должен содержать минимум одну строчную букву кириллицы"

    if not re.search(r"[А-Я]", password):
        return False, "Пароль должен содержать минимум одну заглавную букву кириллицы"

    if not re.search(r"\d", password):
        return False, "Пароль должен содержать минимум одну цифру"

    if not re.search(r"[!@#$%^&*()_\-+=\[\]{};:'\",.<>/?\\|`~]", password):
        return False, "Пароль должен содержать минимум один спецсимвол"

    # Запрещённые символы: латиница, пробелы и прочее вне разрешённого набора
    if not re.fullmatch(
        r"[а-яА-Я\d!@#$%^&*()_\-+=\[\]{};:'\",.<>/?\\|`~]+", password
    ):
        return False, "Пароль содержит недопустимые символы (разрешены только кириллица, цифры и спецсимволы)"

    return True, None



def register_user(login: str, password: str, password_confirm: str):

    masked_pwd = mask_password(password)
    masked_confirm = mask_password(password_confirm)

    logging.info(
        "Запрос регистрации: login='%s', password=%s, password_confirm=%s",
        login, masked_pwd, masked_confirm
    )

    try:
        # 1) Логин
        ok, err = validate_login(login)
        if not ok:
            logging.error("Регистрация отклонена: %s", err)
            return False, err

        # 2) Пароль
        ok, err = validate_password(password)
        if not ok:
            logging.error("Регистрация отклонена: %s", err)
            return False, err

        # 3) Совпадение паролей
        if password != password_confirm:
            err = "Пароль и подтверждение пароля не совпадают"
            logging.error("Регистрация отклонена: %s", err)
            return False, err

        # 4) Успех
        logging.info("Регистрация успешна: login='%s', password=%s", login, masked_pwd)
        return True, ""

    except Exception as ex:
        # Неуспешный запрос — логируем traceback
        logging.error("Исключение при регистрации: %s", ex)
        logging.exception("Трассировка стека:")
        return False, f"Внутренняя ошибка: {ex}"



def Main():
    try:
        login = input("Логин: ")
        password = input("Пароль: ")
        password_confirm = input("Подтверждение пароля: ")

        result, message = register_user(login, password, password_confirm)

        print(f"Результат: {result}")
        print(f"Сообщение: {message if message else '<пусто>'}")
        if not result:
            logging.warning("Итог регистрации: неуспех — %s", message)
        else:
            logging.info("Итог регистрации: успех")

    except KeyboardInterrupt:
        logging.warning("Прервано пользователем (Ctrl+C)")
    except Exception as ex:
        logging.error("Критическая ошибка в Main: %s", ex)
        logging.exception("Трассировка стека:")
        print("Произошла непредвиденная ошибка. Подробности в логах.")


if __name__ == "__main__":
    Main()