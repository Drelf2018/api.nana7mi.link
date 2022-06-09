from pywebio.output import *


def notice():
    return [
        put_markdown('''## 📢 api.nana7mi.link 06月09日23:45临时不停机更新公告

    感谢您对《api.nana7mi.link》的关注与支持。我们计划将于2022年06月09日23:45进行服务器不停机更新。本次更新不会影响用户正常查询进程，更新结束后，用户只需选择合适时间重启网站即可完成更新。

    更新时间：
    2022年06月09日23:45

    更新内容：
    ◆修复使用【api.nana7mi.link/live/{roomid}/last】进行直播记录查询在部分情况下报错的问题
    ◆新增「公告Notice」页面
    ---''')
    ]