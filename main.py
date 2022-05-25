import telebot
import requests
from config import tel_API, faceit_API, db_URI

match_id_example = '1-1f4bb450-998d-45f2-a664-6b850f271c51'

bot = telebot.TeleBot(tel_API)
headers = {"Authorization": f"Bearer {faceit_API}", "accept": "application/json"}

@bot.message_handler(commands=['start','help'])
def start(message):
    bot.send_message(message.chat.id, 'Privet, klounich')

@bot.message_handler(commands=['elo'])
def elo(message):
    if (len(message.text)<6 or message.text.count(' ') == 0):
        bot.send_message(message.chat.id, "Please follow the form:\n<b>/elo FaceitNickname</b>", parse_mode='html')
    else:
        user_name = message.text[5:]
        response = requests.get(f"https://open.faceit.com/data/v4/players?nickname={user_name}", headers=headers)
        if (response.status_code == 200):
            user_elo = response.json()["games"]["csgo"]["faceit_elo"]
            user_level = response.json()["games"]["csgo"]["skill_level"]
            bot.send_message(message.chat.id, f'Player: {user_name}\nelo: {user_elo}\nlevel: {user_level}')
        else:
            bot.send_message(message.chat.id, "<b>404</b> <i>Not Found</i>", parse_mode='html')

bot.polling(none_stop=True)
