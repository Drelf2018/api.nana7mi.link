import random
import time
from functools import partial
import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from PIL import Image
from pywebio.input import *
from pywebio.output import *
from pywebio.platform.fastapi import webio_routes
from pywebio.session import run_asyncio_coroutine as rac
from pywebio.session import run_js
from pywebio_battery import get_query
import notice

app = FastAPI()
esu = Image.open('esu.png')  # 查询页面配图
forever = Image.open('forever.png')  # 私活页面配图
BASEURL = 'http://localhost:5762'

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
def put_live(room_info: dict, pos: int = None):
    rst, rsp = t2s(room_info["st"], "%Y/%m/%d %H:%M:%S"), t2s(room_info["sp"], "%Y/%m/%d %H:%M:%S")
    put_row([
        put_image(room_info['cover']+'@196w.webp', width='196px').style("border-radius:10px"),
        None,
        put_column([
            put_markdown('### {username} {title}'.format_map(room_info)),
            put_markdown(f'<font color="grey">开始</font> __{rst}__ <font color="grey">结束</font> __{rsp}__')
        ])
    ], size='10fr 1fr 30fr', scope='query_scope').onclick(partial(reload_live, room_info=room_info, pos=pos))

async def reload_live(room_info, pos: int = None):
    if pos is None:
        return
    clear('query_scope')
    with put_loading('border', 'primary'):
        try:
            session = httpx.AsyncClient(timeout=30.0)
            resp = await rac(session.get(f'{BASEURL}/live/{room_info["room"]}/{pos}', timeout=20.0))
        except Exception as e:
            put_markdown(f'### 获取弹幕超时 {e}', scope='query_scope')
            return
        else:
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
async def put_danmaku(room_info: dict, danmaku: list, pos: int = None):
    put_live(room_info, pos)  # 先打印直播信息
    danma_str = '\n\n'.join([f'{t2s(dm["time"])} <a href="https://space.bilibili.com/{dm["uid"]}">{dm["username"]}</a> {dm["msg"]}'
                                for dm in danmaku])
    put_markdown(danma_str, scope='query_scope')
    put_markdown('---', scope='query_scope')

# 按钮点击事件
async def onclick(btn):
    clear('query_scope')
    try:
        if btn == '😋查发言':
            uid = await input('输入查询用户 uid')
            await user(uid)
        elif btn == '🍜查直播':
            roomid = await input('输入查询直播间号')
            if roomid and roomid.isdigit:
                await lives(roomid)
            else:
                toast('输入不正确', 3, color='error')
    except Exception as e:
        toast(f'运行时错误：{e}', 3, color='error')

async def user(uid: str = ''):
    '用户弹幕'
    session = httpx.AsyncClient(timeout=30.0)
    if uid == '':
        uid = await get_query('uid')
        put_scope('query_scope')
    if uid and uid.isdigit:
        try:
            resp = await rac(session.get(f'{BASEURL}/uid/{uid}', timeout=20.0))
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
            await put_danmaku(dm['room_info'], dm['danmaku'])

async def lives(roomid: str = ''):
    '直播记录'
    session = httpx.AsyncClient(timeout=30.0)
    if roomid == '':
        roomid = await get_query('roomid')
        put_scope('query_scope')
    if pos := await get_query('position'):
        with put_loading('border', 'primary'):
            resp = await rac(session.get(f'{BASEURL}/live/{roomid}/{pos}', timeout=50.0))
        js = resp.json()
        if js['status'] == 0:
            await put_danmaku(js['live'], js['live'].pop('danmaku'))
    else:
        resp = await rac(session.get(f'{BASEURL}/live/{roomid}', timeout=20.0))
        js = resp.json()
        if js['status'] == 0:
            n = len(js['lives']) - 1
            for pos, live in enumerate(js['lives']):
                put_live(live, n-pos)

async def index():
    '狠狠查他弹幕'

    quotations = [
        '你们会无缘无故的说好用，就代表哪天无缘无故的就要骂难用',
        '哈咯哈咯，听得到吗',
        '还什么都没有更新，不要急好嘛',
        '直播只是工作吗直播只是工作吗直播只是工作吗？'
    ]
    put_markdown(f'# 😎 nana7mi.link <font color="grey" size=4>*{random.choice(quotations)}*</font>')
    put_image(esu, format='png').onclick(lambda: run_js('window.open().location="https://www.bilibili.com/video/BV1pR4y1W7M7";')),
    put_buttons(['😋查发言', '🍜查直播'], onclick=onclick),
    put_scope('query_scope')
    try:
        session = httpx.AsyncClient(timeout=30.0)
        resp = await rac(session.get(f'{BASEURL}/rooms', timeout=20.0))
        js = resp.json()
        if isinstance(js['rooms'], list):
            for room in js['rooms']:
                put_live(room, -1)
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

app.mount('/', FastAPI(routes=webio_routes([index, about, lives, user])))

if __name__ == '__main__':
    uvicorn.run(app=app, host="0.0.0.0", port=5761)
