import asyncio
import json
import time
from logging import DEBUG, INFO, Logger

import requests
from aiowebsocket.converses import AioWebSocket
from apscheduler.schedulers.background import BackgroundScheduler

from database import conn, danmuDB, liveDB
from WebHandler import get_default_handler

BASEURL = 'http://localhost:5764'
ROOM_STATUS = {}  # 记录开播时间
# 重启程序后从数据库中读取没有结束时间(SP)的直播间号及开播时间
for room, st in conn.execute('SELECT ROOM,ST FROM LIVE WHERE SP IS NULL').fetchall():
    ROOM_STATUS[room] = st


class Adapter:
    '连接网页、数据库、biligo-ws-live 的适配器'
    def __init__(self, logger: Logger, url: str = BASEURL+'/ws'):
        self.url = url  # biligo-ws-live 运行地址
        self.logger = logger  # 网页端输出 Logger
        self.converse = None  # 异步连接
        self.danmu = []  # 暂存的弹幕
        self.sched = BackgroundScheduler()  # 用来保存暂存弹幕到数据库的计时器

    async def connect(self):
        while not self.converse:  # 多次尝试连接 biligo-ws-live
            try:
                async with AioWebSocket(self.url) as aws:
                    self.converse = aws.manipulator
            except Exception:
                self.logger.info('`Adapter` 重连中')
                await asyncio.sleep(3)
        self.logger.info('`Adapter` 连接成功')
        return self.converse.receive  # 接受消息的函数

    async def run(self, listening_rooms: list):
        recv = await self.connect()
        logger = self.logger  # 不知道从哪学的减少 self. 操作耗时的方法 好像说 self. 就是查字典也要时间

        # 定时保存弹幕
        @self.sched.scheduled_job('interval', id='record_danmu', seconds=10, max_instances=3)
        def record():
            count = len(self.danmu)
            if count > 0:
                logger.info(f'储存 `{count}` 条弹幕记录')
                # 防止保存数据 求出现有数量后 若有新增弹幕 将新增弹幕重新存回 self.danmu
                record_danmu, self.danmu = self.danmu[:count], self.danmu[count:]
                danmuDB.insert(record_danmu)

        self.sched.start()

        # 将监听房间号告知 biligo-ws-live
        requests.post(BASEURL+'/subscribe', data={'subscribes': listening_rooms})

        while True:  # 死循环接受消息
            try:
                mes = await recv()
            except Exception as e:
                logger.error(e)
                break
            js = json.loads(mes)
            roomid = js.get('live_info', {}).get('room_id')
            if roomid in listening_rooms:
                if js['command'] == 'LIVE':  # 开播时记录时间戳在 ROOM_STATUS 里并插入数据库
                    start_time = round(time.time())
                    if not ROOM_STATUS.get(roomid):
                        ROOM_STATUS[roomid] = start_time
                        info = js['live_info']
                        name, uid, title, cover = info['name'], info['uid'], info['title'], info['cover']
                        liveDB.insert(ROOM=roomid, USERNAME=name, UID=uid, TITLE=title, COVER=cover, ST=start_time)
                        logger.info(f'`{name}` 正在 `{roomid}` 直播\n标题：{title}\n封面：{cover}')

                elif js['command'] == 'DANMU_MSG':  # 接受到弹幕
                    info = js['content']['info']
                    self.danmu.append((roomid, info[9]['ts'], info[2][1], info[2][0], info[1], 'DANMU_MSG', 0, ROOM_STATUS.get(roomid, 0)))
                    logger.info(f'在直播间 `{roomid}` 收到 `{info[2][1]}` 的弹幕：{info[1]}')
                    # 向暂存弹幕库添加元组 (房间号, 时间戳, 用户名, 用户uid, 信息内容, 信息类型, 信息价值 当前直播间的开播时间)
                    # 当前直播间的开播时间 为 None 或 0 表示未开播

                elif js['command'] == 'SEND_GIFT':  # 接受到礼物
                    data = js['content']['data']
                    msg = '{action} {giftName}'.format_map(data) + f'<font color="red">￥{data["price"]/1000}</font>'
                    self.danmu.append((roomid, data['timestamp'], data['uname'], data['uid'], msg, 'SEND_GIFT', data["price"]/1000, ROOM_STATUS.get(roomid, 0)))
                    logger.info(f'在直播间 `{roomid}` 收到 `{data["uname"]}` 的礼物：{data["giftName"]}')

                elif js['command'] == 'GUARD_BUY':  # 接受到大航海
                    data = js['content']['data']
                    msg = f'赠送 {data["gift_name"]}<font color="red">￥{data["price"]//1000}</font>'
                    self.danmu.append((roomid, data['start_time'], data['username'], data['uid'], msg, 'GUARD_BUY', data["price"]//1000, ROOM_STATUS.get(roomid, 0)))
                    logger.info(f'在直播间 `{roomid}` 收到 `{data["username"]}` 的{data["gift_name"]}')

                elif js['command'] in ['SUPER_CHAT_MESSAGE', 'SUPER_CHAT_MESSAGE_JPN']:  # 接受到醒目留言
                    data = js['content']['data']
                    msg = '{message}<font color="red">￥{price}</font>'.format_map(data)
                    self.danmu.append((roomid, data['start_time'], data['user_info']['uname'], data['uid'], msg, 'SUPER_CHAT_MESSAGE', data['price'], ROOM_STATUS.get(roomid, 0)))
                    logger.info(f'在直播间 `{roomid}` 收到 `{data["user_info"]["uname"]}` 的 ￥{data["price"]} SuperChat: {data["message"]}')

                elif js['command'] == 'PREPARING' and ROOM_STATUS.get(roomid):  # 下播 更新数据库中下播时间戳 并将全局数组清零（真能清零吗（你在暗示什么））
                    liveDB.update(roomid, ROOM_STATUS[roomid], round(time.time()))
                    logger.info(f'直播间 `{roomid}` 下播了')
                    del ROOM_STATUS[roomid]

                else:
                    logger.debug(json.dumps(js, indent=4, ensure_ascii=False))

    async def send(self, cmd):  # 不知道有啥用的发送消息 但是既然有ws连接还是写个发送好 万一用到了呢
        if isinstance(cmd, str):
            await self.converse.send(cmd)
        else:
            try:
                js = json.dumps(cmd, ensure_ascii=False)
                await self.converse.send(js)
            except Exception as e:
                self.logger.error('发送失败 '+str(e))


if __name__ == '__main__':
    # 其实适配器就是个最小实例 不用运行网页也能做到保存数据了
    logger = Logger('MAIN', INFO)
    loglist, handler = get_default_handler()
    logger.addHandler(handler)
    asyncio.run(Adapter(logger).run([21452505]))
