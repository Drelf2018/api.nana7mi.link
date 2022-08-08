import os
import random
import subprocess
import threading
import time
from functools import partial
from io import BytesIO
from typing import Optional

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from PIL import Image
from pywebio.input import *
from pywebio.output import *
from pywebio.platform.fastapi import webio_routes
from pywebio.session import eval_js
from pywebio.session import run_asyncio_coroutine as rac
from pywebio.session import run_js

import notice
from night.app import admin
from night.app import index as night

app = FastAPI()
esu = Image.open('esu.png')  # 查询页面配图
forever = Image.open('forever.png')  # 私活页面配图

def code():
    '打印 python 源码'
    with open(__file__, 'r', encoding='utf-8') as fp:
        code = fp.read()
    return [
        put_markdown('## 😰你知道我长什么样 来找我吧').onclick(
            lambda: run_js(code_='tw=window.open();tw.location="https://github.com/Drelf2018/api.nana7mi.link";')
        ),
        put_code(code, 'python')
    ]

def t2s(timenum: int, format: str = '%H:%M:%S') -> str:
    '时间戳转指定格式'
    if timenum is None:
        return '直播中'
    elif timenum == 0:
        return 0
    if len(str(timenum)) > 10:
        timenum //= 1000
    return time.strftime(format, time.localtime(timenum))

# 打印直播场次信息
def put_live(room_info: dict, pos: int):
    if not os.path.exists('cover\\{room}_{st}.png'.format_map(room_info)):
        try:
            if room_info['cover']:
                r = httpx.get(room_info['cover'])  # 获取直播封面
                img = Image.open(BytesIO(r.content))
                img = img.resize((200, int(img.height*200/img.width)))
                img.save('cover\\{room}_{st}.png'.format_map(room_info))
        except Exception as e:
            # 开了魔法这里会报错
            toast(f'又是这里报错 Exception: {e} line: {e.__traceback__.tb_lineno}', 0, color='error')
    room_info["rst"], room_info["rsp"] = t2s(room_info["st"], "%Y/%m/%d %H:%M:%S"), t2s(room_info["sp"], "%Y/%m/%d %H:%M:%S")
    put_html('''
    <div style="display: grid; grid-auto-flow: column; grid-template-columns: 10fr 1fr 30fr;" class="pywebio-clickable">
        <a href="{cover}"><img src="/cover/{room}/{st}" alt></a>
        <div></div>
        <div style="display: grid; grid-auto-flow: row; grid-template-rows: 1fr 1fr;">
            <h3 id="{username}-{title}">{username} {title}</h3>
            <p><font color="grey">开始</font> <strong>{rst}</strong> <font color="grey">结束</font> <strong>{rsp}</strong></p>
        </div>
    </div>
    '''.format_map(room_info), scope='query_scope').onclick(partial(reload_live, room_info=room_info, url=f'http://localhost:5762/live/{room_info["room"]}/{pos}', pos=pos))

async def reload_live(room_info, url: str, pos: int):
    clear('query_scope')
    put_markdown('弹幕加载中', scope='query_scope')
    session = httpx.AsyncClient()
    with put_loading('border', 'primary'):
        resp = await rac(session.get(url))
        js = resp.json()
        if js['status'] != 0:
            toast('运行时错误：'+js['status'], 3, color='error')
            return
        danmaku = js['live']['danmaku']
        clear('query_scope')
    put_live(room_info, pos)
    temp = '%s <a href="https://space.bilibili.com/%d">%s</a> %s\n\n'
    danma_str = ''.join([temp % (t2s(dm["time"]), dm["uid"], dm["username"], dm["msg"]) for dm in danmaku])
    put_markdown(danma_str, scope='query_scope')

# 打印弹幕列表
async def put_danmaku(room_info: dict, danmaku: list, flag: bool = False):
    put_live(room_info, danmaku)  # 先打印直播信息
    if flag:
        danma_str = '\n\n'.join([f'{t2s(dm["time"])} <a href="https://space.bilibili.com/{dm["uid"]}">{dm["username"]}</a> {dm["msg"]}'
                                    for dm in danmaku])
        put_markdown(danma_str, scope='query_scope')
        put_markdown('---', scope='query_scope')

