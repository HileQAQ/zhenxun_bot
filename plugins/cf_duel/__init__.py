import asyncio
import datetime
import random
import time
import json
import aiohttp
from plugins import command, scheduler
from utils import db

@command(name='bind', permission=1)
async def bind(bot, event, *args):
    if len(args) < 1:
        return 'Invalid parameters. Usage: !bind <Codeforces ID>'
    cf_id = args[0]
    # 查询用户是否提交了1A题目
    url = f'https://codeforces.com/api/user.status?handle={cf_id}&from=1&count=1'
    # 如果1min内未提交1A题目，则提示“绑定失败”
    start_time = datetime.datetime.now()
    timeout = datetime.timedelta(minutes=1)
    while True:
        elapsed_time = datetime.datetime.now() - start_time
        if elapsed_time >= timeout:
            await bot.send_group_msg(group_id=event['group_id'], message='Binding failed: You did not submit problem 1A within 1 minute.')
            break
        await asyncio.sleep(5)
        # 再次查询用户是否提交了1A题目
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
        if data['status'] != 'COMPILATION_ERROR':
            continue
        if len(data['result']) == 0:
            continue
        submission = data['result'][0]
        if submission['problem']['contestId'] == 1 and submission['problem']['index'] == 'A' and submission['verdict'] == 'COMPILATION_ERROR':
            db.set(str(event['user_id']), cf_id)
            await bot.send_group_msg(group_id=event['group_id'], message='Binding successful.')
            break

async def check_submission(qq_id, cf_id):
    # 使用Codeforces API查询该用户是否提交了1A题目
    url = f'https://codeforces.com/api/user.status?handle={cf_id}&from=1&count=1'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
    if data['status'] != 'COMPILATION_ERROR':
        return
    if len(data['result']) == 0:
        return
    submission = data['result'][0]
    if submission['problem']['contestId'] == 1 and submission['problem']['index'] == 'A' and submission['verdict'] == 'COMPILATION_ERROR':
        # 如果提交了1A题目且CE了，发送QQ消息提醒
        await bot.send_private_msg(user_id=qq_id, message='身份验证成功喵')

@scheduler(interval=60)
async def check_submissions(bot):
    # 查询所有绑定了Codeforces ID的QQ号
    qq_ids = db.keys()
    for qq_id in qq_ids:
        cf_id = db.get(qq_id)
        if cf_id is not None:
            asyncio.ensure_future(check_submission(qq_id, cf_id))

@command(name='duel', permission=1)
async def duel(bot, event, *args):
    if len(args) < 2:
        return 'Invalid parameters. Usage: !duel <user_id> <rating>'
    user_id = event['user_id']
    opponent_id = args[0]
    rating = args[1]
    # 检查用户A和用户B是否都绑定了Codeforces账号
    user_cf_id = db.get(str(user_id))
    opponent_cf_id = db.get(opponent_id)
    if user_cf_id is None or opponent_cf_id is None:
        return 'Both users must bind their Codeforces account in order to start a duel.'
    # 随机选一道分数为<rating>的题目
    url = f'https://codeforces.com/api/problemset.problems?tags=implementation&minRating={rating}&maxRating={rating}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
    if data['status'] != 'OK':
        return 'Failed to fetch problems from Codeforces.'
    problems = data['result']['problems']
    if len(problems) == 0:
        return 'No problems found with the given rating.'
    problem = random.choice(problems)
    problem_url = f'https://codeforces.com/problemset/problem/{problem["contestId"]}/{problem["index"]}'
    # 将题目发送到聊天窗口
    await bot.send_group_msg(group_id=event['group_id'], message=f'Duel started! {user_id} vs. {opponent_id} Problem: {problem_url}')
    # 启动一个异步任务，等待用户A或用户B通过题目
    asyncio.ensure_future(wait_for_ac(bot, event, user_id, opponent_id, problem))

async def wait_for_ac(bot, event, user_id, opponent_id, problem):
    start_time = datetime.datetime.now()
    timeout = datetime.timedelta(hours=1)
    while True:
        # 检查用户A是否通过题目
        user_ac = await check_ac(user_id, problem)
        if user_ac:
            await bot.send_group_msg(group_id=event['group_id'], message=f'Duel ended! Winner: {db.get(str(user_id))}')
            break
        # 检查用户B是否通过题目
        opponent_ac = await check_ac(opponent_id, problem)
        if opponent_ac:
            await bot.send_group_msg(group_id=event['group_id'], message=f'Duel ended! Winner: {db.get(opponent_id)}')
            break
        # 如果超过了1小时仍然没有结果，结束决斗
        elapsed_time = datetime.datetime.now() - start_time
        if elapsed_time >= timeout:
            await bot.send_group_msg(group_id=event['group_id'], message='Duel timed out.')
            break
        # 等待1分钟再重复检查
        await asyncio.sleep(60)

async def check_ac(user_id, problem):
    # 使用Codeforces API查询指定用户是否通过了指定题目
    url = f'https://codeforces.com/api/user.status?handle={db.get(str(user_id))}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
    if data['status'] != 'OK':
        return False
    for submission in data['result']:
        if submission['problem']['contestId'] == problem['contestId'] and submission['problem']['index'] == problem['index'] and submission['verdict'] == 'OK':
            return True
    return False
