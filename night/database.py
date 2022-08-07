import sqlite3


conn = sqlite3.connect(f'.\\night\\Core.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS USER(
    USERNAME TEXT PRIMARY KEY,
    PASSWORD TEXT,
    UID TEXT,
    NICKNAME TEXT,
    FACE TEXT,
    PENDANT TEXT,
    COLOR TEXT,
    SESSDATA TEXT,
    BILI_JCT TEXT,
    BUVID3 TEXT,
    CONFIG TEXT,
    IP TEXT
);''')
cursor.execute('''CREATE TABLE IF NOT EXISTS CONFIG(
    CID INT PRIMARY KEY,
    NAME TEXT,
    OWNER TEXT,
    DATA TEXT
);''')


class DataBase:
    def __init__(self, table: str):
        self.table = table if table else 'USER'

    def insert(self, **kwargs):
        sql = f'INSERT INTO {self.table} ({",".join(kwargs.keys())}) VALUES ({",".join(list("?"*len(kwargs.keys())))});'
        cursor.execute(sql, tuple(kwargs.values()))
        self.save()

    def update(self, location: dict, **kwargs):
        sql = f'UPDATE {self.table} SET ' + ', '.join([f"{k}='{v}'" for k, v in kwargs.items()])
        sql += ' WHERE ' + ' AND '.join([f"{k}='{v}'" for k, v in location.items()])
        cursor.execute(sql)
        self.save()

    def query(self, cmd='*', all=False, **kwargs):
        sql = f'SELECT {cmd} FROM {self.table}'
        if kwargs:
            sql += ' WHERE ' + ' AND '.join([f"{k}='{v}'" for k, v in kwargs.items()])
        if all:
            resp = cursor.execute(sql).fetchall()
        else:
            resp = cursor.execute(sql).fetchone()
        if not resp:
            if cmd.find(',') == -1:
                return None
            return (None,) * len(cmd.split(','))
        else:
            if not all and len(resp) == 1:
                return resp[0]
            return resp

    def save(self):
        conn.commit()

    def __del__(self):
        conn.close()


class UserDB(DataBase):
    def __init__(self):
        super().__init__('USER')

    def update(self, username: str, **kwargs):
        return super().update({'USERNAME': username}, **kwargs)

class ConfigDB(DataBase):
    def __init__(self):
        super().__init__('CONFIG')
    
    def query(self, cids: str):
        if cids:
            return super().query('*', all=True, CID=cids.replace(',', "' OR CID='"))
        else:
            return []

    def get_last_cid(self):
        return max(super().query('CID', all=True))[0]


userDB = UserDB()
configDB = ConfigDB()

if __name__ == '__main__':
    pass
