import asyncio
import requests
import json
import time
from logging import DEBUG, Logger

from aiowebsocket.converses import AioWebSocket
from apscheduler.schedulers.background import BackgroundScheduler

from database import danmuDB, liveDB, conn
from WebHandler import get_default_handler

BASEURL = 'http://localhost:5764'
ROOM_STATUS = {}
for room, st in conn.execute('SELECT ROOM,ST FROM LIVE WHERE SP IS NULL').fetchall():
    ROOM_STATUS[room] = st


class Adapter:
    def __init__(self, logger: Logger = Logger('MAIN', DEBUG), url: str = BASEURL+'/ws'):
        self.url = url
        self.logger = logger
        self.converse = None
        self.danmu = []
        self.sched = BackgroundScheduler()

    async def connect(self):
        while not self.converse:
            try:
                async with AioWebSocket(self.url) as aws:
                    self.converse = aws.manipulator
            except Exception:
                self.logger.info('`Adapter` 重连中')
                await asyncio.sleep(3)
        self.logger.info('`Adapter` 连接成功')
        return self.converse.receive

    async def run(self, listening_rooms):
        recv = await self.connect()
        logger = self.logger

        # 定时保存弹幕
        @self.sched.scheduled_job('interval', id='record_danmu', seconds=10, max_instances=3)
        def record():
            count = len(self.danmu)
            if count > 0:
                logger.info(f'储存 `{count}` 条弹幕记录')
                # 防止保存数据 求出现有数量后 有新增弹幕 将新增弹幕重新存回 self.danmu
                record_danmu, self.danmu = self.danmu[:count], self.danmu[count:]
                danmuDB.insert(record_danmu)

        self.sched.start()

        requests.post(BASEURL+'/subscribe', data={'subscribes': listening_rooms})

        while True:
            try:
                mes = await recv()
            except Exception as e:
                logger.error(e)
                break
            js = json.loads(mes)
            if js['command'] == 'LIVE':
                start_time = round(time.time())
                info = js['live_info']
                roomid = info['room_id']
                if not ROOM_STATUS.get(roomid):
                    ROOM_STATUS[roomid] = start_time
                    name, uid, title, cover = info['name'], info['uid'], info['title'], info['cover']
                    liveDB.insert(ROOM=roomid, USERNAME=name, UID=uid, TITLE=title, COVER=cover, ST=start_time)
                    logger.info(f'`{name}` 正在 `{roomid}` 直播\n标题：{title}\n封面：{cover}')
            elif js['command'] == 'DANMU_MSG':
                roomid = js['live_info']['room_id']
                if roomid in listening_rooms:
                    info = js['content']['info']
                    self.danmu.append((roomid, info[9]['ts'], info[2][1], info[2][0], info[1], ROOM_STATUS.get(roomid, 0)))
                    logger.info(f'在直播间 `{roomid}` 收到 `{info[2][1]}` 的弹幕：{info[1]}')
            elif js['command'] == 'PREPARING':
                roomid = js['live_info']['room_id']
                st = ROOM_STATUS.get(roomid)
                if st:
                    del ROOM_STATUS[roomid]
                    liveDB.update(roomid, st, round(time.time()))
                    logger.info(f'直播间 `{roomid}` 下播了')
            else:
                logger.debug(json.dumps(js, indent=4, ensure_ascii=False))

    async def send(self, cmd):
        if isinstance(cmd, str):
            await self.converse.send(cmd)
        else:
            try:
                js = json.dumps(cmd, ensure_ascii=False)
                await self.converse.send(js)
            except Exception as e:
                self.logger.error('发送失败 '+str(e))


if __name__ == '__main__':
    logger = Logger('MAIN', DEBUG)
    loglist, handler = get_default_handler()
    logger.addHandler(handler)
    adapter = Adapter(logger)
    asyncio.run(adapter.run([21452505]))
