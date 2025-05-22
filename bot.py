import urllib3
urllib3.disable_warnings()

import requests
import time
import os
from concurrent.futures import ThreadPoolExecutor
from colorama import Fore, Style, init
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import random
import telebot
import hashlib
import string
from faker import Faker
from urllib.parse import urljoin, urlparse, urldefrag
from telebot import types

fake = Faker()

init(autoreset=True)

# Các biến cố định
__AUTHOR__ = 'Nguyễn Văn Phúc'
__CONTACT__ = 'https://www.facebook.com/100037043542788'
__TOOL_NAME__ = 'Bot Tiện Ích'
THỜI_GIAN_CHỜ = timedelta(seconds=300)
GIỚI_HẠN_CHIA_SẺ = 1000
ALLOWED_GROUP_IDS = [-1002235214987, -1002239701736, -4278958450]
TOKEN = '7001901118:AAGZz4YsJ_A3KlrkrO8Cs9xfgNSzzn2WhuI'  # Token của bot
bot = telebot.TeleBot(TOKEN)

# Các biến toàn cục
user_cooldowns = {}
admins = {6076210951}
share_count = {}
bot_active = True
user_keys = {}
admins = set()

# Thông tin đăng nhập traodoisub.com
USERNAME = 'nguyenvanphuc07'
PASSWORD = '31012007'
# Hàm kiểm tra nếu người dùng là admin
def is_admin(user_id):
    return user_id in admins
# Hàm đăng nhập vào tài khoản traodoisub.com và lấy PHPSESSID
def login_tds(username, password):
    login_url = 'https://traodoisub.com/scr/login.php'
    data = {
        'username': username,
        'password': password,
        'submit': 'Đăng nhập'
    }

    session = requests.Session()
    response = session.post(login_url, data=data)

    if 'PHPSESSID' in session.cookies:
        return session.cookies['PHPSESSID']
    else:
        return None

# Hàm mua tim cho video TikTok
def buy_hearts_tiktok(phpsessid, video_url, amount):
    buy_url = 'https://traodoisub.com/mua/tiktok_like/themid.php'
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cookies = {
        'PHPSESSID': phpsessid,
    }

    headers = {
        'accept': '*/*',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://traodoisub.com',
        'referer': 'https://traodoisub.com/mua/tiktok_like/',
        'x-requested-with': 'XMLHttpRequest',
    }

    data = {
        'maghinho': '',
        'id': video_url,
        'sl': amount,
        'dateTime': current_time,
    }

    response = requests.post(buy_url, cookies=cookies, headers=headers, data=data)
    return response.status_code, response.text

# Xử lý lệnh /getkey
@bot.message_handler(commands=['getkey'])
def get_key(message):
    username = message.from_user.username
    user_id = message.from_user.id  
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    key_string = f'darling-{username}+{timestamp}'
    key = hashlib.md5(key_string.encode()).hexdigest()

    with open('key.txt', 'a') as f:
        f.write(f'{key}\n')

    url_key = requests.get(f'https://partner.8link.io/api/public/gen-shorten-link?apikey=017e87a9ab3a6198ad34d3d9b8669dac46161f4ba45811b46377fbb5fa45ab67&url=https://offvn.io.vn/vphc.html?key={key}').json()['shortened_url']
    text = f'''
- Link Lấy Key {timestamp} là: {url_key} -
- Khi lấy key xong dùng lệnh /key {{key}} để check key
- Nếu đã nhập key thì chỉ cần /key True
    '''
    bot.send_message(message.chat.id, text)
    
    # Gửi key cho các admin
    for admin_id in admins:
        admin_message = f"{user_id}: {key}"
        bot.send_message(admin_id, admin_message)

# Xử lý lệnh /key
@bot.message_handler(commands=['key'])
def check_key(message):
    try:
        username = message.from_user.username
        key = message.text.split(' ', 1)[1] if len(message.text.split()) > 1 else ''
        key_string = f'darling-{username}+{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        valid_key = hashlib.md5(key_string.encode()).hexdigest()

        with open('key.txt', 'r') as f:
            keys = f.read().splitlines()

        if key in keys or key == 'True':
            user_keys[message.from_user.id] = valid_key
            bot.send_message(message.chat.id, 'Key đúng! 🔓')
        else:
            bot.send_message(message.chat.id, 'Key sai! 🔒\n- Vui lòng nhập đúng định dạng /key {key}')
    except:
        bot.send_message(message.chat.id, 'Key không hợp lệ ❌!')

# Xử lý lệnh /addadmin
@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "Bạn không có quyền sử dụng lệnh này.")
        return

    try:
        params = message.text.split()
        if len(params) != 2:
            bot.reply_to(message, "Vui lòng nhập ID admin theo định dạng: /addadmin <user_id>")
            return

        new_admin_id = int(params[1])
        
        if new_admin_id in admins:
            bot.reply_to(message, "Người dùng đã là admin.")
            return
        
        # Thêm admin vào danh sách
        admins.add(new_admin_id)
        bot.reply_to(message, f"Đã thêm ID {new_admin_id} vào danh sách admin.")

        # Cập nhật danh sách admin trong tệp
        with open('admins.txt', 'a') as f:
            f.write(f'{new_admin_id}\n')

    except ValueError:
        bot.reply_to(message, "ID không hợp lệ. Vui lòng nhập số.")
    except Exception as e:
        bot.reply_to(message, f"Đã xảy ra lỗi: {str(e)}")

# Nạp danh sách admin từ tệp khi khởi động
def load_admins():
    global admins
    if os.path.exists('admins.txt'):
        with open('admins.txt', 'r') as f:
            admins = set(map(int, f.read().splitlines()))

# Gọi hàm load_admins khi khởi động bot
load_admins()

