import asyncio
import os
import time
from functools import partial
from logging import INFO, Logger
from typing import Optional

import requests
from fastapi import FastAPI
from PIL import Image
from pywebio.input import *
from pywebio.output import *
from pywebio.platform.fastapi import webio_routes
from pywebio.session import eval_js, run_async, run_js
from uvicorn import Config, Server

from adapter import Adapter
import notice
from database import danmuDB, liveDB
from WebHandler import LinkedList, get_default_handler

app = FastAPI()
esu = Image.open('esu.png')
forever = Image.open('forever.png')


@app.get("/uid/{uid}")
def cha_uid(uid: int, q: Optional[str] = None):
    dms = danmuDB.query('ROOM,TIME,USERNAME,MSG,ST', True, UID=uid)
    count = 0
    resp = []
    lives = {}
    for room, time, username, msg, st in dms[::-1]:
        if msg:
            count += 1
        if not st:
            resp.append({'room': room, 'room_info': False, 'time': time, 'username': username, 'msg': msg})
        else:
            danmaku = lives.get((room, st))
            if not danmaku:
                lives[(room, st)] = []
                danmaku = lives[(room, st)]
                resp.append({'room': room, 'room_info': liveDB.query(room, st), 'danmaku': danmaku})
            danmaku.append({'time': time, 'username': username, 'msg': msg})
    return {'status': 0, 'total': count, 'danmaku': resp}


# 查某个房间的总直播数据(无弹幕)
@app.get("/live/{roomid}")
def cha_lives(roomid: int, q: Optional[str] = None):
    lives = liveDB.query(room_id=roomid, all=True)
    if lives:
        return {'status': 0, 'total': len(lives), 'lives': lives}
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
        if not live['sp']:
            live['sp'] = time.time()
        live['danmaku'] = danmuDB.query_room(roomid, live['st'], live['sp'])
        return {'status': 0, 'live':live}
    else:
        return {'status': '房间号不正确'}


def code():
    '遍历运行目录并打印所有python源码'
    widgets = []
    widgets.append(put_markdown('## 😰你知道我长什么样 来找我吧').onclick(partial(run_js, code_='''tempwindow=window.open();
                                                              tempwindow.location="https://github.com/Drelf2018";''')))
    widgets.append(put_code(f'# 监听直播间列表 如有新增需要 B站联系@脆鲨12138\nroom_ids = {room_ids}', 'python'))
    for root, folders, files in os.walk('.'):
        for file in files:
            if file.split('.')[-1] == 'py':
                with open(file, 'r', encoding='utf-8') as fp:
                    code_str = fp.read()
                    widgets.append(put_collapse(file, put_code(code_str, 'python')))
    return widgets


async def index():
    '狠狠查他弹幕'

    # 按钮点击事件
    async def onclick():
        uid = await eval_js('prompt("输入查询用户uid")')
        # run_js(f'window.open("./uid/{value}")')
        if uid.isdigit:
            js = cha_uid(uid)
        else:
            return

        def t2s(timenum, format='%H:%M:%S'):
            return time.strftime(format, time.localtime(timenum))

        clear('query_scope')

        first = True
        danmaku = js['danmaku']
        for dm in danmaku:
            if not dm['room_info']:
                put_markdown(f'{t2s(dm["time"])} [{dm["room"]}] <a href="https://space.bilibili.com/{uid}">{dm["username"]}</a> {dm["msg"]}', scope='query_scope')
            else:
                room_info = dm['room_info']
                danmaku2 = dm['danmaku']
                r = requests.get(room_info['cover'])
                if not first:
                    put_markdown('---', scope='query_scope')
                put_row([
                    put_image(notice.circle_corner(r.content), format='png'),
                    None,
                    put_column([
                        put_markdown('### {username}【{title}】'.format_map(room_info)),
                        put_markdown(f'<font color="grey">开始</font> __{t2s(room_info["st"], "%Y-%m-%d %H:%M:%S")}__ <font color="grey">结束</font> __{t2s(room_info["sp"], "%Y-%m-%d %H:%M:%S")}__')
                    ])
                ], size='10fr 1fr 30fr', scope='query_scope')
                for dm2 in danmaku2:
                    put_markdown(f'{t2s(dm2["time"])} <a href="https://space.bilibili.com/{uid}">{dm2["username"]}</a> {dm2["msg"]}', scope='query_scope')
                put_markdown('---', scope='query_scope')
            first = False

    put_markdown('# 😎个人用弹幕记录站 / api.nana7mi.link')
    put_tabs([
        {'title': '终端', 'content': put_scrollable(put_scope('background'), height=510, keep_bottom=True)},
        {'title': '源码', 'content': code()},
        {'title': '私货', 'content': [
            put_html('''
                <iframe src="//player.bilibili.com/player.html?aid=78090377&bvid=BV1vJ411B7ng&cid=133606284&page=1"
                    width="100%" height="550" scrolling="true" border="0" frameborder="no" framespacing="0" allowfullscreen="true">
                </iframe>'''),
            put_markdown('#### <font color="red">我要陪你成为最强直播员</font>'),
            put_image(forever, format='png'),
        ]},
        {'title': '公告', 'content': notice.notice()},
        {'title': '查询', 'content': [
            put_image(esu, format='png', width='100%'),
            put_markdown('---'),
            put_button('😋查', onclick=onclick),
            put_markdown('*<font color="grey">请在“结果”标签页查看查询信息</color>*')
        ]},
        {'title': '结果', 'content': put_scope('query_scope')}
    ]).style('border:none;')  # 取消 put_tabs 的边框

    run_async(refresh_msg(loglist))  # 刷新消息


async def refresh_msg(loglist: LinkedList, sleeptime: float = 0.33):
    '刷新并打印消息'
    count = 0
    node = loglist.getTrueHead()
    while True:
        count += 1
        if count >= 10/sleeptime:
            logger.debug('Heartbeat')
            count = 0
        await asyncio.sleep(sleeptime)
        while node.getNext():  # 遍历并打印节点内容到网页
            try:
                node = node.getNext()
                put_markdown(node.getValue(), sanitize=True, scope='background')
            except Exception as e:
                toast(f'refresh_msg Error: {e}', 5, color='error')


logger = Logger('MAIN', INFO)
loglist, handler = get_default_handler(50)
logger.addHandler(handler)

app.mount('/', FastAPI(routes=webio_routes([index])))

room_ids = [
    21452505, 80397, 22778610,
    22637261, 22625025, 22632424, 22625027
]

loop = asyncio.get_event_loop()
loop.create_task(Adapter(logger).run(room_ids))
config = Config(app, loop=loop, host="0.0.0.0", port=80, reload=True, debug=True)
server = Server(config=config)
loop.run_until_complete(server.serve())
