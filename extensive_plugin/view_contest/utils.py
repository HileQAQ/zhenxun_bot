import re
from datetime import datetime, timedelta

import requests
from binascii import unhexlify, hexlify
from Crypto.Cipher import AES
from bs4 import BeautifulSoup

sess = requests.session()


def _set_RCPC(resp):
    res = re.findall('toNumbers\("(.+?)"\)', resp.text)
    text = unhexlify(res[2].encode('utf-8'))
    key = unhexlify(res[0].encode('utf-8'))
    iv = unhexlify(res[1].encode('utf-8'))

    aes = AES.new(key, AES.MODE_CBC, iv)
    res = hexlify(aes.decrypt(text)).decode('utf-8')
    sess.cookies.set('RCPC', res, domain='.codeforces.com', path='/')
    url = re.findall('href="(.+?)"', resp.text)[0]
    return sess.get(url=url)


def getCodeforces():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
        'origin': 'https://codeforces.com/'
    }
    url = 'https://codeforces.com/contests'
    now = datetime.now()
    contests = []
    try:
        res = sess.get(url=url, headers=headers)
        if 'Redirecting...' in res.text:
            res = _set_RCPC(res)
        soup = BeautifulSoup(res.text, features='lxml')
        divs = soup.select('div[class="datatable"]')[0]
        trs = divs.find_all('tr')[1:]
        for i in trs:
            tds = i.find_all('td')
            url = tds[2].select('a')[0].attrs['href']
            d = re.findall(r'\d+', url)
            time = '{}-{}-{} {}:{}:{}'.format(d[2], d[1], d[0], d[3], d[4], d[5])
            contest_time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S') + timedelta(hours=5)
            if contest_time.strftime('%Y-%m-%d') == now.strftime('%Y-%m-%d'):
                content = re.findall(r'[^\n\r]', tds[0].text)
                while content[-1] == ' ':
                    content.pop()
                content = ''.join(content)
                contests.append({
                    'name': content,
                    'time': contest_time.strftime('%Y-%m-%d %H:%M:%S')
                })
    except:
        print('getCF Error!!!')
    return contests


def getAtcoder():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
        'origin': 'https://atcoder.jp/contests/'
    }
    url = 'https://atcoder.jp/contests/'
    contests = []
    now = datetime.now()
    try:
        res = requests.get(url=url, headers=headers)
        soup = BeautifulSoup(res.text, features='lxml')
        div = soup.select('#contest-table-upcoming')[0]
        trs = div.find_all('tr')[1:]
        for tr in trs:
            tds = tr.select('td')
            contest_time = tds[0].text
            pos = contest_time.find('+')  # 获取最后一个+的位置
            if pos != -1:
                contest_time = contest_time[0:pos]
            contest_time = datetime.strptime(contest_time, '%Y-%m-%d %H:%M:%S')
            contest_time = contest_time + timedelta(hours=-1)
            name = tds[1].select('a')[0].text
            if contest_time.strftime('%Y-%m-%d') == now.strftime('%Y-%m-%d'):
                contests.append({
                    'name': name,
                    'time': contest_time.strftime('%Y-%m-%d %H:%M:%S')
                })
    except:
        print('getATC Error!!!')
    return contests


def getNowCoder():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
        'origin': 'https://ac.nowcoder.com/acm/contest/vip-index'
    }
    url = 'https://ac.nowcoder.com/acm/contest/vip-index'
    now = datetime.now()
    contests = []
    try:
        res = requests.get(url=url, headers=headers)
        soup = BeautifulSoup(res.text, features='lxml')
        div = soup.select('div[class="platform-mod js-current"]')[0]
        divs = div.select('div[class="platform-item-cont"]')
        for i in divs:
            name = i.select('a')[0].text
            content = i.select('li')[1].text
            contest_time = re.findall(r'\d+-\d+-\d+ \d+:\d+', content)[0]
            contest_time = datetime.strptime(contest_time, '%Y-%m-%d %H:%M')
            if contest_time.strftime('%Y-%m-%d') == now.strftime('%Y-%m-%d'):
                contests.append({
                    'name': name,
                    'time': contest_time.strftime('%Y-%m-%d %H:%M:%S')
                })
    except:
        print('getNowCoder Error!!')
    return contests


def getToday():
    contests = []
    cf_contests = getCodeforces()
    contests.extend(cf_contests)
    atc_contests = getAtcoder()
    contests.extend(atc_contests)
    nc_contests = getNowCoder()
    contests.extend(nc_contests)
    message = '今日没有比赛哦~'
    if len(contests) > 0:
        message = '提醒小助手提醒您今日有比赛哦~\n'
        for i in contests:
            message += '\n比赛名称: ' + i.get('name') + '\n比赛时间: ' + i.get('time') + '\n'
    return message
