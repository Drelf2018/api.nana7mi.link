from pywebio.output import *
from pywebio.input import textarea
from pywebio.session import run_js, local
from night.liteDB import userDB, configDB
from night.night import night
from json import loads, dumps
from bilibili_api import Credential
from functools import partial

tasks = {}


async def on_click(btn: str, data):
    username, cid, code = btn.split('.')
    try:
        if not tasks.get(username):
            cookies = userDB.query('SESSDATA,BILI_JCT,BUVID3', USERNAME=username)
            credential = Credential(*cookies)
            tasks[username] = {'credential': credential}
        task = tasks[username].get(cid)
        if code == 'run':
            if not task:
                tasks[username][cid] = night(cid, local.loglist, tasks[username]['credential'], data)
        elif code == 'close':
            if task:
                await task.close()
                del tasks[username][cid]
    except Exception as e:
        print(e, e.__traceback__.tb_lineno)


async def set_config(cid, config):
    new_config = await textarea('编辑配置文件', rows=20, code={}, value=config)
    js = loads(new_config)
    new_config = dumps(js, indent=4, ensure_ascii=False)
    configDB.update({'CID': cid}, DATA=new_config)
    run_js('location.reload();')


def get_configs(username, cids):
    configs = configDB.query(cids)
    widgets = []
    for cid, name, owner, data in configs:
        js = loads(data)
        color, bname = userDB.query('COLOR,NICKNAME', USERNAME=owner)
        widgets.append(
            put_collapse(f'配置：{name}', [
                put_tabs([
                    {'title': '基本信息', 'content': [
                        put_markdown(f'`配置所有`：<font color="{color}">{bname}</font>'),
                        put_markdown(f'`配置序号`：{cid}'),
                        put_markdown(f'`直播间号`：{js["roomid"]}'),
                        put_markdown(f'`监听阈值`：{js["limited_density"]}'),
                        put_markdown(f'`输出间隔`：{js["send_rate"]}'),
                        put_markdown('`监听词句`：\n&emsp;'+"\n&emsp;".join(js["listening_words"])),
                        put_markdown('`输出词句`：\n&emsp;'+"\n&emsp;".join(js["goodnight_words"])),
                    ]},
                    {
                        'title': '输出终端',
                        'content': [
                            put_row([
                                put_buttons([
                                    {'label': '▷', 'value': f'{username}.{cid}.run'},
                                    {'label': '■', 'color': 'danger', 'value': f'{username}.{cid}.close'}
                                ], onclick=partial(on_click, data=js)),
                                None,
                                put_scope(f'scrollable_{cid}_hb')
                            ], size='auto 1fr auto'),
                            put_scrollable(put_scope(f'scrollable_{cid}'), height=200, keep_bottom=True)
                        ]
                    },
                    {'title': '源代码', 'content': [put_code(data, 'json')] + [
                        put_button('编辑配置', onclick=partial(set_config, cid=cid, config=data)) if username == owner else put_scope(str(cid))
                    ]},
                ]).style('border:none;')
            ])
        )
    return widgets


if __name__ == '__main__':
    '''
    configDB.insert(CID=1, NAME='曹你', OWNER='Admin', DATA='fuck you')
    configDB.insert(CID=2, NAME='曹我', OWNER='Admin2', DATA='fuck me')
    configDB.insert(CID=3, NAME='曹谁', OWNER='Admin3', DATA='fuck who')
    '''
