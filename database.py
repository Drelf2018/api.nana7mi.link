import time
import sqlite3


conn = sqlite3.connect(f'./Core.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS DANMU(
    ROOM INT,
    TIME INT,
    USERNAME TEXT,
    UID INT,
    MSG TEXT,
    MSG_TYPE TEXT,
    MSG_PRICE INT,
    ST INT
);''')
cursor.execute('''CREATE TABLE IF NOT EXISTS LIVE(
    ROOM INT,
    USERNAME TEXT,
    UID INT,
    TITLE TEXT,
    COVER TEXT,
    ST INT,
    SP INT
);''')


class DataBase:
    def __init__(self, table: str):
        self.table = table if table else 'DANMU'

    def insert(self, **kwargs):
        sql = f'INSERT INTO {self.table} ({",".join(kwargs.keys())}) VALUES ({",".join(list("?"*len(kwargs.keys())))});'
        conn.execute(sql, tuple(kwargs.values()))
        self.save()

    def update(self, location: dict, **kwargs):
        sql = f'UPDATE {self.table} SET ' + ', '.join([f"{k}={v}" for k, v in kwargs.items()])
        sql += ' WHERE ' + ' AND '.join([f"{k}={v}" for k, v in location.items()])
        conn.execute(sql)
        self.save()

    def query(self, cmd='*', all=False, **kwargs):
        sql = f'SELECT {cmd} FROM {self.table}'
        if kwargs:
            sql += ' WHERE ' + ' AND '.join([f"{k}='{v}'" for k, v in kwargs.items()])
        if all:
            resp = conn.execute(sql).fetchall()
        else:
            resp = conn.execute(sql).fetchone()
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
        super().__init__('DANMU')
    
    def insert(self, data):
        sql = f'INSERT INTO {self.table} (ROOM,TIME,USERNAME,UID,MSG,MSG_TYPE,MSG_PRICE,ST) VALUES (?,?,?,?,?,?,?,?);'
        conn.executemany(sql, data)
        self.save()
    
    def query_room(self, roomid: int, start_time: int, stop_time: int = 0):
        flag = False
        if not stop_time:
            stop_time = time.time()
            flag = True
        sql = f'SELECT TIME,USERNAME,UID,MSG,MSG_TYPE,MSG_PRICE FROM DANMU WHERE ROOM = {roomid} AND TIME >= {start_time} AND TIME <= {stop_time}'
        dms = conn.execute(sql).fetchall()
        if flag:
            dms = dms[::-1]
        return [{'time': dm[0], 'username': dm[1], 'uid': dm[2], 'msg': dm[3], 'type': dm[4], 'price': dm[5]} for dm in dms]


class LiveDB(DataBase):
    def __init__(self):
        super().__init__('LIVE')
    
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
        params = {'ROOM': room_id}
        if start_time:
            params.update({'ST': start_time})
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
