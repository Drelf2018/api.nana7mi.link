from pywebio.output import *
from PIL import Image
import os


PICS = {}
for root, folders, files in os.walk('./notice_pic'):
    for file in files:
        PICS[file] = Image.open(os.path.join(root,file))


def notice():
    return [
        put_row([
            put_image(PICS['notice.6.10.png']),
            None,
            put_markdown('''## 📢 api.nana7mi.link 06月10日11:20临时不停机更新公告

            感谢您对《api.nana7mi.link》的关注与支持。我们计划将于2022年06月10日11:20进行服务器不停机更新。本次更新不会影响用户正常查询进程，更新结束后，用户只需选择合适时间重启网站即可完成更新。

            更新时间：
            2022年06月10日11:20

            更新内容：
            ◆新增「公告Notice」页面配图''')
        ], size='18fr 1fr 24fr'),
        put_markdown('---'),
        put_row([
            put_image(PICS['notice.6.9.png']),
            None,
            put_markdown('''## 📢 api.nana7mi.link 06月09日23:45临时不停机更新公告

            感谢您对《api.nana7mi.link》的关注与支持。我们计划将于2022年06月09日23:45进行服务器不停机更新。本次更新不会影响用户正常查询进程，更新结束后，用户只需选择合适时间重启网站即可完成更新。

            更新时间：
            2022年06月09日23:45

            更新内容：
            ◆修复使用【api.nana7mi.link/live/{roomid}/last】进行直播记录查询在部分情况下报错的问题
            ◆新增「公告Notice」页面''')
        ], size='18fr 1fr 24fr'),
        put_markdown('---')
    ]