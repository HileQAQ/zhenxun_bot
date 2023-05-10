from nonebot import on_command
from nonebot.params import CommandArg

from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, Message
from nonebot import require, get_bot
from .utils import getToday

__zx_plugin_name__ = "查看当日比赛情况"
__plugin_usage__ = """
usage：
    查看当日比赛(支持atc, nowcoder, cf)
    指令：
        今日比赛
""".strip()
__plugin_des__ = "查看当日比赛情况"
__plugin_cmd__ = ["今日比赛"]
__plugin_version__ = 0.1
__plugin_author__ = "Kyooma"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["今日比赛"],
}

view_contest = on_command(
    "今日比赛", priority=5, block=True
)
cf_helper = require("nonebot_plugin_apscheduler").scheduler


@view_contest.handle()
async def _(event: GroupMessageEvent, arg: Message = CommandArg()):
    msg = getToday()
    await view_contest.send(msg)


@cf_helper.scheduled_job("cron", hour=21, minute=0)
async def get_night_contest():
    msg = getToday()
    bot = get_bot()
    if msg != '今日没有比赛哦~':
        await bot.send_group_msg(group_id=636840605, message=msg)


@cf_helper.scheduled_job("cron", hour=10, minute=0)
async def get_morning_contest():
    msg = getToday()
    bot = get_bot()
    if msg != '今日没有比赛哦~':
        await bot.send_group_msg(group_id=636840605, message=msg)
