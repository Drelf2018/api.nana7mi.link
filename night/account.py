from night.liteDB import userDB
from pywebio.session import eval_js, run_js
from tornado.web import create_signed_value, decode_signed_value


with open('.\\night\\key.txt', 'r', encoding='utf-8') as fp:
    SECRET = fp.read()

async def get():
    token = await eval_js("localStorage.getItem(key)", key='token')  # get token from user's web browser
    username = decode_signed_value(SECRET, 'token', token, max_age_days=7)  # try to decrypt the username from the token
    if username:
        username = username.decode('utf-8')
        pwd = userDB.query('PASSWORD', USERNAME=username)
        if not pwd:
            return
    return username

def save(username):
    signed = create_signed_value(SECRET, 'token', username).decode("utf-8")  # encrypt username to token
    run_js("localStorage.setItem(key, value)", key='token', value=signed)  # set token to user's web browser

def clear():
    save('')
