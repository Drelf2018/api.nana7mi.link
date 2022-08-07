import aiohttp
import qrcode
import asyncio
from night import account
from pywebio.output import *
from pywebio.session import run_asyncio_coroutine as rac, go_app
from bilibili_api.live import Danmaku, LiveRoom
from bilibili_api import Credential, user
from bilibili_api.exceptions import CredentialNoSessdataException
from logging import DEBUG, Formatter, Logger, StreamHandler


logger = Logger('BILI', DEBUG)
handler = StreamHandler()
handler.setFormatter(Formatter("`%(asctime)s` `%(levelname)s` `Bili`: %(message)s", '%Y-%m-%d %H:%M:%S'))
logger.addHandler(handler)
Headers = {
    'Connection': 'keep-alive',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
}

class BILI:
    url = None
    uid = 0
    running = False
    cookies = {}
    credential = None

    def __bool__(self):
        return all([self.uid, self.cookies])

    def __del__(self):
        if self.session:
            asyncio.run_coroutine_threadsafe(self.session.close(), asyncio.new_event_loop())

    def __init__(self, uid, cookies):
        self.uid = uid
        self.cookies = {
            'sessdata': cookies[0],
            'bili_jct': cookies[1],
            'buvid3': cookies[2]
        }
        self.credential = Credential(**self.cookies)

    async def login(self):
        '通过扫描二维码模拟登录B站并获取cookies'
        
        if self.running:
            logger.debug('为什么不return')
            return
        else:
            self.running = True

        session = aiohttp.ClientSession(headers=Headers)
        self.session = session

        # 获取 oauthKey 以生成二维码
        r = await rac(session.get('https://passport.bilibili.com/qrcode/getLoginUrl'))
        js = (await rac(r.json()))['data']

        # 验证时要发送的数据
        check_data = {'oauthKey': js['oauthKey']}

        def on_click(btn):
            self.running = False
            if btn == '退出':
                account.clear()
                go_app('index', False)
            close_popup()

        # 生成图片展示并保存
        qrimg = qrcode.make(js['url'])
        popup('账号绑定', [
            put_html('<h3>请打开哔哩哔哩APP扫码登录</h3>'),
            put_image(qrimg.get_image(), format='png', width='150px'),
            put_markdown('---'),
            put_buttons(['关闭', {'label': '退出登录', 'color': 'danger', 'value': '退出'}], onclick=on_click)
        ], closable=False)

        while self.running:
            # 间隔 3 秒轮询扫码状态
            await asyncio.sleep(3)
            try:
                r = await rac(session.post('https://passport.bilibili.com/qrcode/getLoginInfo', data=check_data))
            except Exception:
                self.running = False
                break
            js = await rac(r.json())
            if js['status']:
                await rac(session.get(js['data']['url']))  # 访问此网站更新cookies
                cookies = session.cookie_jar.filter_cookies("https://message.bilibili.com")
                break

        close_popup()

        if self.running:
            def get_clean_cookie(cookie):
                return str(cookies[cookie]).replace(f'Set-Cookie: {cookie}=', '')
            self.uid = get_clean_cookie('DedeUserID')
            for cookie in ['SESSDATA', 'bili_jct', 'buvid3']:
                self.cookies[cookie.lower()] = get_clean_cookie(cookie)
            self.credential = Credential(**self.cookies)
            self.running = False

    async def check(self):
        try:
            return await LiveRoom(14703541, self.credential).send_danmaku(Danmaku('check()'))
        except Exception as e:
            if isinstance(e, CredentialNoSessdataException):
                logger.debug('CredentialNoSessdataException')
                self.uid = None
                return -101
            else:
                logger.debug(f'{e.code} {e.msg}')
                if e.code != 10031:
                    self.uid = None
                return e.code
            

    async def get_info(self):
        return await user.get_self_info(self.credential)