# Xử lý lệnh /tim (bổ sung từ mã nguồn của bạn)
@bot.message_handler(commands=['tim'])
def handle_tim(message):
    if not is_admin(message.from_user.id) and message.from_user.id not in user_keys:
        bot.reply_to(message, "Vui lòng nhập key đúng trước khi sử dụng lệnh /tim.")
        return

    try:
        params = message.text.split()
        if len(params) < 2:
            bot.reply_to(message, "Vui lòng nhập URL video TikTok theo định dạng: /tim <video_url>")
            return

        video_url = params[1]
        amount = '50'  # Số lượng tim mặc định là 50

        phpsessid = login_tds(USERNAME, PASSWORD)
        
        if not phpsessid:
            bot.reply_to(message, "Đăng nhập thất bại. Vui lòng kiểm tra lại thông tin đăng nhập.")
            return

        status_code, response_text = buy_hearts_tiktok(phpsessid, video_url, amount)
        
        if status_code == 200:
            user_id = message.from_user.id
            username = message.from_user.username
            full_name = message.from_user.full_name
            
            success_message = (
                "Mua Thành Công\n\n"
                "Thông tin người mua\n"
                f"Uid: {user_id}\n"
                f"Tên Người Dùng: @{username}\n"
                f"Họ tên: {full_name}\n"
                f"Số lượng mua: {amount}\n"
                f"Link : {video_url}\n\n"
                "Cre: @abcdxyz310107"
            )
            bot.reply_to(message, success_message)
        else:
            bot.reply_to(message, f"Mua tim thất bại. Status Code: {status_code}, Response: {response_text}")

    except Exception as e:
        bot.reply_to(message, f"Đã xảy ra lỗi: {str(e)}")
# Class từ code 1
class KsxKoji:
    def __Get_ThongTin__(self, cookie):
        id_ck = cookie.split('c_user=')[1].split(';')[0]
        a = requests.get('https://mbasic.facebook.com/profile.php?='+id_ck, headers={'cookie': cookie}).text
        try:
            self.name = a.split('<title>')[1].split('</title>')[0]
            self.fb_dtsg = a.split('<input type="hidden" name="fb_dtsg" value="')[1].split('"')[0]
            self.jazoest = a.split('<input type="hidden" name="jazoest" value="')[1].split('"')[0]
            return True
        except:
            return False

    def __Get_Page__(self, cookie):
        self.dem = 0
        data = {
            'fb_dtsg': self.fb_dtsg,
            'jazoest': self.jazoest,
            'variables': '{"showUpdatedLaunchpointRedesign":true,"useAdminedPagesForActingAccount":false,"useNewPagesYouManage":true}',
            'doc_id': '5300338636681652'
        }
        getidpro5 = requests.post('https://www.facebook.com/api/graphql/', headers={'cookie': cookie}, data=data).json()['data']['viewer']['actor']['profile_switcher_eligible_profiles']['nodes']
        list_page = []
        for uidd in getidpro5:
            self.dem += 1
            uid_page = uidd['profile']['id']
            list_page.append(uid_page)
        return list_page

    def __Follow__(self, cookie, id, taget):
        self.headers = {
            'accept': '*/*',
            'accept-language': 'vi,vi-VN;q=0.9,en;q=0.8',
            'cache-control': 'max-age=0',
            'content-encoding': 'br',
            'content-type': 'application/x-www-form-urlencoded',
            'cookie': f'{cookie} i_user={id};',
            'origin': 'https://www.facebook.com',
            'referer': 'https://www.facebook.com',
            'sec-ch-prefers-color-scheme': 'light',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'sec-gpc': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        }
        data = {
            'av': id,
            '__user': id,
            'fb_dtsg': self.fb_dtsg,
            'jazoest': self.jazoest,
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'CometUserFollowMutation',
            'variables': '{"input":{"attribution_id_v2":"ProfileCometTimelineListViewRoot.react,comet.profile.timeline.list,tap_search_bar,1713671419755,394049,190055527696468,,","is_tracking_encrypted":false,"subscribe_location":"PROFILE","subscribee_id":"'+taget+'","tracking":null,"actor_id":"'+id+'","client_mutation_id":"19"},"scale":1}',
            'server_timestamps': 'true',
            'doc_id': '7393793397375006',
        }

        follow = requests.post('https://www.facebook.com/api/graphql/', headers=self.headers, data=data)
        try:
            check = follow.json()['errors']
            for i in check:
                if i['summary'] == 'Tài khoản của bạn hiện bị hạn chế':
                    return 'block'
        except:
            if 'IS_SUBSCRIBED' in follow.text:
                return True
            else:
                return False

# Lệnh /cookie chỉ cho chat riêng với bot
@bot.message_handler(commands=['cookie'])
def process_cookie(message):
    if message.chat.type != 'private':
        bot.reply_to(message, 'Lệnh này chỉ dùng trong chat riêng với bot.')
        return
    
    cookie = ' '.join(message.text.split()[1:])
    if 'c_user=' in cookie:
        f = KsxKoji()
        fb = f.__Get_ThongTin__(cookie)
        if fb:
            list_page = f.__Get_Page__(cookie)
            response = f"Name Profile: {f.name} | Có {f.dem} Page"
            with open('list_cookie.txt', 'a+') as file:
                file.write(cookie + '\n')
        else:
            response = 'Cookie không hợp lệ hoặc đã hết hạn.'
    else:
        response = 'Cookie không đúng định dạng.'
    
    bot.reply_to(message, response)

