import datetime
from io import BytesIO
from bs4 import BeautifulSoup
import re

from utils.image_utils import BuildImage
from binascii import unhexlify, hexlify
from Crypto.Cipher import AES
import requests
from configs.path_config import IMAGE_PATH
from utils.message_builder import image

VIEW_CF_PATH = IMAGE_PATH / 'view_cf' / 'img'

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


def _get_info(uid):
    try:
        url = f'https://codeforces.com/profile/{uid}'
        html = sess.get(url=url)
        if 'Redirecting...' in html.text:
            html = _set_RCPC(html)
        html = html.text
        soup = BeautifulSoup(html, features='lxml')
        div = soup.select('div[class="title-photo"]')[0]
        src = div.select('img')[0].attrs['src']
        if 'https:' not in src:
            src = 'https:' + src
        ava = sess.get(url=src)
        if 'Redirecting...' in ava.text:
            ava = _set_RCPC(ava)
        ava = ava.content
        rating_div = soup.select('div[class="info"]')[0]
        now_rank = rating_div.select('div[class="user-rank"]')[0].select('span')[0].text
        handle = rating_div.select('a')[0].text
        li = rating_div.select('li')
        spans = li[0].select('span')
        now_rating = spans[0].text
        max_rank = li[0].select('span[class="smaller"]')[0].select('span')[0].text
        max_rating = li[0].select('span[class="smaller"]')[0].select('span')[1].text
        friends = re.search(r'\d+', li[2].text)[0]
        last_visit = li[3].select('span')[0].text
        registered = li[4].select('span')[0].text
        data = {
            'ava': ava,
            'now_rating': now_rating,
            'max_rating': max_rating,
            'friends': friends,
            'max_rank': max_rank,
            'now_rank': now_rank,
            'handle': handle,
            'registered': registered,
            'last_visit': last_visit
        }
        return data
    except Exception as e:
        print(e)
        return f'cfer {uid} not found.'


def _get_color(rating):
    rating = int(rating)
    if rating >= 2400:
        return 255, 0, 0, 0
    elif rating >= 2100:
        return 255, 140, 0, 0
    elif rating >= 1900:
        return 170, 0, 170, 0
    elif rating >= 1600:
        return 0, 0, 225, 0
    elif rating >= 1400:
        return 3, 168, 158, 0
    elif rating >= 1200:
        return 0, 128, 0, 0
    else:
        return 128, 128, 128, 0


def timestamp_to_str(timestamp: int) -> str:
    return datetime.datetime.strftime(
        datetime.datetime.fromtimestamp(
            timestamp, datetime.timezone(datetime.timedelta(hours=8))), '%Y-%m-%d')


def _get_statics(uid):
    url = f'https://codeforces.com/api/user.status?handle={uid}'
    res = sess.get(url=url)
    if 'Redirecting...' in res.text:
        res = _set_RCPC(res)
    res = res.json()
    if res['status'] != 'OK':
        raise Exception('cf_api error')
    now = datetime.datetime.now().strftime('%Y-%m-%d')
    res = res['result']
    ac = 0
    sum = 0
    max_rating = 0
    pid = ''
    for i in res:
        time = timestamp_to_str(i['creationTimeSeconds'])
        if time != now:
            break
        sum = sum + 1
        if i['verdict'] == 'OK':
            ac = ac + 1
            if 'rating' in i['problem']:
                if i['problem']['rating'] > max_rating:
                    max_rating = i['problem']['rating']
                    pid = str(i['problem']['contestId']) + i['problem']['index']
    return {'max_rating': max_rating, 'pid': pid, 'ac': ac, 'sum': sum}


def _generate_card(uid):
    data = _get_info(uid)
    if 'ava' not in data:
        return data
    # print(data)
    ava = BytesIO(data['ava'])
    _ava = BuildImage(300, 400, background=ava)
    rating = BuildImage(24, 24, background=VIEW_CF_PATH / "rating.png")
    star = BuildImage(24, 24, background=VIEW_CF_PATH / "star.png")
    today_info = _get_statics(uid)
    now_rank = BuildImage(
        0,
        0,
        plain_text=data['now_rank'],
        color=_get_color(data['now_rating']),
        font_size=15,
        font_color=_get_color(data['now_rating'])[0:3],
        is_alpha=True)
    handle = BuildImage(
        0,
        0,
        plain_text=data['handle'],
        color=_get_color(data['now_rating']),
        font_size=35,
        font_color=_get_color(data['now_rating'])[0:3], )
    now_rating = BuildImage(
        0,
        0,
        plain_text=data['now_rating'],
        color=_get_color(data['now_rating']),
        font_size=20,
        font_color=_get_color(data['now_rating'])[0:3], )
    max = BuildImage(
        0,
        0,
        plain_text='max:',
        color=(0, 0, 0, 0),
        font_size=18,
        font_color=(0, 0, 0),)
    rat = BuildImage(
        0,
        0,
        plain_text='Rating:',
        color=(0, 0, 0, 0),
        font_size=20,
        font_color=(0, 0, 0), )
    max_rating = BuildImage(
        0,
        0,
        plain_text=data['max_rank'] + data['max_rating'],
        color=_get_color(data['max_rating']),
        font_size=18,
        font_color=_get_color(data['max_rating'])[0:3], )
    cnt = data['friends']
    friends = BuildImage(
        0,
        0,
        plain_text=f'Friend of: {cnt} users',
        color=(0, 0, 0, 0),
        font_size=20,
        font_color=(0, 0, 0), )
    last = data['last_visit']
    last_visit = BuildImage(
        0,
        0,
        plain_text=f'Last visit: {last}',
        color=(0, 0, 0, 0),
        font_size=20,
        font_color=(0, 0, 0), )
    register = data['registered']
    registered = BuildImage(
        0,
        0,
        plain_text=f'Registered: {register}',
        color=(0, 0, 0, 0),
        font_size=20,
        font_color=(0, 0, 0), )
    sum = today_info['sum']
    ac = today_info['ac']
    statics = BuildImage(
        0,
        0,
        plain_text=f'Today Status: accepted {ac} / submitted {sum}',
        color=(0, 0, 0, 0),
        font_size=20,
        font_color=(0, 0, 0), )
    pid = today_info['pid']
    p_rating = today_info['max_rating']
    msg = f'Today Max Rate Problem: {pid} - {p_rating}'
    if pid == '':
        msg = 'Today Max Rate Problem: None'
    hard_problem = BuildImage(
        0,
        0,
        plain_text=msg,
        color=(0, 0, 0, 0),
        font_size=20,
        font_color=(0, 0, 0), )
    bk = BuildImage(876, 424, font_size=25, background=VIEW_CF_PATH / "white.png")
    bk.paste(_ava, (10, 12), True)
    bk.paste(now_rank, (320, 12), True)
    bk.paste(handle, (320, 32), True)
    bk.paste(rating, (320, 92), True)
    bk.paste(rat, (350, 92), True)
    bk.paste(now_rating, (430, 92), True)
    bk.paste(max, (510, 92), True)
    bk.paste(max_rating, (555, 92), True)
    bk.paste(star, (320, 142), True)
    bk.paste(friends, (350, 142), True)
    bk.paste(statics, (320, 192), True)
    bk.paste(hard_problem, (320, 242), True)
    bk.paste(last_visit, (320, 292), True)
    bk.paste(registered, (320, 342), True)
    bk.save(IMAGE_PATH / 'view_cf' / "today_card" / f"{uid}.png")
    return image(IMAGE_PATH / 'view_cf' / "today_card" / f"{uid}.png")


if __name__ == "__main__":
    print(_get_info('Kyooma'))
