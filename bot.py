import telebot
import redis
from redis.commands.json.path import Path
import redis.commands.search.aggregation as aggregations
import redis.commands.search.reducers as reducers
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import NumericFilter, Query
import logging
import json

r = redis.StrictRedis(host='artemki77.ru', port=6379, password='maxar2005', decode_responses=True)
logging.basicConfig(filename='py_logs.log', level=logging.WARNING, filemode='a', format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', datefmt='%H:%M:%S',)

bot = telebot.TeleBot('6401275301:AAGWQxy_8ITn0wZBODGjJqH3yerMdmlwD38')

users_index = r.ft("idx:users")
clicks_index = r.ft("idx:clicks")

@bot.message_handler(commands=["start", "help", "h"])
def start(message: telebot.types.Message):
    res = """
@PixelVerify_bot - бот созданный для верификации пользователей на сайте artemki77.ru
/verify - команда для верефикации вашего аккаунта по вашему нику в телеграмме
/stats - команда со статистикой вашей активности
если у вас возникли какие то проблемы или вы нашли ошибку то пишите @artemki77
"""
    bot.send_message(message.chat.id,res)

@bot.message_handler(commands=["verify"])
def verify(message: telebot.types.Message):
    user = message.from_user
    username = user.username

    res = users_index.search(Query(f"@username:{username}"))
    if not res.total:
        bot.reply_to(message, f'Пользователя с ником {username} на сайте artemki77.ru не существует')
    else:
        if res.total > 1:
            logging.ERROR(f'BOT: req "@username:{username}"')
        
        doc_res = res.docs[0]
        json_res = json.loads(doc_res.json)
        if json_res.get('verify'):
            bot.reply_to(message, f'Пользователя с ником {username} уже верифицирован')
        else:
            r.json().set(doc_res.id, '$.verify', 1)
            bot.reply_to(message, f'Пользователя с ником {username} прошёл верификацию')


@bot.message_handler(commands=["stats"])
def verify(message: telebot.types.Message):
    bot.reply_to(message, f'cорян эту функцию я ещё не доделал(')






if __name__ == '__main__':
    print('start..')
    bot.polling(non_stop=True)