import asyncio
import os
import random
import time
from functools import partial
from typing import Optional

from aiohttp import ClientSession
from fastapi import FastAPI
from PIL import Image
from pywebio import config
config(js_code='''$("body").prepend('<nav class="navbar navbar-dark bg-dark"><div class="container"><a href="/night" class="router-link-active router-link-exact-active navbar-brand">😎</a><a href="/cha"><img src="https://api.nana7mi.link/pic" height="40px"></a><a href="/fans" class="router-link-active router-link-exact-active navbar-brand">🛒</a></div></nav>')''')
from pywebio.input import *
from pywebio.output import *
from pywebio.platform.fastapi import webio_routes
from pywebio.session import defer_call, eval_js
from pywebio.session import run_asyncio_coroutine as rac
from pywebio.session import run_js
from uvicorn import Config, Server

import notice
from database import danmuDB, liveDB

import sys
sys.path.insert(0, '..\\web-Automatic-Goodnight-Algorithm')
from app import index, admin
sys.path.insert(0, '..\\web-fans')
from fans import index as fans

app = FastAPI()
esu = Image.open('esu.png')  # 查询页面配图
forever = Image.open('forever.png')  # 私活页面配图


# 查某用户在记录中所有弹幕
@app.get("/uid/{uid}")
def cha_uid(uid: int, q: Optional[str] = None):
    dms = danmuDB.query('roomid,time,username,msg,cmd,st', True, True, UID=uid)
    count = 0  # 弹幕数记录
    resp = []
    lives = {}
    for room, time, username, msg, msg_type, st in dms:  # 倒序输出
        if msg_type == 'DANMU_MSG':
            count += 1
        if not st:  # 没有 st 表示是在下播时发送的弹幕 直接添加进 resp
            resp.append({'room': room, 'room_info': False, 'time': time, 'username': username, 'msg': msg, 'msg_type': msg_type})
        else:  # 用 (room, st) 作为 key 选出一个弹幕列表，把该用户在该场直播中所有弹幕添加在这个列表里
            danmaku = lives.get((room, st))
            if not danmaku:
                lives[(room, st)] = []
                danmaku = lives[(room, st)]
                # 将这个直播间信息和该用户在这场直播的所有弹幕存进 resp
                resp.append({'room': room, 'room_info': liveDB.query(room, st), 'danmaku': danmaku})
            danmaku.append({'time': time, 'username': username, 'uid': uid, 'msg': msg, 'msg_type': msg_type})
    return {'status': 0, 'total': count, 'danmaku': resp}


# 查某个房间的总直播数据(无弹幕)
@app.get("/live/{roomid}")
def cha_lives(roomid: int, q: Optional[str] = None):
    lives = liveDB.query(room_id=roomid, all=True)
    if lives:
        return {'status': 0, 'total': len(lives), 'lives': lives[::-1]}
    else:
        return {'status': '房间号不正确'}


# 查具体某场直播数据(有弹幕)
@app.get("/live/{roomid}/{pos}")
def cha_live(roomid: int, pos: str, q: Optional[str] = None):
    if pos == 'last':
        pos = -1
    elif pos.replace('-', '').replace('+', '').isdigit():
        pos = int(pos)
    else:
        return {'status': '场次码不正确'}
    try:
        live = liveDB.query(room_id=roomid, all=True)[pos]
    except Exception as e:
        return {'status': '应该是超出总场次数了', 'exception': str(e)}
    if live:
        if not live['sp']:  # 直播中
            live['sp'] = round(time.time())
        # 统计弹幕数，礼物、大航海、SuperChat 等金额
        live.update({'total': 0, 'send_gift': 0, 'guard_buy': 0, 'super_chat_message': 0})
        live['danmaku'] = list(danmuDB.query_room(roomid, live['st'], live['sp']))
        for dm in live['danmaku']:
            if dm['type'] == 'DANMU_MSG':
                live['total'] += 1
            else:
                live[dm['type'].lower()] += dm['price']
        return {'status': 0, 'live':live}
    else:
        return {'status': '房间号不正确'}


def code():
    '遍历运行目录并打印所有python源码'
    widgets = []
    widgets.append(put_markdown('## 😰你知道我长什么样 来找我吧').onclick(partial(run_js, code_='tw=window.open();tw.location="https://github.com/Drelf2018";')))
    widgets.append(put_code(f'# 监听直播间列表 如有新增需要 B站联系@脆鲨12138\nroom_ids = {room_ids}', 'python'))
    for root, folders, files in os.walk('.'):  # 遍历打印当前目录下所有 python 脚本
        for file in files:
            if file.endswith('.py'):
                with open(file, 'r', encoding='utf-8') as fp:
                    code_str = fp.read()
                    widgets.append(put_collapse(file, put_code(code_str, 'python')))
        break
    return widgets


