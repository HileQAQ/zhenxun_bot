from nonebot import on_command
from nonebot.params import CommandArg
from services.log import logger
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, Message
from nonebot.typing import T_State
from utils.http_utils import AsyncHttpx
from utils.data_utils import _init_rank_graph
from utils.message_builder import image
import datetime

__zx_plugin_name__ = "查看队员训练状态"
__plugin_usage__ = """
usage：
    视监队员训练状态
    指令：
        查看训练状态
""".strip()
__plugin_des__ = "视监队员训练状态"
__plugin_cmd__ = ["查看训练状态"]
__plugin_version__ = 0.1
__plugin_author__ = "Kyooma"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["查看训练状态"],
}

view_training = on_command(
    "查看训练状态", priority=5, block=True
)


@view_training.handle()
async def _(event: GroupMessageEvent, arg: Message = CommandArg()):
    end_time = datetime.datetime.now()
    begin_time = end_time + datetime.timedelta(days=-7)
    end_time = end_time.strftime('%Y-%m-%d')
    begin_time = begin_time.strftime('%Y-%m-%d')
    url = 'https://api.zuccacm.top/mainsite/overview?begin_time={}&end_time={}'.format(begin_time, end_time)
    data = (await AsyncHttpx.get(url)).json()['data']
    res = '最近一周训练状态'
    all_user_id = []
    all_user_data = []
    temp = []
    for group in data:
        for user in group['users']:
            temp.append((user['solved'], user['username']))
    temp.sort(key=lambda x: (x[0], x[1]))
    for i in temp:
        all_user_data.append(i[0])
        all_user_id.append(i[1])
    _image = _init_rank_graph(res, all_user_id, all_user_data)
    await view_training.send(image(b64=_image.pic2bs4()))