# Lệnh /follow chỉ cho chat trong group
@bot.message_handler(commands=['follow'])
def follow_profile(message):
    if not bot_active:
        bot.reply_to(message, 'Bot hiện đang tắt')
        return
    
    if message.chat.id not in ALLOWED_GROUP_IDS:
        bot.reply_to(message, 'Xin lỗi, bot này chỉ hoạt động trong nhóm này https://t.me/geminivipchat.')
        return
    
    args = message.text.split()[1:]
    if len(args) < 2:
        bot.reply_to(message, 'Vui lòng nhập ID và số lượng.')
        return
    
    taget = args[0]
    so_luong = int(args[1])
    delay = 10  # Đặt delay 
    
    x = 0
    dem = 0
    dem_ck = 0
    follow_success = 0
    follow_fail = 0
    with open('list_cookie.txt', 'r') as file:
        open_file = file.read().splitlines()
    
    list_page = []
    
    # Gửi thông báo khi bắt đầu lệnh follow
    message_follow = bot.reply_to(
        message,
        "Đang Tiến Hành Buff Sub\n"
        "╭───────────────╮\n"
        f"│» UID: {taget}\n"
        f"│» Follow thành công: {follow_success}\n"
        f"│» Follow thất bại: {follow_fail}\n"
        "╰───────────────╯"
    )

    while True:
        try:
            cookie = open_file[dem_ck]
            f = KsxKoji()
            f.__Get_ThongTin__(cookie)
            list_page = f.__Get_Page__(cookie)
            while True:
                try:
                    dem += 1
                    id = list_page[x]
                    fl = f.__Follow__(cookie, id, taget)
                    if fl == True:
                        follow_success += 1
                    elif fl == 'block':
                        bot.reply_to(message, f"Profile {f.name} đã bị block. Chuyển sang profile tiếp theo.")
                        list_page.clear()
                        time.sleep(2)
                        dem_ck += 1
                        x = 0
                        dem = 0
                        break
                    elif fl == False:
                        follow_fail += 1

                    # Cập nhật thông báo theo thời gian thực
                    new_message_text = (
                        "Đang Tiến Hành Buff Sub\n"
                        "╭───────────────╮\n"
                        f"│» UID: {taget}\n"
                        f"│» Follow thành công: {follow_success}\n"
                        f"│» Follow thất bại: {follow_fail}\n"
                        "╰───────────────╯"
                    )

                    # Chỉ cập nhật nếu nội dung mới khác nội dung hiện tại
                    if new_message_text != message_follow.text:
                        bot.edit_message_text(
                            chat_id=message.chat.id,
                            message_id=message_follow.message_id,
                            text=new_message_text
                        )
                    
                    x += 1
                    if dem >= so_luong:
                        bot.reply_to(message, f"Thành công {so_luong} sub")
                        return
                    if x >= len(list_page):
                        break
                    time.sleep(delay)
                except IndexError:
                    break
            dem_ck += 1
            if dem_ck >= len(open_file):
                bot.reply_to(message, f"Đã sử dụng hết {dem_ck} cookie, nhưng không đủ để follow {so_luong} lần.")
                break
        except Exception as e:
            bot.reply_to(message, f"Có lỗi xảy ra: {str(e)}")
            break
                       
def banner():
    return f'''
{Fore.GREEN}
╔════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║    {Fore.CYAN}{Style.BRIGHT}{__TOOL_NAME__}{Fore.GREEN}                                        ║
║                                                                        ║
╠════════════════════════════════════════════════════════════════════════╣
║    {Fore.YELLOW}Author  : {Fore.WHITE}{__AUTHOR__}{Fore.GREEN}                                         ║
║    {Fore.YELLOW}Contact : {Fore.WHITE}{__CONTACT__}{Fore.GREEN}                          ║
╚════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
    '''

def share_post(token, post_id, share_number):
    headers = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate',
        'connection': 'keep-alive',
        'content-length': '0',
        'host': 'graph.facebook.com'
    }
    try:
        url = f'https://graph.facebook.com/me/feed'
        params = {
            'link': f'https://m.facebook.com/{post_id}',
            'published': '0',
            'access_token': token
        }
        res = requests.post(url, headers=headers, params=params).json()
        print(f"{Fore.GREEN}{share_number}: Chia sẻ bài viết thành công: {res}{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}Lỗi khi chia sẻ bài viết: {e}{Fore.RESET}")

def get_facebook_post_id(post_url):
    try:
        response = requests.get('https://chongluadao.x10.bz/api/fb/getidfbvinhq.php?url=' + post_url, verify=False)
        response.raise_for_status()
        data = response.json()
        post_id = data.get("id")
        if post_id:
            return post_id
        else:
            raise Exception("Không tìm thấy ID bài viết")
    except Exception as e:
        return f"Lỗi: {e}"

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    username = message.from_user.username
    name_bot = bot.get_me().first_name  # Lấy tên của bot

    if chat_id in ALLOWED_GROUP_IDS:
        msg = bot.reply_to(
            message, 
            f"<blockquote>┌───⭓ {name_bot}\n"
            f"│» Xin chào @{username}\n"
            f"│» /share : Buff share bài viết Facebook\n"
            f"│» /idfb : Get id Facebook \n"
            f"│» /cookie : để góp page follow Facebook\n"
            f"│» /follow : Follow Facebook\n"
            f"│» /tim : Buff tim TikTok\n"
            f"│» /in4 : Lấy ID Tele Của Bản Thân\n"
            f"│» /tiktok : Tải Video Tiktok.\n"
            f"│» /ff : Check tài khoản Free Fire\n"
            f"│» /tt : Check thông tin tài khoản TikTok\n"
            f"│» /code : Lấy Code html của web\n"
            f"│» /tv : Đổi Ngôn Ngữ Sang Tiếng Việt\n"
            f"│» Lệnh Cho ADMIN\n"
            f"│» /on : Bật bot\n"
            f"│» /off : Tắt bot\n"
            f"└───────────⧕</blockquote>", parse_mode='HTML') 
        time.sleep(30)
        try:
            bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Error deleting message: {e}")
    else:
        msg = bot.reply_to(message, 'Xin lỗi, bot này chỉ hoạt động trong nhóm này https://t.me/geminivipchat.')
        time.sleep(10)
        try:
            bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Error deleting message: {e}")

