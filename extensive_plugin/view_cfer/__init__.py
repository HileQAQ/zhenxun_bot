from nonebot import on_command
from nonebot.params import CommandArg

from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message
from .utils import _generate_card

__zx_plugin_name__ = "视监cfer"
__plugin_usage__ = """
usage：
    查看cf详情与当天训练状况
    指令：
        视监 + id
""".strip()
__plugin_des__ = "视监cfer"
__plugin_cmd__ = ["视监"]
__plugin_version__ = 0.1
__plugin_author__ = "Kyooma"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["视监"],
}

view_cfer = on_command(
    "视监", priority=5, block=True
)


@view_cfer.handle()
async def _(event: GroupMessageEvent, arg: Message = CommandArg()):
    msg = str(event.get_message()).strip()
    msg = msg.replace('视监', '')
    msg = msg.replace(' ', '')
    print(msg)
    await view_cfer.send(_generate_card(msg))
