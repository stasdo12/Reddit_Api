# -*- coding: utf-8 -*-
import praw
import logging
import concurrent.futures
import datetime
import sqlite3

# Соединение с базой данных или создание новой, если она не существует
con = sqlite3.connect("usernames.db")
cursor = con.cursor()

# Вынесем настройки аутентификации Reddit API в отдельные переменные
CLIENT_ID = 'MMkN7_zE7JEPMQicEWQkWQ'
CLIENT_SECRET = 'Pt1rXzwDvm4P49eZGh80009n0Lnv1g'
USERNAME = 'I_cant_do_i'
PASSWORD = 'Stas123212321'
USER_AGENT = 'test'

# Вынесем настройки логирования в отдельные переменные
LOG_FILE = 'final_Redit_api.log'
LOG_LEVEL = logging.INFO
comment_authors_name_set = set()



# Функция для сохранения имен авторов комментариев
def create_and_insert_table(authors_name_set):
    try:
        # Создание таблицы main.username, если она не существует
        cursor.execute('''
                CREATE TABLE IF NOT EXISTS main.test (
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
def process_submission(submission, timestamp):
    logging.info(f'[{timestamp}] Title: {submission.title}')
    author_name = submission.author.name if submission.author else "[УДАЛЕНО]"
    logging.info(f'[{timestamp}] Author name: {author_name}')

    for comment in submission.comments.list():
        if comment.author and comment.author.name != "AutoModerator":
            comment_authors_name_set.add(comment.author.name)
            logging.info(f'[{timestamp}] Comment author: {comment.author.name}')
    logging.info("-----------------------------------------------------------------")


# Функция для отправки сообщений
def send_message(username):
    global message_sent_counter
    try:
        reddit.redditor(username).message(subject="Title", message='message')
        message_sent_counter += 1
        logging.info(f'[{datetime.datetime.now()}] Message sent to user: {username}')
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

# Список ссылок на сабреддиты
subreddit_links = [
    'https://www.reddit.com/r/Tattoo/',
    'https://www.reddit.com/r/Economist/'
    # Добавьте другие ссылки на сабреддиты, если необходимо
]

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
        for submission in subreddit.new(limit=35):
            submission_counter += 1
            executor.submit(process_submission, submission)

    logging.info(f'[{datetime.datetime.now()}] Всего постов в {subreddit_name}: {submission_counter}')

    # Запись в лог количества уникальных авторов комментариев
    log_message = "Множество авторов комментариев: {}".format(len(comment_authors_name_set))
    logging.info(log_message)

    # Вызываем функцию для создания таблицы и вставки данных в БД
    create_and_insert_table(comment_authors_name_set)

    # Отправка сообщений
    message_text_or_image = "Ваше сообщение здесь"  # Замените на ваш текст или изображение
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