# 按钮点击事件
async def onclick(btn):
    clear('query_scope')
    session = httpx.AsyncClient()
    try:
        if btn == '😋查发言':
            uid = await input('输入查询用户 uid')
            if uid and uid.isdigit:
                try:
                    resp = await rac(session.get(f'http://localhost:5762/uid/{uid}'))
                except Exception as e:
                    toast(f'运行时错误：{e}', 3, color='error')
                    return
                js = resp.json()
            else:
                toast('输入不正确', 3, color='error')
                return
            first = True  # 标识符 用来判断是否打印分割线
            danmaku = js['danmaku']
            for dm in danmaku:
                if not dm['room_info']:  # 没有 room_info 表示下播时发送的弹幕 直接打印
                    first = False
                    put_markdown(f'{t2s(dm["time"], "%Y/%m/%d %H:%M:%S")} <a href="https://live.bilibili.com/{dm["room"]}">[{dm["room"]}]</a> <a href="https://space.bilibili.com/{uid}">{dm["username"]}</a> {dm["msg"]}', scope='query_scope')
                else:
                    if not first:
                        put_markdown('---', scope='query_scope')
                    first = True
                    await put_danmaku(dm['room_info'], dm['danmaku'], True)

        elif btn == '🍜查直播':
            roomid = await input('输入查询直播间号')
            if roomid and roomid.isdigit:
                resp = await rac(session.get(f'http://localhost:5762/live/{roomid}'))
                js = resp.json()
                if js['status'] == 0:
                    n = len(js['lives']) - 1
                    for pos, live in enumerate(js['lives']):
                        await put_danmaku(live, danmaku=n-pos)
            else:
                toast('输入不正确', 3, color='error')
    except Exception as e:
        toast(f'运行时错误：{e}', 3, color='error')
        return

async def cha():
    '狠狠查他弹幕'

    quotations = [
        '你们会无缘无故的说好用，就代表哪天无缘无故的就要骂难用',
        '哈咯哈咯，听得到吗',
        '还什么都没有更新，不要急好嘛',
        '直播只是工作吗直播只是工作吗直播只是工作吗？'
    ]
    put_markdown(f'# 😎 api.nana7mi.link <font color="grey" size=4>*{random.choice(quotations)}*</font>')
    put_image(esu, format='png').onclick(partial(run_js, code_='window.open().location="https://www.bilibili.com/video/BV1pR4y1W7M7";')),
    put_buttons(['😋查发言', '🍜查直播'], onclick=onclick),
    put_scope('query_scope')
    try:
        session = httpx.AsyncClient()
        resp = await rac(session.get('http://localhost:5762/rooms'))
        js = resp.json()
        if isinstance(js['rooms'], list):
            [put_live(room, -1)for room in js['rooms']]
        else:
            toast(f'运行时错误：{js["rooms"]}', 3, color='error')
    except Exception as e:
        print(e, e.__traceback__.tb_lineno, resp.content)
        toast(f'运行时错误：{e.__traceback__.tb_lineno} {e}', 3, color='error')

async def about():
    '关于'
    put_tabs([
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

# 返回图片
@app.get("/eyes")
def eyes():
    file_like = open('eyes.png', mode="rb")
    return StreamingResponse(file_like, media_type="image/jpg")

# 查具体某场直播数据(有弹幕)
@app.get("/cover/{roomid}/{st}")
def cover(roomid: int, st: int, q: Optional[str] = None):
    try:
        file_like = open(f'cover\\{roomid}_{st}.png', mode="rb")
        return StreamingResponse(file_like, media_type="image/jpg")
    except Exception:
        return {'status': '未找到封面'}

app.mount('/', FastAPI(routes=webio_routes({'index': cha, 'about': about, 'night': night, 'admin': admin})))

def run_python(filepath: str, port: int, callback=print, hook=print):
    folder_path = os.path.dirname(filepath)
    subp = subprocess.Popen('python '+filepath, cwd=folder_path, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while not subp.poll():
        try:
            try:
                bt = subp.stdout.readline()
            except ValueError:
                hook(f'bt = subp.stdout.readline() 这行错了，原因我不清楚，好像是 ValueError ({port})')
                continue
            line = str(bt, encoding='utf-8').strip()
        except UnicodeDecodeError:
            hook(f'line = str(bt, encoding="utf-8").strip() 这行错了，原因我不清楚，好像是 UnicodeDecodeError ({port})')
            continue
        if line:
            callback(f'{line} ({port})')

if __name__ == '__main__':
    threading.Thread(target=run_python, args=('.\\api.py', 5762)).start()
    threading.Thread(target=run_python, args=('.\\http_redirect.py', 80)).start()
    uvicorn.run(app='cha:app', host="0.0.0.0", port=443, ssl_keyfile='../api/8032637_api.drelf.cn.key', ssl_certfile='../api/8032637_api.drelf.cn.pem')