async def cha():
    '狠狠查他弹幕'

    session = ClientSession()

    @defer_call
    def onclose():
        loop.create_task(session.close())

    # 按钮点击事件
    async def onclick(btn):
        # 时间戳转指定格式
        def t2s(timenum: int, format: str = '%H:%M:%S') -> str:
            if timenum is None:
                return '直播中'
            elif timenum == 0:
                return 0
            if len(str(timenum)) > 10:
                timenum //= 1000
            return time.strftime(format, time.localtime(timenum))

        # 打印直播场次信息
        async def put_live(room_info: dict):
            try:
                r = await rac(session.get(room_info['cover']))  # 获取直播封面
                content = await rac(r.read())
            except Exception as e:
                # 开了魔法这里会报错
                toast(f'又是这里报错 Exception: {e} line: {e.__traceback__.tb_lineno}', 0, color='error')
            put_row([
                put_image(notice.circle_corner(content), format='png'),
                None,
                put_column([
                    put_markdown('### {username}【{title}】'.format_map(room_info)),
                    put_markdown(f'<font color="grey">开始</font> __{t2s(room_info["st"], "%Y/%m/%d %H:%M:%S")}__ <font color="grey">结束</font> __{t2s(room_info["sp"], "%Y/%m/%d %H:%M:%S")}__')
                ])
            ], size='10fr 1fr 30fr', scope='query_scope')

        async def check_scope(room_info: dict):
            scope = str(room_info['st'])
            if not used_scope.get(scope):
                # 将所有弹幕连接成一个长字符串
                danma_str = '\n\n'.join([f'{t2s(dm["time"])} <a href="https://space.bilibili.com/{dm["uid"]}">{dm["username"]}</a> {dm["msg"]}'
                                            for dm in danmuDB.query_room(room_info['room'], room_info['st'], room_info['sp'])])
                put_markdown(danma_str, scope=scope)
                used_scope[scope] = True

        # 打印弹幕列表
        async def put_danmaku(room_info: dict, danmaku: list, scope: str = 'query_scope'):
            await put_live(room_info)  # 先打印直播信息
            if not scope:
                put_collapse('弹幕列表', put_scope(str(room_info['st'])), scope='query_scope').onclick(partial(check_scope, room_info=room_info))
            else:
                danma_str = '\n\n'.join([f'{t2s(dm["time"])} <a href="https://space.bilibili.com/{dm["uid"]}">{dm["username"]}</a> {dm["msg"]}'
                                            for dm in danmaku])
                put_markdown(danma_str, scope=scope)
            put_markdown('---', scope='query_scope')

        clear('query_scope')

        if btn == '😋查发言':
            uid = await eval_js('prompt("输入查询用户uid")')
            if uid.isdigit:
                js = cha_uid(uid)
            else:
                toast('输入不正确', 3, color='error')
                return

            first = True  # 标识符 用来判断是否打印分割线
            danmaku = js['danmaku']
            for dm in danmaku:
                if not dm['room_info']:  # 没有 room_info 表示下播时发送的弹幕 直接打印
                    first = False
                    put_markdown(f'{t2s(dm["time"], "%Y/%m/%d %H:%M:%S")} [{dm["room"]}] <a href="https://space.bilibili.com/{uid}">{dm["username"]}</a> {dm["msg"]}', scope='query_scope')
                else:
                    if not first:
                        put_markdown('---', scope='query_scope')
                    first = True
                    await put_danmaku(dm['room_info'], dm['danmaku'])

        elif btn == '🍜查直播':
            roomid = await eval_js('prompt("输入查询直播间号")')
            lives = liveDB.query(room_id=roomid, all=True)
            if lives:
                used_scope = {}
                for live in lives[::-1]:
                    await put_danmaku(live, danmaku=None, scope=None)


    quotations = [
        '你们会无缘无故的说好用，就代表哪天无缘无故的就要骂难用',
        '哈咯哈咯，听得到吗',
        '还什么都没有更新，不要急好嘛',
        '直播只是工作吗直播只是工作吗直播只是工作吗？'
    ]

    put_markdown(f'# 😎 api.nana7mi.link <font color="grey" size=4>*{random.choice(quotations)}*</font>')
    put_tabs([
        {'title': '查询', 'content': [
            put_image(esu, format='png').onclick(partial(run_js, code_='tw=window.open();tw.location="https://www.bilibili.com/video/BV1pR4y1W7M7";')),
            put_buttons(['😋查发言', '🍜查直播'], onclick=onclick),
            put_scope('query_scope')
        ]},
        {'title': '公告', 'content': notice.notice()},
        {'title': '源码', 'content': code()},
        {'title': '私货', 'content': [
            put_html('''
                <iframe src="//player.bilibili.com/player.html?aid=78090377&bvid=BV1vJ411B7ng&cid=133606284&page=1"
                    width="100%" height="550" scrolling="true" border="0" frameborder="no" framespacing="0" allowfullscreen="true">
                </iframe>'''),
            put_markdown('#### <font color="red">我要陪你成为最强直播员</font>'),
            put_image(forever, format='png'),
        ]}
    ]).style('border:none;')  # 取消 put_tabs 的边框


app.mount('/cha', FastAPI(routes=webio_routes(cha), cdn='/html'))  # 绑定应用到网页根目录
app.mount('/night', FastAPI(routes=webio_routes([index, admin]), cdn='/html'))
app.mount('/fans', FastAPI(routes=webio_routes(fans), cdn='/html'))

room_ids = [
    21452505, 80397, 22778610,
    22637261, 22625025, 22632424, 22625027
]  # 监听中直播间号


loop = asyncio.get_event_loop()
# config = Config(app, loop=loop, port=80)
config = Config(app, loop=loop, host="0.0.0.0", port=443, debug=True, ssl_keyfile='../api/8032637_api.drelf.cn.key', ssl_certfile='../api/8032637_api.drelf.cn.pem')
server = Server(config=config)
loop.run_until_complete(server.serve())
