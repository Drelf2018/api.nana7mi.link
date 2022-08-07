from PIL import Image, ImageDraw
from io import BytesIO
from pywebio.session import run_asyncio_coroutine as rac
import aiohttp

Headers = {
    'Connection': 'keep-alive',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
}

async def exface(face, pendant):
    session = aiohttp.ClientSession(headers=Headers)
    # 头像
    if isinstance(face, str):
        response = await rac(session.get(face))  # 请求图片
        face = Image.open(BytesIO(await rac(response.read())))  # 读取图片
    w, h = face.size

    a = Image.new('L', face.size, 0)  # 创建一个黑色背景的画布
    ImageDraw.Draw(a).ellipse((0, 0, a.width, a.height), fill=255)  # 画白色圆形
    
    # 装扮
    if pendant:
        image = Image.new('RGBA', (int(1.75*w), int(1.75*h)), (0, 0, 0, 0))
        image.paste(face, (int(0.375*w), int(0.375*h)), mask=a)  # 粘贴至背景
        response = await rac(session.get(pendant))  # 请求图片
        pd = Image.open(BytesIO(await rac(response.read())))  # 读取图片
        pd = pd.resize((int(1.75*w), int(1.75*h)), Image.ANTIALIAS)  # 装扮应当是头像的1.75倍
        try:
            r, g, b, a = pd.split()  # 分离alpha通道
            image.paste(pd, (0, 0), mask=a)  # 粘贴至背景
            await rac(session.close())
            return image
        except Exception:
            pendant = None
    # 粉圈
    if not pendant:
        image = Image.new('RGBA', (int(1.16*w), int(1.16*h)), (0, 0, 0, 0))
        image.paste(face, (int(0.08*w), int(0.08*h)), mask=a)  # 粘贴至背景
        ps = Image.new("RGB", (int(1.16*w), int(1.16*h)), (242, 93, 142))
        a = Image.new('L', ps.size, 0)  # 创建一个黑色背景的画布
        ImageDraw.Draw(a).ellipse((0, 0, a.width, a.height), fill=255)  # 画白色外圆
        ImageDraw.Draw(a).ellipse((int(0.06*w), int(0.06*h), int(1.1*w), int(1.1*h)), fill=0)  # 画黑色内圆
        image.paste(ps, (0, 0), mask=a)  # 粘贴至背景
        w, h = image.size
        bg = Image.new('RGBA', (int(1.25*w), int(1.25*h)), (0, 0, 0, 0))
        bg.paste(image, (int((1.25-1)/2*w), int((1.25-1)/2*h)))
        await rac(session.close())
        return bg


if __name__ == '__main__':
    face = Image.open('./images/0.png')
    image = exface(face, None)
