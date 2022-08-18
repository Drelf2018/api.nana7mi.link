import datetime
import logging
import time

import httpx
import psycopg2
from apscheduler.schedulers.background import BackgroundScheduler
from psycopg2 import extras as ex


conn = psycopg2.connect(...)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS public.danmaku
(
    roomid bigint,
    time bigint,
    username text COLLATE pg_catalog."default",
    uid bigint,
    msg text COLLATE pg_catalog."default",
    cmd text COLLATE pg_catalog."default",
    price double precision,
    st bigint
)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS public.live
(
    roomid bigint,
    username text COLLATE pg_catalog."default",
    uid bigint,
    title text COLLATE pg_catalog."default",
    cover text COLLATE pg_catalog."default",
    st bigint,
    sp bigint
)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS public.data
(
    username text COLLATE pg_catalog."default",
    uid bigint,
    roomid bigint,
    time bigint,
    follower bigint,
    guardNum bigint
)''')

class DataBase:
    def insert(self, **kwargs):
        keys = ", ".join(kwargs.keys())
        vals = ", ".join([f'%({key})s' for key in list(kwargs.keys())])
        sql = f'INSERT INTO {self.table} ({keys}) VALUES ({vals});'
        cursor = conn.cursor()
        cursor.execute(sql, kwargs)
        self.save()

    def update(self, location: dict, **kwargs):
        sql = f'UPDATE {self.table} SET ' + ', '.join([f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}" for k, v in kwargs.items()])
        sql += ' WHERE ' + ' AND '.join([f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}" for k, v in location.items()])
        cursor = conn.cursor()
        cursor.execute(sql)
        self.save()

    def query(self, cmd='*', all=False, desc=False, **kwargs):
        sql = f'SELECT {cmd} FROM {self.table}'
        if kwargs:
            sql += ' WHERE ' + ' AND '.join([f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}" for k, v in kwargs.items()])
        sql += ' order by '
        if self.table == 'danmaku':
            sql += 'time'
        else:
            sql += 'st'
        if desc:
            sql += ' desc'
        cursor = conn.cursor()
        if all:
            cursor.execute(sql)
            resp = cursor.fetchall()
        else:
            cursor.execute(sql)
            resp = cursor.fetchone()
        if not resp:
            if cmd.find(',') == -1:
                if all:
                    return [None]
                else:
                    return None
            if all:
                return [(None,) * len(cmd.split(','))]
            else:
                return (None,) * len(cmd.split(','))
        else:
            if not all and len(resp) == 1:
                return resp[0]
            return resp

    def save(self):
        conn.commit()

    def __del__(self):
        conn.close()


class DanmuDB(DataBase):
    table = 'danmaku'

    def insert(self, data):
        sql = 'INSERT INTO danmaku (roomid,time,username,uid,msg,cmd,price,st) VALUES %s;'
        ex.execute_values(cursor, sql, data)
        self.save()

    def query_room(self, roomid: int, start_time: int, stop_time: int = 0):
        flag = False
        if not stop_time:
            stop_time = time.time()
            flag = True
        sql = f'''SELECT time,username,uid,msg,cmd,price FROM danmaku 
            WHERE roomid = {roomid} AND time >= {start_time} AND time <= {stop_time} 
            order by time''' + (' desc' if flag else '')
        cursor = conn.cursor()
        cursor.execute(sql)
        dms = cursor.fetchall()
        for dm in dms:
            yield {'time': dm[0], 'username': dm[1], 'uid': dm[2], 'msg': dm[3], 'type': dm[4], 'price': dm[5]}


class LiveDB(DataBase):
    table = 'live'
    
    def update(self, room_id: int, start_time: int, stop_time):
        super().update({'roomid': room_id, 'st': start_time}, SP=stop_time)

    def query(self, room_id: int = None, start_time: int = 0, all=False):
        parse = lambda data: {
            'room':     data[0],
            'username': data[1],
            'uid':      data[2],
            'title':    data[3],
            'cover':    data[4],
            'st':       data[5],
            'sp':       data[6]
        }
        params = {'roomid': room_id}
        if start_time:
            params.update({'st': start_time})
        data = super().query(all=all, **params)
        if not all:
            if not data:
                return
            return parse(data)
        else:
            if not data[0]:
                return
            return [parse(d) for d in data]

    def rooms(self):
        table_name = f'tb{int(time.time())}'
        sql = f'''CREATE TEMP TABLE {table_name} as SELECT roomid, MAX(st) FROM live GROUP BY roomid;
SELECT
    roomid,cover,username,title,st,sp,uid
FROM
    live big
WHERE
    big.roomid in (
        SELECT
            {table_name}.roomid
        FROM
            {table_name}
        WHERE
            big.st = {table_name}.max
    )
ORDER BY sp DESC;
'''
        cursor = conn.cursor()
        try:
            cursor.execute(sql)
            rooms = cursor.fetchall()
            conn.cursor().execute(f'DROP TABLE {table_name};')
        except Exception as e:
            return str(e)
        parse = lambda room: {
            'room':     room[0],
            'cover':    room[1],
            'username': room[2],
            'title':    room[3],
            'st':       room[4],
            'sp':       room[5],
            'uid':      room[6]
        }
        return [parse(room) for room in rooms] if rooms else None

class DataDB(DataBase):
    table = 'data'

danmuDB = DanmuDB()
liveDB = LiveDB()
dataDB = DataDB()
sched = BackgroundScheduler(timezone="Asia/Shanghai")
logger = logging.getLogger('sched')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", '%H:%M:%S'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

@sched.scheduled_job('interval', hours=1, next_run_time=datetime.datetime.now())
def heartbeat():
    BASEURL = 'https://api.live.bilibili.com/xlive/web-room/v1/index/getInfoByRoom?room_id={room}'
    for room in liveDB.rooms():
        resp = httpx.get(BASEURL.format_map(room))
        js = resp.json()
        data = js['data']
        if data:
            dataDB.insert(
                username=room['username'],
                uid=room['uid'],
                roomid=room['room'],
                time=int(time.time()),
                follower=data['anchor_info']['relation_info']['attention'],
                guardNum=data['guard_info']['count']
            )
            logger.debug('更新'+room['username']+'数据成功')
        else:
            logger.error('更新'+room['username']+'数据失败')
        time.sleep(3)
    logger.info('全部更新完毕')

sched.start()
