from flask import Flask, render_template, redirect, request, session, url_for, jsonify, make_response
import redis
import json
from redis.commands.json.path import Path
import redis.commands.search.aggregation as aggregations
import redis.commands.search.reducers as reducers
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import NumericFilter, Query
import hashlib
import random
import datetime as dt
import logging
import re
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

logging.basicConfig(filename='py_logs.log', level=logging.WARNING, filemode='a', format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', datefmt='%H:%M:%S',)
r = redis.StrictRedis(host='artemki77.ru', port=6379, password=os.environ.get('db_password'), decode_responses=True)
colors = [
	"#FFA500", "#664200", "#331a00", "#00fac8", "#009476", "#9600c8", "#490061", "#e1beaa", "#c4845e", 
	"#ffaabe", "#ff5f82", "#000000", "#808080", "#C0C0C0", "#FFFFFF", "#FF00FF", "#800080", "#FF0000", 
	"#800000", "#FFFF00", "#808000", "#00FF00", "#008000", "#00FFFF", "#008080", "#0000FF", "#000080", 
	"#FA8750", "#ffd700"
]

patern_color = re.compile(r'#[0-9A-Fa-f]{6}')

time_wait = dt.timedelta(minutes=1)

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
# all_map = [['#FFFFFF' for i in range(100)] for i in range(100)]
# all_map = r.json().get('map')



schema_user = (
    TextField("$.username", as_name="username"),
    TextField("$.password_hash", as_name="password_hash"),
    TextField("$.password_salt", as_name="password_salt"),
    TextField('$.datetime_last_click', as_name='datetime_last_click'),
    NumericField("$.verify", as_name="verify"),
)

schema_click = (
    TextField("$.username", as_name="username"),
    TextField("$.datetime", as_name="datetime"),
    TextField("$.color", as_name="color"),
    NumericField("$.x", as_name="x"),
    NumericField("$.y", as_name="y"),
)

schema_cells = (
    TextField("$.color", as_name="color"),
    TextField("$.x", as_name="x"),
    TextField("$.y", as_name="y"),
)


users_index = r.ft("idx:users")
clicks_index = r.ft("idx:clicks")


def get_random_salt():
    ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    chars=[]
    for i in range(8):
        chars.append(random.choice(ALPHABET))
    return "".join(chars)

def sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

# def save_map():
#     r.json().set('map', Path.root_path(), all_map)

@app.route('/', methods=['POST', 'GET', 'HEAD'])
def index():
    if request.method == 'HEAD':
        # save_map()
        ...

    if session.get('username') is None:
        return redirect(url_for('login'))

    return redirect(url_for('page_map'))


            
            


@app.route('/map', methods=['POST', 'GET'])
def page_map():
    if request.method == "GET":
        if session.get('username') is None:
            return redirect(url_for('login'))
        
        username = session.get('username')
        res = users_index.search(Query(f"@username:'{username}'"))
        if res.total > 1:
            logging.error(f'ERROR: req "@username:{username}"')
        
        doc_res = res.docs[0]
        json_res = json.loads(doc_res.json)

        return render_template('map.html', colors=colors, timer=json_res['datetime_last_click'])
    else:
        return jsonify({'ok': True, 'map': r.json().get('map')})


@app.route('/login', methods = ['POST', 'GET'])
def login():
    try:
        if request.method == 'GET':
            username = request.cookies.get('username')
            password = request.cookies.get('password')

            if username and password:
                res = users_index.search(Query(f"@username:'{username}'"))
                if res.total > 1:
                    logging.error(f'ERROR: req "@username:{username}"')

                if res.total:
                    doc_res = res.docs[0]
                    json_res = json.loads(doc_res.json)

                    if sha256(f'{password}:{json_res.get("password_salt")}') == json_res.get('password_hash') and json_res.get('verify'):
                        session['username'] = username
                        return redirect(url_for('index'))



            if 'username' in session:
                return redirect(url_for('index'))

            return render_template('login.html')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
            if username and password:
                if not isinstance(username, str):
                    logging.ERROR(f'{username}, {type(username)}')
                    return render_template('login.html', answer="что то пошло не так, напишите в поддержку @artemki77", username=username, password=password)
                username = username.lower()

                if username[0] == '@':
                    username = username[1:]

                res = users_index.search(Query(f"@username:'{username}'"))
                if not res.total:
                    return render_template('login.html', answer="Not such user", username=username, password=password)
                else:
                    if res.total > 1:
                        logging.ERROR(f'ERROR: req "@username:{username}"')
                    
                    doc_res = res.docs[0]
                    json_res = json.loads(doc_res.json)

                    if sha256(f'{password}:{json_res.get("password_salt")}') == json_res.get('password_hash'):
                        if not json_res.get('verify'):
                            return render_template('login.html', answer="Ваш аккаунт ещё не верифицирован, вы можете это сделать в @PixelVerify_bot", username=username, password=password)
                        else:
                            session['username'] = username
                            resp = make_response(redirect(url_for('index')))
                            resp.set_cookie('username',
                                        username,
                                        max_age=60 * 60 * 24 * 365 * 2)
                            resp.set_cookie('password',
                                            password,
                                            max_age=60 * 60 * 24 * 365 * 2)
                            return resp
                    else:
                        return render_template('login.html', answer="Пароль неправильный", username=username, password=password)
            else:
                return render_template('login.html', answer="что то пошло не так, попробуйте ещё раз или обратитесь к @artemki77", username=username, password=password)
    except Exception as e:
        logging.error(str(e))
        return render_template('login.html', answer="что то пошло не так, попробуйте ещё раз или обратитесь к @artemki77", username=username, password=password)

@app.route('/signup', methods = ['POST', 'GET'])
def signup():
    try:
        if request.method == 'GET':

            return render_template('signup.html', answer='регистрация на этом сайте происходит через телеграмм, укажите свой никнейм в тг и потом через бота(@PixelVerify_bot) подтвердите его')
        
        else:
            username = request.form.get('username')
            password = request.form.get('password')
            if username and password:
                if username[0] == '@':
                    username = username[1:]
                
                username = username.lower()

                res = users_index.search(Query(f"@username:'{username}'"))

                if res.total > 1:
                    logging.ERROR(f'ERROR: req "@username:{username}"')

                if res.total:
                    return render_template('signup.html', answer='Пользователь с этим ником уже существует', username=username, password=password)
                else:
                    new_index_user = r.incr('idx:users')
                    salt = get_random_salt()
                    user = {
                        "username": username.lower(),
                        "password_hash": sha256(f'{password}:{salt}'),
                        "password_salt": salt,
                        "datetime_last_click": dt.datetime.isoformat(dt.datetime.now()),
                        "verify": 0
                    }

                    r.json().set(f"user:{new_index_user}", Path.root_path(), user)

                    return render_template('login.html', answer='Перед тем как войти вы должны подтвердить свой аккаунт через телеграмм бота @PixelVerify_bot', username=username, password=password)
                    
            else:
                return render_template('signup.html', answer='что то пошло не так, попробуйте ещё раз или обратитесь к @artemki77', username=username, password=password)
    except Exception as e:
        logging.error(str(e))
        return render_template('signup.html', answer='что то пошло не так, попробуйте ещё раз или обратитесь к @artemki77', username=username, password=password)


@app.route('/click', methods = ['POST'])
def click():
    try:
        if session.get('username') is None:
            return redirect(url_for('login'))

        
        req_json = request.json


        if not patern_color.findall(req_json.get('color', '')):
            return jsonify({'ok': False, 'result': 'ERROR with color'})

        username = session.get('username')
        res = users_index.search(Query(f"@username:'{username}'"))
        doc_res = res.docs[0]
        user_json = json.loads(doc_res.json)

        if dt.datetime.now() - dt.datetime.fromisoformat(user_json.get('datetime_last_click')) > time_wait or username in ['artemki77']:
            r.json().set(doc_res.id, '$.datetime_last_click', dt.datetime.isoformat(dt.datetime.now()))
            res = r.json().set('map', Path(f"[{req_json.get('y')}][{req_json.get('x')}]"), req_json.get('color'))

            new_index_click = r.incr('idx:clicks')
            click = {
                        "username": username.lower(),
                        "datetime": dt.datetime.isoformat(dt.datetime.now()),
                        "color": req_json.get('color'),
                        "x": int(req_json.get('x')),
                        "y": int(req_json.get('y'))
                    }
            
            r.json().set(f"click:{new_index_click}", Path.root_path(), click)

            return jsonify({'ok': True, 'result': 'SUCCESS', 'params': {
                'x': int(req_json.get('x')),
                'y': int(req_json.get('y')),
                'color': req_json.get('color')
            }})
        else:
            return jsonify({'ok': False, 'result': '5 min has not passed', "last_time": user_json.get('datetime_last_click')})
    except Exception as e:
        logging.error(f'ERROR CLICK {e}')
        return jsonify({'ok': False, 'result': 'error'})

        


@app.route('/logout')
def logout():
    session.clear()
    resp = make_response(redirect("/login"))

    resp.set_cookie('username', '', expires=0)
    resp.set_cookie('password', '', expires=0)
    
    return resp



if __name__ == "__main__":
    app.run('0.0.0.0', 8000, debug=True)