@bot.message_handler(commands=['share'])
def share(message):
    global bot_active
    if not bot_active:
        msg = bot.reply_to(message, 'Bot hiện đang tắt.')
        time.sleep(10)
        try:
            bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Error deleting message: {e}")
        return

    chat_id = message.chat.id
    if chat_id not in ALLOWED_GROUP_IDS:
        msg = bot.reply_to(message, 'Xin lỗi, bot này chỉ hoạt động trong nhóm này https://t.me/geminivipchat.')
        time.sleep(10)
        try:
            bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Error deleting message: {e}")
        return

    chat_id = message.chat.id
    if chat_id not in ALLOWED_GROUP_IDS:
        msg = bot.reply_to(message, 'Xin lỗi, bot này chỉ hoạt động trong nhóm này https://t.me/geminivipchat.')
        time.sleep(10)
        try:
            bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Error deleting message: {e}")
        return
    
    global user_cooldowns
    user_id = message.from_user.id
    current_time = datetime.now()
    
    if user_id not in admins:
        if user_id in user_cooldowns:
            last_share_time = user_cooldowns[user_id]
            if current_time < last_share_time + THỜI_GIAN_CHỜ:
                remaining_time = (last_share_time + THỜI_GIAN_CHỜ - current_time).seconds
                msg = bot.reply_to(message, f'Bạn cần đợi {remaining_time} giây trước khi chia sẻ lần tiếp theo.')
                time.sleep(10)
                try:
                    bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
                except telebot.apihelper.ApiTelegramException as e:
                    print(f"Error deleting message: {e}")
                return
    
    try:
        args = message.text.split()
        if len(args) != 3:
            msg = bot.reply_to(message, '+/share {link_buff} {số lần chia sẻ}')
            time.sleep(10)
            try:
                bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
            except telebot.apihelper.ApiTelegramException as e:
                print(f"Error deleting message: {e}")
            return

        post_url, total_shares = args[1], int(args[2])
        post_id = get_facebook_post_id(post_url)

        if isinstance(post_id, str) and post_id.startswith("Lỗi"):
            msg = bot.reply_to(message, post_id)
            time.sleep(10)
            try:
                bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
            except telebot.apihelper.ApiTelegramException as e:
                print(f"Error deleting message: {e}")
            return

        if user_id not in admins and total_shares > GIỚI_HẠN_CHIA_SẺ:
            msg = bot.reply_to(message, f'Số lần chia sẻ vượt quá giới hạn {GIỚI_HẠN_CHIA_SẺ} lần.')
            time.sleep(10)
            try:
                bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
            except telebot.apihelper.ApiTelegramException as e:
                print(f"Error deleting message: {e}")
            return

        file_path = 'tokens.txt'
        
        with open(file_path, 'r') as file:
            tokens = file.read().split('\n')

        total_live = len(tokens)
        
        msg = bot.reply_to(message, 
            f'ʙᴏᴛ ꜱʜᴀʀᴇ ʙᴀ̀ɪ ᴠɪᴇ̂́ᴛ\n\n'
            f'╔═══════════════╗\n'
            f'║Số lần share: {total_shares}\n'
            f'║𝝩ổ𝖓𝗴 Token: {total_live}\n'
            f'║𝝩𝗶𝗺𝐞 delay?: 1S\n'
            f'╚═══════════════╝\n'
            f'-𝗡𝗴ườ𝗶 𝗱ù𝖓𝗴: {message.from_user.username}',
            parse_mode='HTML'
        )
        time.sleep(10)
        try:
            bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Error deleting message: {e}")

        if total_live == 0:
            msg = bot.reply_to(message, 'Không có token nào hoạt động.')
            time.sleep(10)
            try:
                bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
            except telebot.apihelper.ApiTelegramException as e:
                print(f"Error deleting message: {e}")
            return

        def share_with_delay(token, post_id, count):
            share_post(token, post_id, count)
            time.sleep(2)

        with ThreadPoolExecutor() as executor:
            futures = []
            for i in range(total_shares):
                token = random.choice(tokens)
                share_number = share_count.get(user_id, 0) + 1
                share_count[user_id] = share_number
                futures.append(executor.submit(share_with_delay, token, post_id, share_number))
            for future in futures:
                future.result()
        
        user_cooldowns[user_id] = current_time
        msg = bot.reply_to(message, 'Đơn của bạn đã hoàn thành')
        time.sleep(5)
        try:
            bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Error deleting message: {e}")

    except Exception as e:
        msg = bot.reply_to(message, f'Lỗi: {e}')
        time.sleep(10)
        try:
            bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Error deleting message: {e}")

@bot.message_handler(commands=['idfb'])
def idfb(message):
    chat_id = message.chat.id
    if chat_id not in ALLOWED_GROUP_IDS:
        msg = bot.reply_to(message, 'Xin lỗi, bot này chỉ hoạt động trong nhóm này https://t.me/geminivipchat.')
        time.sleep(10)
        try:
            bot.delete_message(chat_id=message.chat.id,message_id=msg.message_id)
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Error deleting message: {e}")
        return
    
    try:
        link = message.text.split()[1]
        wait = bot.reply_to(message, "🔎")
        get_id_post = requests.post('https://id.traodoisub.com/api.php', data={"link": link}).json()
        if 'success' in get_id_post:
            id_post = get_id_post["id"]
            msg = bot.reply_to(message, f"Lấy id facebook thành công\n+ URL: {link}\n+ ID: `{id_post}`", parse_mode='Markdown')
        else:
            msg = bot.reply_to(message, 'Link không hợp lệ không thể lấy ID')
        time.sleep(10)
        try:
            bot.delete_message(chat_id=message.chat.id, message_id=wait.message_id)
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Error deleting message: {e}")
    except Exception as e:
        msg = bot.reply_to(message, f'Lỗi: {e}')
        time.sleep(10)
        try:
            bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Error deleting message: {e}")

