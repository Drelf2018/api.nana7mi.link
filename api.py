import time
from typing import Optional

import uvicorn
from database import danmuDB, liveDB
from fastapi import FastAPI

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


if __name__ == '__main__':
    uvicorn.run(app='api:app', host="0.0.0.0", port=5762)
