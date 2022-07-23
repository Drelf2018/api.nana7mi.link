import time
import psycopg2
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


class DataBase:
    def __init__(self, table: str):
        self.table = table if table else 'danmaku'

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

    def query(self, cmd='*', all=False, **kwargs):
        sql = f'SELECT {cmd} FROM {self.table}'
        if kwargs:
            sql += ' WHERE ' + ' AND '.join([f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}" for k, v in kwargs.items()])
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
    def __init__(self):
        super().__init__('danmaku')

    def insert(self, data):
        sql = f'INSERT INTO {self.table} (roomid,time,username,uid,msg,cmd,price,st) VALUES %s;'
        ex.execute_values(cursor, sql, data)
        self.save()

    def query_room(self, roomid: int, start_time: int, stop_time: int = 0):
        flag = False
        if not stop_time:
            stop_time = time.time()
            flag = True
        sql = f'SELECT time,username,uid,msg,cmd,price FROM danmaku WHERE roomid = {roomid} AND time >= {start_time} AND time <= {stop_time}'
        cursor = conn.cursor()
        cursor.execute(sql)
        dms = cursor.fetchall()
        if flag:
            dms = dms[::-1]
        for dm in dms:
            yield {'time': dm[0], 'username': dm[1], 'uid': dm[2], 'msg': dm[3], 'type': dm[4], 'price': dm[5]}


class LiveDB(DataBase):
    def __init__(self):
        super().__init__('live')
    
    def update(self, room_id: int, start_time: int, stop_time):
        super().update({'ROOM': room_id, 'ST': start_time}, SP=stop_time)

    def d2d(self, data):
        return {
            'room': data[0],
            'username': data[1],
            'uid': data[2],
            'title': data[3],
            'cover': data[4],
            'st': data[5],
            'sp': data[6]
        }

    def query(self, room_id: int = None, start_time: int = 0, all=False):
        params = {'roomid': room_id}
        if start_time:
            params.update({'st': start_time})
        data = super().query(all=all, **params)
        if not all:
            if not data:
                return
            return self.d2d(data)
        else:
            if not data[0]:
                return
            return [self.d2d(d) for d in data]
        

danmuDB = DanmuDB()
liveDB = LiveDB()