@bot.message_handler(commands=['on'])
def bot_on(message):
    global bot_active
    if message.from_user.id in admins:
        bot_active = True
        bot.reply_to(message, 'Bot đã được bật.')
    else:
        bot.reply_to(message, 'Bạn không có quyền thực hiện thao tác này.')

@bot.message_handler(commands=['off'])
def bot_off(message):
    global bot_active
    if message.from_user.id in admins:
        bot_active = False
        bot.reply_to(message, 'Bot đã được tắt.')
    else:
        bot.reply_to(message, 'Bạn không có quyền thực hiện thao tác này.')

# Các hàm từ đoạn code 2 bắt đầu từ đây

def generate_random_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))

def get_mail_domains():
    url = "https://api.mail.tm/domains"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()['hydra:member']
        else:
            print(f'[×] E-mail Error : {response.text}')
            return None
    except Exception as e:
        print(f'[×] Error : {e}')
        return None

def create_mail_tm_account():
    mail_domains = get_mail_domains()
    if mail_domains:
        domain = random.choice(mail_domains)['domain']
        username = generate_random_string(10)
        password = fake.password()
        birthday = fake.date_of_birth(minimum_age=18, maximum_age=45)
        first_name = fake.first_name()
        last_name = fake.last_name()
        url = "https://api.mail.tm/accounts"
        headers = {"Content-Type": "application/json"}
        data = {"address": f"{username}@{domain}", "password": password}       
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 201:
                print(f'[√] Email Created')
                return f"{username}@{domain}", password, first_name, last_name, birthday
            else:
                print(f'[×] Email Error : {response.text}')
                return None, None, None, None, None
        except Exception as e:
            print(f'[×] Error : {e}')
            return None, None, None, None, None

def register_facebook_account(email, password, first_name, last_name, birthday):
    api_key = '882a8490361da98702bf97a021ddc14d'
    secret = '62f8ce9f74b12f84c123cc23437a4a32'
    gender = random.choice(['M', 'F'])
    req = {
        'api_key': api_key,
        'attempt_login': True,
        'birthday': birthday.strftime('%Y-%m-%d'),
        'client_country_code': 'EN',
        'fb_api_caller_class': 'com.facebook.registration.protocol.RegisterAccountMethod',
        'fb_api_req_friendly_name': 'registerAccount',
        'firstname': first_name,
        'format': 'json',
        'gender': gender,
        'lastname': last_name,
        'email': email,
        'locale': 'en_US',
        'method': 'user.register',
        'password': password,
        'reg_instance': generate_random_string(32),
        'return_multiple_errors': True
    }
    sorted_req = sorted(req.items(), key=lambda x: x[0])
    sig = ''.join(f'{k}={v}' for k, v in sorted_req)
    ensig = hashlib.md5((sig + secret).encode()).hexdigest()
    req['sig'] = ensig
    api_url = 'https://b-api.facebook.com/method/user.register'
    reg = _call(api_url, req)
    id = reg.get('new_user_id', 'N/A')
    token = reg.get('session_info', {}).get('access_token', 'N/A')
    return email, id, token, password, f"{first_name} {last_name}", birthday, gender

def _call(url, params, post=True):
    headers = {'User-Agent': '[FBAN/FB4A;FBAV/35.0.0.48.273;FBDM/{density=1.33125,width=800,height=1205};FBLC/en_US;FBCR/;FBPN/com.facebook.katana;FBDV/Nexus 7;FBSV/4.1.1;FBBK/0;]'}
    if post:
        response = requests.post(url, data=params, headers=headers)
    else:
        response = requests.get(url, params=params, headers=headers)
    return response.json()

@bot.message_handler(commands=['regfb'])
def create_accounts(message):
    try:
        args = message.text.split()
        num_accounts = 1  
        if len(args) > 1:
            try:
                num_accounts = int(args[1])
            except ValueError:
                bot.reply_to(message, "Số lần phải là một số nguyên.")
                return
        
        for _ in range(num_accounts):
            email, password, first_name, last_name, birthday = create_mail_tm_account()
            if email:
                email, id, token, password, name, birthday, gender = register_facebook_account(email, password, first_name, last_name, birthday)
                msg_content = f'''<pre>[+] Email: {email}
[+] ID: {id}
[+] Token: {token}
[+] Password: {password}
[+] Name: {name}
[+] BirthDay: {birthday}
[+] Gender: {gender}
===================================</pre>'''
                bot.reply_to(message, msg_content, parse_mode='HTML')
            else:
                bot.reply_to(message, "Không thể tạo tài khoản email. Vui lòng thử lại sau.")
    except Exception as e:
        bot.reply_to(message, f'Lỗi: {e}')
