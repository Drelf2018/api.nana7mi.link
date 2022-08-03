import random
import time
from functools import partial

import httpx
import uvicorn
from fastapi import FastAPI
from PIL import Image
from pywebio.input import *
from pywebio.output import *
from pywebio.platform.fastapi import webio_routes
from pywebio.session import eval_js, run_js, run_asyncio_coroutine as rac

import notice

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

# 按钮点击事件
async def onclick(btn):

    # 打印直播场次信息
    async def put_live(room_info: dict, pos: int):
        try:
            r = await rac(session.get(room_info['cover']))  # 获取直播封面
        except Exception as e:
            # 开了魔法这里会报错
            toast(f'又是这里报错 Exception: {e} line: {e.__traceback__.tb_lineno}', 0, color='error')
        put_row([
            put_image(notice.circle_corner(r.content), format='png'),
            None,
            put_column([
                put_markdown('### {username} {title}'.format_map(room_info)),
                put_markdown(f'<font color="grey">开始</font> __{t2s(room_info["st"], "%Y/%m/%d %H:%M:%S")}__ <font color="grey">结束</font> __{t2s(room_info["sp"], "%Y/%m/%d %H:%M:%S")}__')
            ])
        ], size='10fr 1fr 30fr', scope='query_scope').onclick(partial(reload_live, room_info=room_info, url=f'https://api.drelf.cn/live/{room_info["room"]}/{pos}', pos=pos))

    async def reload_live(room_info, url: str, pos: int):
        clear('query_scope')
        put_markdown('弹幕加载中', scope='query_scope')
        with put_loading('border', 'primary'):
            resp = await rac(session.get(url))
            js = resp.json()
            if js['status'] != 0:
                toast('运行时错误：'+js['status'], 3, color='error')
                return
            danmaku = js['live']['danmaku']
            clear('query_scope')
        await put_live(room_info, pos)
        temp = '%s <a href="https://space.bilibili.com/%d">%s</a> %s\n\n'
        danma_str = ''.join([temp % (t2s(dm["time"]), dm["uid"], dm["username"], dm["msg"]) for dm in danmaku])
        put_markdown(danma_str, scope='query_scope')

    # 打印弹幕列表
    async def put_danmaku(room_info: dict, danmaku: list, flag: bool = False):
        await put_live(room_info, danmaku)  # 先打印直播信息
        if flag:
            danma_str = '\n\n'.join([f'{t2s(dm["time"])} <a href="https://space.bilibili.com/{dm["uid"]}">{dm["username"]}</a> {dm["msg"]}'
                                        for dm in danmaku])
            put_markdown(danma_str, scope='query_scope')
            put_markdown('---', scope='query_scope')

    clear('query_scope')
    session = httpx.AsyncClient()
    try:
        if btn == '😋查发言':
            uid = await eval_js('prompt("输入查询用户uid")')
            if uid and uid.isdigit:
                try:
                    resp = await rac(session.get(f'https://api.drelf.cn/uid/{uid}'))
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
            roomid = await eval_js('prompt("输入查询直播间号")')
            resp = await rac(session.get(f'https://api.drelf.cn/live/{roomid}'))
            js = resp.json()
            if js['status'] == 0:
                n = len(js['lives']) - 1
                for pos, live in enumerate(js['lives']):
                    await put_danmaku(live, danmaku=n-pos)
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


async def about():
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


app.mount('/', FastAPI(routes=webio_routes({'index': cha, 'about': about})))  # 绑定应用到网页根目录, cdn='/html'

if __name__ == '__main__':
    uvicorn.run(app='cha:app', host="0.0.0.0", port=8001)

# port=443, ssl_keyfile='api.nana7mi.link.key', ssl_certfile='api.nana7mi.link_bundle.crt'
