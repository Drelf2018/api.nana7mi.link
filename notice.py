from pywebio.output import *
from PIL import Image
import os


PICS = {}
for root, folders, files in os.walk('./notice_pic'):
    for file in files:
        PICS[file] = Image.open(os.path.join(root, file))


def notice():
    return [
        put_row([
            put_image(PICS['notice.8.9.png']).style("border-radius:10px"),
            None,
            put_markdown('''## 📢 08月09日00:20临时不停机更新公告

            感谢您对《api.nana7mi.link》的关注与支持。我们计划将于2022年08月09日00:20进行服务器不停机更新。本次更新不会影响用户正常查询进程，更新结束后，用户只需选择合适时间重启网站即可完成更新。

            更新时间：
            2022年08月09日00:20

            更新说明：
            本次更新为版本更新，前期 Gramma 测试时的数据已被移除。

            更新内容：
            ◆ 移除了Database - Adapter - Biligo - Web 沟通连接模式。
            ◆ 适配器与数据库分离，Biligo 自动保存弹幕数据至数据库。
            ◆ 前后端分离，前端网页通过访问本地 api 接口获取数据。
            ◆ 优化主页，并新增监控中直播间状态展示。
            ◆ 优化查询结构，速度大大提升。
            ◆ 新增 http 自动跳转 https 。
            ◆ 前后端分离了但也没分离，因为我懒得每次开三个窗口。所以我直接用多线程同时启动 api 服务、跳转服务和网页服务。''')
        ], size='18fr 1fr 24fr'),
        put_markdown('---'),
        put_row([
            put_image(PICS['notice.6.13.png']).style("border-radius:10px"),
            None,
            put_markdown('''## 📢 06月13日01:10临时不停机更新公告

            感谢您对《api.nana7mi.link》的关注与支持。我们计划将于2022年06月13日01:10进行服务器不停机更新。本次更新不会影响用户正常查询进程，更新结束后，用户只需选择合适时间重启网站即可完成更新。

            更新时间：
            2022年06月13日01:10

            更新说明：
            本次更新为版本更新，前期Beta测试时的数据已被移除。

            更新内容：
            ◆ 为网站添加了SSL证书，现可用 <a href="https://api.nana7mi.link">https://api.nana7mi.link</a> 访问
            ◆ 为网页头新增了随机语录
            ◆ 新增弹幕记录时对礼物、SuperChat、大航海的记录
            ◆ 修复了一个「查询」时导致记录不全的错误
            ◆ 修复了一个打字把font打成fnot导致数据库烂掉的错误
            ◆ 新建了一个数据库并对外宣布版本大更新''')
        ], size='18fr 1fr 24fr'),
        put_markdown('---'),
        put_row([
            put_image(PICS['notice.6.11.png']).style("border-radius:10px"),
            None,
            put_markdown('''## 📢 06月11日15:40临时不停机更新公告

            感谢您对《api.nana7mi.link》的关注与支持。我们计划将于2022年06月11日15:40进行服务器不停机更新。本次更新不会影响用户正常查询进程，更新结束后，用户只需选择合适时间重启网站即可完成更新。

            更新时间：
            2022年06月11日15:40

            更新内容：
            ◆ 修改「查询」页面配图
            ◆ 新增「查询」页面查直播记录按钮
            ◆ 修复了一个「查询」时导致记录乱序的错误''')
        ], size='18fr 1fr 24fr'),
        put_markdown('---'),
        put_row([
            put_image(PICS['notice.6.10.png']).style("border-radius:10px"),
            None,
            put_markdown('''## 📢 06月10日11:20临时不停机更新公告

            感谢您对《api.nana7mi.link》的关注与支持。我们计划将于2022年06月10日11:20进行服务器不停机更新。本次更新不会影响用户正常查询进程，更新结束后，用户只需选择合适时间重启网站即可完成更新。

            更新时间：
            2022年06月10日11:20

            更新内容：
            ◆ 新增「公告Notice」页面配图''')
        ], size='18fr 1fr 24fr'),
        put_markdown('---'),
        put_row([
            put_image(PICS['notice.6.9.png']).style("border-radius:10px"),
            None,
            put_markdown('''## 📢 06月09日23:45临时不停机更新公告

            感谢您对《api.nana7mi.link》的关注与支持。我们计划将于2022年06月09日23:45进行服务器不停机更新。本次更新不会影响用户正常查询进程，更新结束后，用户只需选择合适时间重启网站即可完成更新。

            更新时间：
            2022年06月09日23:45

            更新内容：
            ◆ 修复使用【api.nana7mi.link/live/{roomid}/last】进行直播记录查询在部分情况下报错的问题
            ◆ 新增「公告Notice」页面''')
        ], size='18fr 1fr 24fr')
    ]