@bot.message_handler(commands=['in4'])
def get_info(message):
    chat_id = message.chat.id
    message_id = message.message_id
    text = message.text.split()

    def get_user_info(user):
        user_mention = user.first_name
        user_link = f'<a href="tg://user?id={user.id}">{user_mention}</a>'
        user_id = user.id
        username = user.username if user.username else "Không có username"
        full_name = user.full_name if hasattr(user, 'full_name') else "No Name"
        language_code = user.language_code if hasattr(user, 'language_code') else "Không rõ"
        bio = bot.get_chat(user_id).bio or "Không có bio"

        try:
            chat_member = bot.get_chat_member(chat_id, user_id)
            status = chat_member.status
        except Exception as e:
            bot.send_message(chat_id, f"Không thể lấy thông tin thành viên: {e}", parse_mode='HTML')
            return None, None

        status_text = "Thành viên"
        if status == 'administrator':
            status_text = "Quản Trị Viên"
        elif status == 'creator':
            status_text = "Chủ sở hữu"
        elif status == 'member':
            status_text = "Thành viên"
        elif status == 'restricted':
            status_text = "Bị hạn chế"
        elif status == 'left':
            status_text = "Đã rời đi"
        elif status == 'kicked':
            status_text = "Đã bị đuổi"

        info = (f"┌─┤📄 Thông tin của bạn├──⭓\n"
                f"├▷<b>ID</b> : <code>{user_id}</code>\n"
                f"├▷<b>Name</b>: {user_link}\n"
                f"├▷<b>UserName</b>: @{username}\n"
                f"├▷<b>Language</b>: {language_code}\n"
                f"├▷<b>Bio</b>: {bio}\n"
                f"├▷<b>Trạng thái</b>: {status_text}\n"
                f"└───────────────⭓")

        return info, user_id

    if len(text) > 1:
        username = text[1].lstrip('@')
        try:
            user_list = bot.get_chat_administrators(chat_id)
            target_user = None

            for user in user_list:
                if user.user.username == username:
                    target_user = user.user
                    break

            if not target_user:
                bot.send_message(chat_id, f"Không thể tìm thấy thông tin người dùng: @{username}", parse_mode='HTML')
                return

            info, user_id = get_user_info(target_user)

            if info:
                photos = bot.get_user_profile_photos(user_id)
                if photos.total_count > 0:
                    photo_file_id = photos.photos[0][-1].file_id  # Lấy file_id của ảnh có độ phân giải cao nhất
                    bot.send_photo(chat_id, photo_file_id, caption=info, parse_mode='HTML')
                else:
                    bot.send_message(chat_id, "Người dùng không có ảnh đại diện.")

        except Exception as e:
            bot.send_message(chat_id, f"Không thể tìm thấy thông tin người dùng: {e}", parse_mode='HTML')
    else:
        user = message.from_user
        info, user_id = get_user_info(user)

        if info:
            photos = bot.get_user_profile_photos(user_id)
            if photos.total_count > 0:
                photo_file_id = photos.photos[0][-1].file_id  # Lấy file_id của ảnh có độ phân giải cao nhất
                bot.send_photo(chat_id, photo_file_id, caption=info, parse_mode='HTML')
            else:
                bot.send_message(chat_id, "Bạn không có ảnh đại diện.")

    # Delete user's command message
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        bot.send_message(chat_id, f"Không thể xóa tin nhắn: {e}", parse_mode='HTML')
# Hàm xử lý khi người dùng gửi lệnh /tiktok
@bot.message_handler(commands=['tiktok'])
def get_video(message):
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        video_url = args[1]
        api_url = f'https://chongluadao.x10.bz/api/down/tiktokdowndvinh09.php?url={video_url}'
        
        # Gửi request tới API và lấy kết quả trả về
        response = requests.get(api_url)
        
        # Kiểm tra xem API có trả về dữ liệu hay không
        if response.status_code == 200:
            data = response.json().get("data", {})
            
            # Lấy thông tin cần thiết từ dữ liệu API trả về
            title = data.get("title", "Không có tiêu đề")
            author = data.get("author", {}).get("nickname", "Không rõ tác giả")
            region = data.get("region", "Không rõ khu vực")
            duration = data.get("duration", 0)
            create_time = data.get("create_time", "Không rõ thời gian")
            play_count = data.get("play_count", "0")
            digg_count = data.get("digg_count", "0")
            comment_count = data.get("comment_count", "0")
            share_count = data.get("share_count", "0")
            download_count = data.get("download_count", "0")
            collect_count = data.get("collect_count", "0")
            music_url = data.get("music_info", {}).get("play", None)
            
            # Lấy danh sách các URL ảnh và video
            image_urls = data.get("images", [])
            video_url = data.get("play")
            
            # Tạo tin nhắn theo định dạng yêu cầu với HTML
            message_text = f"""
🎥 {title if video_url else 'None'}

<blockquote>👤 Tác giả: {author}
🌍 Khu Vực: {region}
🎮 Độ Dài Video: {duration} Giây
🗓️ Ngày Đăng: {create_time}
---------------------------------------
▶️ Views: {play_count}
❤️ Likes: {digg_count} like
💬 Comments: {comment_count}
🔄 Shares: {share_count}
⬇️ Downloads: {download_count}
📥 Favorites: {collect_count}</blockquote>
"""
            
            # Nếu có video
            if video_url:
                if image_urls:
                    # Gửi tất cả các ảnh trong một tin nhắn
                    media_group = [types.InputMediaPhoto(media=url) for url in image_urls if url]
                    if media_group:
                        bot.send_media_group(message.chat.id, media=media_group)
                
                # Gửi video và tiêu đề trong một tin nhắn văn bản
                bot.send_video(message.chat.id, video=video_url, caption=message_text, parse_mode='HTML')
            else:
                # Nếu chỉ có ảnh (không có video), gửi ảnh
                if image_urls:
                    media_group = [types.InputMediaPhoto(media=url) for url in image_urls if url]
                    if media_group:
                        bot.send_media_group(message.chat.id, media=media_group)
                
                # Gửi thông tin video nếu không có video
                bot.send_message(message.chat.id, message_text, parse_mode='HTML')
        else:
            bot.send_message(message.chat.id, "Không thể lấy thông tin video.")
    else:
        bot.send_message(message.chat.id, "⚠️ Vui lòng nhập url sau lệnh /tiktok.\n💭 Ví dụ: /tiktok https://vt.tiktok.com/abcd/.")
