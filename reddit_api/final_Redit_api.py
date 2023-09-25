# -*- coding: utf-8 -*-
import praw
import logging
import concurrent.futures
import time
import datetime
import sqlite3
import json

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Соединение с базой данных или создание новой, если она не существует
con = sqlite3.connect("usernames.db")
cursor = con.cursor()



# Вынесем настройки аутентификации Reddit API в отдельные переменные
reddit_config = config.get('reddit_api', {})
CLIENT_ID = reddit_config.get('client_id', 'default')
CLIENT_SECRET = reddit_config.get('client_secret', 'default')
USERNAME = reddit_config.get('username', 'default')
PASSWORD = reddit_config.get('password', 'default')
USER_AGENT = reddit_config.get('user_agent', 'default')

# Вынесем настройки логирования в отдельные переменные
logging_config = config.get('logging', {})
LOG_FILE = logging_config.get('log_file', "final_Reddit_api.log")
LOG_LEVEL = logging_config.get('log_level', "INFO")
comment_authors_name_set = set()
running_tests = False

post_limit = config.get('post_limit', 35)

# Функция для сохранения имен авторов комментариев
def create_and_insert_table(authors_name_set):
    try:
        # Создание таблицы main.username, если она не существует
        cursor.execute('''
                CREATE TABLE IF NOT EXISTS main.username (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT 
                )
            ''')

        # Вставка имен в таблицу
        for username in authors_name_set:
            cursor.execute('INSERT INTO main.username (name) VALUES (?)', (username,))

        con.commit()
    except sqlite3.IntegrityError:
        con.rollback()
        logging.info(f'User already exists in the database.')
    except sqlite3.Error as e:
        con.rollback()
        logging.error(f'Error inserting user into database: {str(e)}')


# Функция для обработки постов
def process_submission(submission):
    logging.info(f'[{datetime.datetime.now()}] Заголовок: {submission.title}')
    author_name = submission.author.name if submission.author else "[УДАЛЕНО]"
    logging.info(f'[{datetime.datetime.now()}] Имя автора: {author_name}')

    for comment in submission.comments.list():
        if comment.author and comment.author.name != "AutoModerator":
            comment_authors_name_set.add(comment.author.name)
            logging.info(f'[{datetime.datetime.now()}] Автор комментария: {comment.author.name}')
    logging.info("-----------------------------------------------------------------")


# Функция для отправки сообщений
def send_message(username):
    global message_sent_counter
    try:
        reddit.redditor(username).message(subject="Заголовок сообщения", message=message_text_or_image)
        message_sent_counter += 1
        logging.info(f'[{datetime.datetime.now()}] Сообщение отправлено пользователю: {username}')
        logging.info("-----------------------------------------------------------------")
    except Exception as e:
        logging.error(f'[{datetime.datetime.now()}] Ошибка при отправке сообщения пользователю {username}: {str(e)}')
        logging.info("-----------------------------------------------------------------")


# Настройка логирования
logging.basicConfig(filename=LOG_FILE, level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')

# Создание объекта Reddit API
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    username=USERNAME,
    password=PASSWORD,
    user_agent=USER_AGENT
)

# Бесконечный цикл для периодического выполнения
while True:
    if running_tests:
        break
    # Список ссылок на сабреддиты
    subreddit_links = config.get('subreddit_links', [])

    # Счетчики
    submission_counter = 0
    message_sent_counter = 0

    # Обработка каждого сабреддита
    for subreddit_link in subreddit_links:
        subreddit_name = subreddit_link.split("/")[-2]
        logging.info(f"[{datetime.datetime.now()}] Ссылка на сабреддит: {subreddit_link}")
        logging.info(f"[{datetime.datetime.now()}] Имя сабреддита :  {subreddit_name}")
        subreddit = reddit.subreddit(subreddit_name)
        logging.info(f'[{datetime.datetime.now()}] Сабреддит : {subreddit}')

        # Обработка постов с использованием пула потоков
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for submission in subreddit.new(limit=post_limit):
                submission_counter += 1
                executor.submit(process_submission, submission)

        logging.info(f'[{datetime.datetime.now()}] Всего постов в {subreddit_name}: {submission_counter}')

        # Запись в лог количества уникальных авторов комментариев
        log_message = "Множество авторов комментариев: {}".format(len(comment_authors_name_set))
        logging.info(log_message)

        # Вызываем функцию для создания таблицы и вставки данных в БД
        create_and_insert_table(comment_authors_name_set)

        # Отправка сообщений
        message_text_or_image = config.get('message_text_or_image', 'Ваше сообщение здесь')

        usernames_to_message = list(comment_authors_name_set)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(send_message, username) for username in usernames_to_message]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f'Ошибка при отправке сообщения: {str(e)}')

        # Логирование счетчиков
        logging.info(f"[{datetime.datetime.now()}] Всего обработано постов: {submission_counter}")
        logging.info(f"[{datetime.datetime.now()}] Всего отправлено сообщений: {message_sent_counter}")
    logging.info(f"[{datetime.datetime.now()}] Круг выполнения окончен")
    pause_duration_seconds = config.get('pause_duration_seconds', 10)

    time.sleep(pause_duration_seconds)