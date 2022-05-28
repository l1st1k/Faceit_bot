import telebot
import requests
import psycopg2
import time
from config import tel_API, faceit_API, db_URI

match_id_example = '1-1f4bb450-998d-45f2-a664-6b850f271c51'

bot = telebot.TeleBot(tel_API)
headers = {"Authorization": f"Bearer {faceit_API}", "accept": "application/json"}

def user_is_in_db(username):
    db_connection = psycopg2.connect(db_URI, sslmode="require")
    db_object = db_connection.cursor()
    db_object.execute(f"SELECT username, nickname FROM main_table WHERE username ='{username}'")
    result = db_object.fetchone()
    db_object.close()
    db_connection.close()
    if result:
        return True
    else:
        return False


def get_nickname(username):
    db_connection = psycopg2.connect(db_URI, sslmode="require")
    db_object = db_connection.cursor()
    db_object.execute(f"SELECT nickname FROM main_table WHERE username ='{username}'")
    result = db_object.fetchone()
    db_object.close()
    db_connection.close()
    return result[0]


def set_elo(username, user_elo):
    db_connection = psycopg2.connect(db_URI, sslmode="require")
    db_object = db_connection.cursor()
    db_object.execute(f"UPDATE main_table SET elo = {user_elo} WHERE username ='{username}'")
    db_connection.commit()
    db_object.close()
    db_connection.close()


@bot.message_handler(commands=['start', 'help'])
def start(message):
    pass


@bot.message_handler(commands=['connect'])
def connect(message):
    if message.text.strip() == '/connect':
        bot.send_message(message.chat.id, "Please follow the form:\n<b>/connect FaceitNickname</b>", parse_mode='html')
    else:
        db_connection = psycopg2.connect(db_URI, sslmode="require")
        db_object = db_connection.cursor()
        username = message.from_user.username
        nickname = message.text[9:].strip()
        response = requests.get(f"https://open.faceit.com/data/v4/players?nickname={nickname}", headers=headers)
        if response.status_code == 200:
            user_elo = response.json()["games"]["csgo"]["faceit_elo"]
            db_object.execute(f"SELECT username, nickname FROM main_table WHERE username ='{username}'")
            result = db_object.fetchone()
            if not result:
                db_object.execute("INSERT INTO main_table (username, nickname, elo, chat_id) VALUES (%s, %s, %s, %s)",
                                  (username, nickname, user_elo, message.chat.id))
                db_connection.commit()
                bot.send_message(message.chat.id,
                                 'Successfully connected!\nNow you can use /elo & /stats without rewriting your nickname!')
            elif result[0] == username and result[1] == nickname:
                bot.send_message(message.chat.id, 'This player is already connected to your telegram!')
            else:
                db_object.execute(
                    f"UPDATE main_table SET nickname = '{nickname}', elo = {user_elo} WHERE username ='{username}'")
                db_connection.commit()
                bot.send_message(message.chat.id,
                                 'Successfully connected!\nNow you can use /elo & /stats without rewriting your nickname!')
        else:
            bot.send_message(message.chat.id, "<b>404</b> <i>Not Found</i>\n<i>Probably incorrect faceit nickname</i>",
                             parse_mode='html')

        db_object.close()
        db_connection.close()





@bot.message_handler(commands=['elo'])
def elo(message):
    if not user_is_in_db(message.from_user.username):
        if len(message.text) < 6 or message.text.count(' ') == 0:
            bot.send_message(message.chat.id, "Please follow the form:\n<b>/elo FaceitNickname</b>", parse_mode='html')
        else:
            nickname = message.text[5:].strip()
            response = requests.get(f"https://open.faceit.com/data/v4/players?nickname={nickname}", headers=headers)
            if response.status_code == 200:
                user_elo = response.json()["games"]["csgo"]["faceit_elo"]
                user_level = response.json()["games"]["csgo"]["skill_level"]
                bot.send_message(message.chat.id, f'Player: {nickname}\nelo: {user_elo}\nlevel: {user_level}')
            else:
                bot.send_message(message.chat.id, "<b>404</b> <i>Not Found</i>", parse_mode='html')
    else:
        if len(message.text) < 6:
            nickname = get_nickname(message.from_user.username)
            response = requests.get(f"https://open.faceit.com/data/v4/players?nickname={nickname}", headers=headers)
            if response.status_code == 200:
                user_elo = response.json()["games"]["csgo"]["faceit_elo"]
                user_level = response.json()["games"]["csgo"]["skill_level"]
                bot.send_message(message.chat.id, f'Player: {nickname}\nelo: {user_elo}\nlevel: {user_level}')
                set_elo(message.from_user.username, user_elo)
            else:
                bot.send_message(message.chat.id, "<i>Unexpected error</i>", parse_mode='html')

        elif message.text.count(' ') == 0:
            bot.send_message(message.chat.id, "Please follow the form:\n<b>/elo FaceitNickname</b>", parse_mode='html')
        else:
            nickname = message.text[5:].strip()
            response = requests.get(f"https://open.faceit.com/data/v4/players?nickname={nickname}", headers=headers)
            if response.status_code == 200:
                user_elo = response.json()["games"]["csgo"]["faceit_elo"]
                user_level = response.json()["games"]["csgo"]["skill_level"]
                bot.send_message(message.chat.id, f'Player: {nickname}\nelo: {user_elo}\nlevel: {user_level}')
            else:
                bot.send_message(message.chat.id, "<b>404</b> <i>Not Found</i>", parse_mode='html')


@bot.message_handler(func=lambda message: message.text == 'elo', content_types=['text'])
def elo_txt(message):
    if user_is_in_db(message.from_user.username):
        nickname = get_nickname(message.from_user.username)
        response = requests.get(f"https://open.faceit.com/data/v4/players?nickname={nickname}", headers=headers)
        if response.status_code == 200:
            user_elo = response.json()["games"]["csgo"]["faceit_elo"]
            user_level = response.json()["games"]["csgo"]["skill_level"]
            bot.send_message(message.chat.id, f'Player: {nickname}\nelo: {user_elo}\nlevel: {user_level}')
            set_elo(message.from_user.username, user_elo)
        else:
            bot.send_message(message.chat.id, "<i>Unexpected error</i>", parse_mode='html')
    else:
        bot.send_message(message.chat.id,
                         "<i>You need to /connect your Faceit account previously</i>", parse_mode='html')




def update():
    db_connection = psycopg2.connect(db_URI, sslmode="require")
    db_object = db_connection.cursor()
    db_object.execute(f"SELECT nickname, elo, chat_id FROM main_table")
    result = db_object.fetchall()
    for user in result:
        response = requests.get(f"https://open.faceit.com/data/v4/players?nickname={user[0]}", headers=headers)
        user_elo = response.json()["games"]["csgo"]["faceit_elo"]
        if user[1] != user_elo:
            diff = user_elo - user[1]
            db_object.execute(
                f"UPDATE main_table SET elo = '{user_elo}' WHERE nickname ='{user[0]}'")
            db_connection.commit()
            if diff > 0:
                bot.send_message(user[2],
                                 f"<b>+{diff} elo</b>\n<i>Current elo: {user_elo}</i>\nGG",
                                 parse_mode='html')
            else:
                #user[2] should be chat_id
                bot.send_message(user[2],
                                 f"<b>-{abs(diff)} elo</b>\nCurrent elo: {user_elo}\nGG",
                                 parse_mode='html')

    print(time.time(), result[0][0])
    db_object.close()
    db_connection.close()

while True:
    update()
    time.sleep(15)


bot.infinity_polling()