@bot.message_handler(commands=['code'])
def handle_code_command(message):
    # Tách lệnh và URL từ tin nhắn
    command_args = message.text.split(maxsplit=1)

    # Kiểm tra xem URL có được cung cấp không
    if len(command_args) < 2:
        bot.reply_to(message, "Vui lòng cung cấp url sau lệnh /code. Ví dụ: /code https://xnxx.com")
        return

    url = command_args[1]
    domain = urlparse(url).netloc
    file_name = f"{domain}.txt"
    
    try:
        # Lấy nội dung HTML từ URL
        response = requests.get(url)
        response.raise_for_status()  # Xảy ra lỗi nếu có lỗi HTTP

        # Lưu nội dung HTML vào file
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(response.text)

        # Gửi file về người dùng
        with open(file_name, 'rb') as file:
            bot.send_document(message.chat.id, file, caption=f"HTML của trang web {url}")

        # Phản hồi tin nhắn gốc
        bot.reply_to(message, "Đã gửi mã nguồn HTML của trang web cho bạn.")

    except requests.RequestException as e:
        bot.reply_to(message, f"Đã xảy ra lỗi khi tải trang web: {e}")

    finally:
        # Đảm bảo xóa file sau khi gửi
        if os.path.exists(file_name):
            try:
                os.remove(file_name)
            except Exception as e:
                bot.reply_to(message, f"Đã xảy ra lỗi khi xóa file: {e}")
@bot.message_handler(commands=['tv'])
def tieng_viet(message):
    chat_id = message.chat.id
    message_id = message.message_id
    
    keyboard = types.InlineKeyboardMarkup()
    url_button = types.InlineKeyboardButton("Tiếng Việt 🇻🇳", url='https://t.me/setlanguage/abcxyz')
    keyboard.add(url_button)
    
    bot.send_message(chat_id, 'Click Vào Nút "<b>Tiếng Việt</b>" để đổi thành tv VN in đờ bét.', reply_markup=keyboard, parse_mode='HTML')
    
    # Delete user's command message
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        bot.send_message(chat_id, f"Không thể xóa tin nhắn: {e}", parse_mode='HTML')

# Hàm gọi API và định dạng kết quả
def get_tiktok_info(username):
    url = f"https://chongluadao.x10.bz/api/other/tiktokclll.php?user={username}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Kiểm tra lỗi HTTP
        data = response.json()
        user_info = data['data']['userInfo']['user']
        stats = data['data']['userInfo']['stats']

        is_verified = "Đã xác minh" if user_info['verified'] else "Chưa xác minh"
        account_status = "Công Khai" if not user_info['privateAccount'] else "Riêng Tư"
        has_playlist = "Có danh sách phát" if user_info['profileTab']['showPlayListTab'] else "Không có danh sách phát"
        following_visibility = "Danh sách following đã bị ẩn" if user_info['followingVisibility'] == 2 else "Danh sách following hiển thị"

        result = f"""
<blockquote>
╭─────────────⭓
│ 𝗜𝗗: {user_info['id']}
│ ‎𝗡𝗮𝗺𝗲:<a href="{user_info['avatarLarger']}">‎</a>{user_info['nickname']}
│ 𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲: {user_info['uniqueId']}
│ 𝗟𝗶𝗻𝗸: <a href="https://www.tiktok.com/@{user_info['uniqueId']}">https://www.tiktok.com/@{user_info['uniqueId']}</a>
│ 𝗩𝗲𝗿𝗶𝗳𝗶𝗲𝗱: {is_verified}
│ 𝗦𝘁𝗮𝘁𝘂𝘀:
│ | -> Tài khoản này đang ở chế độ {account_status}
│ | -> Là tài khoản Cá Nhân
│ | -> {has_playlist}
│ | -> {following_visibility}
│ 𝗖𝗿𝗲𝗮𝘁𝗲𝗱 𝗧𝗶𝗺𝗲: {user_info['createTime']}
│ 𝗕𝗶𝗼: {user_info['signature']}
│ 𝗙𝗼𝗹𝗹𝗼𝘄𝗲𝗿𝘀: {stats['followerCount']:,} Follower
│ 𝗙𝗼𝗹𝗹𝗼𝘄𝗶𝗻𝗴: {stats['followingCount']} Đang Follow
│ 𝗙𝗿𝗶𝗲𝗻𝗱𝘀: {stats['friendCount']} Bạn Bè
│ 𝗟𝗶𝗸𝗲𝘀: {stats['heartCount']:,} Thích
│ 𝗩𝗶𝗱𝗲𝗼𝘀: {stats['videoCount']} Video
├─────────────⭔
| 𝗟𝗮𝗻𝗴𝘂𝗮𝗴𝗲: {user_info['language']}
| 𝗡𝗮𝗺𝗲 𝗨𝗽𝗱𝗮𝘁𝗲: {user_info['nickNameModifyTime']}
| 𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲 𝗨𝗽𝗱𝗮𝘁𝗲: {user_info['uniqueIdModifyTime']}
| 𝗥𝗲𝗴𝗶𝗼𝗻: {user_info['region']}
╰─────────────⭓
</blockquote>
        """
        return result
    except requests.RequestException as e:
        return f"Không thể lấy dữ liệu từ API. Lỗi: {e}"

