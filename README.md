<div align="center">

<img src="https://user-images.githubusercontent.com/41439182/188192683-676693e3-b182-4c53-b618-d9178880a5e5.png" width="225px" />

# api.nana7mi.link

_✨ 基于 [pywebio](https://github.com/pywebio/PyWebIO) 以及 [biligo-live-ws-PostgreSQL](https://github.com/Drelf2018/biligo-live-ws-PostgreSQL) 的直播数据记录前后端 ✨_ 

</div>

## 场报

如果你是看过包含 `数据来源：api.nana7mi.link` 的图片找到这来的，欢迎。不过你要找的可能不在这里。

[_live2pic.py](https://github.com/Drelf2018/Nana7miBot/blob/development/plugins/_live2pic.py) 这个或许是你想要的，利用 `PIL` 将直播数据写入图片。

里面用到的数据接口是我部署在自己服务器上的后端，可提供使用（别访问太频繁）。

但如果你想了解接口是怎么部署的？

## 如何部署？

首先取决于需要部署前端或者后端，前端作用是利用网页展现数据，而后端是提供数据查询的接口。

### 后端
```
api.py
database.py
```
其中 `database.py` 负责读取 `PostgreSQL` 数据库中的弹幕记录。 `api.py` 利用 `FastAPI` 将数据以网络接口形式返回。

#### 如何运行后端

修改 `database.py` 中第 11 行 `conn = psycopg2.connect(...)` 此处应该为本地（或远程）数据库地址。

参考 [使用python操作postgresql 查询](https://blog.csdn.net/qingfengxd1/article/details/109208027) 。

`api.py` 中第 117 行 `uvicorn.run(app=app, host="0.0.0.0", port=5762)`

表示程序会利用 `uvicorn + FastAPI` 的方式将 api 部署在 `5762` 端口。

参考 [python+uvicorn+fastapi (一) - 认识与第一个DEMO](https://www.cnblogs.com/kknote/p/14985301.html)

接着在当前目录使用 `python api.py` 后，打开浏览器访问 `http://localhost:5762` 查看是否有欢迎页面，若有则代表部署成功。

#### 那么数据从哪来？

[biligo-live-ws-PostgreSQL](https://github.com/Drelf2018/biligo-live-ws-PostgreSQL) 是一个经过改造的弹幕伺服器，原项目 [biligo-live-ws](https://github.com/eric2788/biligo-live-ws) 。

区别在于 `biligo-live-ws-PostgreSQL` 会将弹幕数据记录在 `PostgreSQL` 数据库中，具体使用方法可在 [releases](https://github.com/Drelf2018/biligo-live-ws-PostgreSQL/releases) 界面查看。

_注意，此处用到的数据库需与前文提到的一致。_

### 前端
```
cha.py
esu.png
eyes.png
forever.png
notice.py
notice_pic
```
安装 [pywebio](https://github.com/pywebio/PyWebIO) 并使用 `pip install websockets` 安装可能需要的依赖库。

`.png` 是网页中用到的图片资源，`notice.py`、`notice_pic` 是网页中的公告与公告图片。

前端是基本写死了的 `python cha.py` 就能跑，不过应该不需要有人跑这个。

你可以访问 [nana7mi.link](https://nana7mi.link) 。

或者利用阿里云函数计算FC部署 [Aliyun-api-nana7mi-link](https://github.com/Drelf2018/Aliyun-api-nana7mi-link) 。



