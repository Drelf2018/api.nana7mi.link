import time
import httpx
from typing import Optional

import uvicorn
from database import danmuDB, liveDB
from fastapi import FastAPI
from starlette.responses import HTMLResponse

app = FastAPI()

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


# 返回所有监控中房间的最近一次直播数据(无弹幕)
@app.get("/rooms")
def cha_lives():
    return {'status': 0, 'rooms': liveDB.rooms()}


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
        if not live['sp']:  # 直播中 或者没记录到下播弹幕
            # 如果没记录到下播 去 matsuri.icu 查一下有没有下播
            resp = httpx.get('http://43.138.71.81:5763/matsuri/{uid}/{st}'.format_map(live), timeout=20.0)
            js = resp.json()
            if js['status'] == 1:
                if js['clip']['end_time']:
                    live['sp'] = js['clip']['end_time'] // 1000
                    liveDB.update(roomid, live['st'], live['sp'])
                else:
                    live['sp'] = round(time.time())
            else:
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

@app.get('/')
async def hello():
    return HTMLResponse('''<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    <link href="https://example-static.oss-cn-beijing.aliyuncs.com/web-framework/style.css" rel="stylesheet" type="text/css"/>
</head>
<body>
<div class="website">
    <div class="ri-t">
        <h1>你好李鑫</h1>
        <h2>这是一个 FastAPI 项目：api.nana7mi.link</h2>
        <span>通过 Nginx 进行部署</span>
        <br/>
        <p>了解更多，您可以：<br/>
            • 访问代码仓库 github.com/Drelf2018/api.nana7mi.link<br/>
            • 阅读 FastAPI 自动生成文档：/docs<br/>
        </p>
    </div>
</div>
</body>
</html>
''')

if __name__ == '__main__':
    uvicorn.run(app='api:app', host="0.0.0.0", port=5762)