@bot.message_handler(commands=['tt'])
def handle_tiktok_info(message):
    try:
        username = message.text.split(' ', 1)[1].strip() if len(message.text.split(' ')) > 1 else None
        
        if username:
            result = get_tiktok_info(username)
            bot.reply_to(message, result, parse_mode='HTML')  
        else:
            bot.reply_to(message, "⚠️ Vui lòng nhập username hoặc link TikTok sau /tiktok.\n💬 Ví dụ: /tiktok nvp31012007")
    except Exception as e:
        bot.reply_to(message, f"Đã xảy ra lỗi: {e}")
#freefire
API_KEY = 'vay500k'
def get_freefire_info(user_id):
    url = f"https://api.scaninfo.vn/freefire/info/?id={user_id}&key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def get_country_flag(region_code):
    try:
        country = pycountry.countries.get(alpha_2=region_code)
        if country:
            flag = chr(ord(region_code[0]) + 127397) + chr(ord(region_code[1]) + 127397)
            return f"{country.name} {flag}"
    except:
        return "Không xác định"

def translate_language(language_code):
    try:
        language_code = language_code.replace("Language_", "").upper()
        language = pycountry.languages.get(alpha_2=language_code[:2])
        if language:
            return language.name
    except:
        return "Không xác định"

def format_freefire_info(data):
    def check_and_add(label, value):
        invalid_values = ["None", "Not Found", "Found", "Not Found/Not Found", ""]
        if value and value not in invalid_values:
            return f"├─ {label}: {value}\n"
        return None

    language = translate_language(data['Account Language'])
    region = get_country_flag(data['Account Region'])

    account_info = ""
    account_info += check_and_add("Tên", data.get('Account Name')) or ""
    account_info += check_and_add("UID", data.get('Account UID')) or ""
    account_info += check_and_add("Level", f"{data['Account Level']} (Exp: {data['Account XP']})") or ""
    account_info += check_and_add("Sever", region) or ""
    account_info += check_and_add("Ngôn Ngữ", language) or ""
    account_info += check_and_add("Likes", data.get('Account Likes')) or ""
    account_info += check_and_add("Tiểu Sử", data.get('Account Signature')) or ""
    account_info += check_and_add("Điểm Rank", data.get('BR Rank Points')) or ""
    account_info += check_and_add("Điểm Uy Tín", data.get('Account Honor Score')) or ""
    account_info += check_and_add("Ngày Tạo Acc", data.get('Account Create Time (GMT 0530)')) or ""
    account_info += check_and_add("Đăng Nhập Lần Cuối", data.get('Account Last Login (GMT 0530)')) or ""

    if account_info.strip():
        account_info = f"┌ 👤 THÔNG TIN TÀI KHOẢN\n{account_info}"

    pet_info = ""
    pet_info += check_and_add("Pet Đang Chọn", "Có" if data['Equipped Pet Information']['Selected?'] else "Không") or ""
    pet_info += check_and_add("Tên Pet", data['Equipped Pet Information']['Pet Name']) or ""
    pet_info += check_and_add("Level Pet", f"{data['Equipped Pet Information']['Pet Level']} (Exp: {data['Equipped Pet Information']['Pet XP']})") or ""

    if pet_info.strip():
        pet_info = f"┌ 🐾 THÔNG TIN PET\n{pet_info}"

    guild_info = ""
    guild_info += check_and_add("ID Quân Đoàn", data['Guild Information']['Guild ID']) or ""
    guild_info += check_and_add("Tên Quân Đoàn", data['Guild Information']['Guild Name']) or ""
    guild_info += check_and_add("Level", data['Guild Information']['Guild Level']) or ""
    guild_info += check_and_add("Số Thành Viên", f"{data['Guild Information']['Guild Current Members']}/{data['Guild Information']['Guild Capacity']}") or ""
    guild_info += check_and_add("Tên Chủ Quân Đoàn", data['Guild Leader Information']['Leader Name']) or ""

    if guild_info.strip():
        guild_info = f"┌ 👥 THÔNG TIN QUÂN ĐOÀN\n{guild_info}"

    full_info = "\n\n".join(filter(None, [account_info, pet_info, guild_info]))

    return f"<blockquote>{full_info}</blockquote>" if full_info.strip() else "Không có thông tin hợp lệ."

def download_image(image_url):
    response = requests.get(image_url)
    if response.status_code == 200:
        return BytesIO(response.content)
    return None

def create_freefire_sticker(data):
    nickname = data['Account Name']
    level = data['Account Level']
    avatar_id = data['Account Avatar Image'].split('=')[-1]
    banner_id = data['Account Banner Image'].split('=')[-1]
    pin_id = data['Account Pin Image'].split('=')[-1]

    sticker_url = f"https://api.scaninfo.vn/freefire/ffui/?nickname={nickname}&level={level}&avatar_id={avatar_id}&banner_id={banner_id}&pin_id={pin_id}"
    
    return sticker_url

@bot.message_handler(commands=['ff'])
def send_freefire_info(message):
    try:
        user_id = message.text.split()[1]
        data = get_freefire_info(user_id)
        if data:
            info = format_freefire_info(data)
            bot.reply_to(message, info, parse_mode='HTML')

            # Gửi sticker sau khi gửi thông tin tài khoản
            sticker_url = create_freefire_sticker(data)
            image_file = download_image(sticker_url)
            if image_file:
                bot.send_sticker(message.chat.id, image_file)
            else:
                bot.reply_to(message, "Không gửi được ảnh")
        else:
            bot.reply_to(message, "Không tìm thấy ID")
    except IndexError:
        bot.reply_to(message, "⚠️ Vui lòng nhập ID sau /ff.\n💬 Ví dụ: /ff 123456789")
    except Exception as e:
        bot.reply_to(message, f"Đã xảy ra lỗi: {str(e)}")
               
# Khởi động bot
print(banner())
bot.infinity_polling()