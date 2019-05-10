# coding: utf-8

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
import random
import sys, json, re, os, io, requests
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# tmp_words = open("onwords.txt", "r", encoding="utf-8")
# onwords = tmp_words.readlines()
# tmp_words.close()
# os.remove("onwords.txt")
#
# tmp_words = open("offwords.txt", "r", encoding="utf-8")
# offwords = tmp_words.readlines()
# tmp_words.close()
# os.remove("offwords.txt")
#
# data = json.loads(sys.stdin.readline())
# jap = data["jap"]
# pos = data["pos"]
# neg = data["neg"]
# que = data["que"]
# pic = data["pic"]
# mov = data["mov"]
# span = data["span"]
# span_since = data["span_since"]
# span_until = data["span_until"]
# loc = data["loc"]
# loc_near = data["loc_near"]
# loc_within = data["loc_within"]
# rep = data["rep"]
# rep_to = data["rep_to"]
# num = int(data["num"])

#テスト用の設定

onwords = []
while True:
    words = input("ONword: ")
    if words != "":
        onwords.append(words)
    else:
        break

offwords = []
while True:
    words = input("OFFword: ")
    if words != "":
        offwords.append(words)
    else:
        break


mode = input("mode: ") # "Top", "Latest", "People", "Photos", "Videos", "News", "Broadcasts"

jap = True # 日本語のツイートのみ
pos = False # ポジティブな内容
neg = False # ネガティブな内容
que = False # 疑問文が入っている
span = False # 投稿日時の範囲を設定
span_since = "2018-01-01"
span_until = "2019-04-29"
loc = False # 以下の地域での投稿に限定
loc_near = ""
rep = False # 特定のユーザーへの返信のみ
rep_to = ""
num = int(input("num: ")) # 実際にいいね！する数
interval = int(input("interval: ")) # アクション同士の間隔時間


line_notify_token = 'GXfWzNXa2GuTTU8MtfvbGT9tKmSpoTSAobPELTOO3SQ'
line_notify_api = 'https://notify-api.line.me/api/notify'

options = webdriver.ChromeOptions()
driver_path = r"src/chromedriver.exe"

driver_path = r"../chromedriver.exe"

PROFILE_PATH = "C:\\Users\\{0}\\AppData\\Local\\Google\\Chrome\\User Data".format(os.environ.get("USERNAME"))

userdata_dir = 'UserData'
os.makedirs(userdata_dir, exist_ok=True)

options.add_argument('--user-data-dir=' + userdata_dir)

good_user_list = []


# ウェブを開く
def make_driver():
    global driver

    driver = webdriver.Chrome(executable_path=driver_path, options=options)
    driver.set_window_position(0, 0)
    driver.set_window_size(600, 660)
    URL = "https://twitter.com/explore"
    driver.get(URL)
    if not("twitter" in driver.current_url):
        print(json.dumps({"result":"既に他のChromeが開かれています。\nすべて閉じてからもう一度実行してください。"}))


# ログインしていればTrue
def login_check():
    sleep(1)
    if len(driver.find_elements_by_xpath('//a[@href="/login"]')) == 0:
        return True

    else:
        URL = "https://twitter.com/login"
        driver.get(URL)
        message = "<初回設定>\nログインした後、一度ブラウザーを閉じてもう一度実行ボタンを押して下さい。"
        print(json.dumps({"result": message}))
        return False


# 新しいツイッターでなければ新しいツイッターにする
def check_new_twitter():
    new = driver.find_elements_by_xpath('//button[text()="新しいTwitterを試す" or text()="Try the new Twitter"]')
    if len(new) == 0:
        return True

    driver.find_element_by_xpath('//a[@href="/settings"]').send_keys(Keys.ENTER)
    sleep(0.2)
    new[0].send_keys(Keys.ENTER)
    for i in range(5):
        sleep(1)
        if driver.current_url == "https://twitter.com/home":
            break


# 様々なオプションを付け、検索を行う
def search(onwords, offwords, jap, pos, neg, que, span, span_since, span_until, loc, loc_near, rep, rep_to):
    driver.get("https://twitter.com/explore")
    driver.set_page_load_timeout(10)
    sleep(2)
    inputbox = driver.find_elements_by_xpath('//input[contains(@spellcheck, "")]')

    if len(inputbox) == 0:
        return False

    goword = ""
    for onword in onwords:
        goword += onword + " "
    for offword in offwords:
        goword += '-' + offword + ' '
    if jap:
        goword += "lang:ja "
    if pos and neg:
        pos = False
        neg = False
    if pos:
        goword += ":) "
    if neg:
        goword += ":( "
    if que:
        goword += "? "
    if span:
        goword += "since:" + span_since + " "
        goword += "until:" + span_until + " "
    if loc:
        goword += "near:" + loc_near + " "
    if rep:
        goword += "to:" + rep_to

    inputbox[0].send_keys(goword)
    sleep(0.5)
    inputbox[0].send_keys(Keys.ENTER)
    driver.set_page_load_timeout(10)
    sleep(2)

    return True


# ｢話題のツイート｣｢最新｣｢アカウント｣｢画像｣｢動画｣を選択
def mode_select(mode, num, interval): #"Top", "Latest", "People", "Photos", "Videos"
    if mode == "Top":
        elements = driver.find_elements_by_xpath('//a[div[span[text()="話題のツイート" or text()="Top"]]]')

    elif mode == "Latest":
        elements = driver.find_elements_by_xpath('//a[div[span[text()="最新" or text()="Latest"]]]')

    elif mode == "People":
        elements = driver.find_elements_by_xpath('//a[div[span[text()="アカウント" or text()="People"]]]')

    elif mode == "Photos":
        elements = driver.find_elements_by_xpath('//a[div[span[text()="画像" or text()="Photos"]]]')

    elif mode == "Videos":
        elements = driver.find_elements_by_xpath('//a[div[span[text()="動画" or text()="Videos"]]]')

    else:
        return False

    if len(elements) != 0:
        url = elements[0].get_attribute("href")
        driver.get(url)
        driver.set_page_load_timeout(10)
        sleep(2)

    if mode == "People":
        # crawling_users(num, 0, 0)
        scrolling_follow(num, interval)
    else:
        scrolling_like(num, interval)


# いいねを上からnum個、およそinterval秒ごとに押す
def scrolling_like(num, interval):
    like_count = 0
    for i in range(1000):

        likes = driver.find_elements_by_xpath('//div[@data-testid="like"]')
        unlikes = driver.find_elements_by_xpath('//div[@data-testid="unlike"]')
        if len(likes) > 0:
            likes[0].location_once_scrolled_into_view
            likes[0].send_keys(Keys.ENTER)
            like_count += 1
        elif len(unlikes) > 0:
            unlikes[-1].location_once_scrolled_into_view
            sleep(1)
        else:
            print("投稿が一つも存在しませんでした")
            break

        if like_count >= num:
            print("規定数に到達しました")
            break

        sleep(random.uniform(interval/2, interval*3/2))

        likes = driver.find_elements_by_xpath('//div[@data-testid="like"]')
        if len(likes) == 0:
            print("条件に合う投稿全てにいいねしました")
            break

    print("終了")


# フォローを上からnum個、およそinterval秒ごとに押す
def scrolling_follow(num, interval):
    follow_count = 0
    for i in range(1000):
        follows = driver.find_elements_by_xpath('//div[contains(@data-testid, "-follow")]')
        unfollows = driver.find_elements_by_xpath('//div[contains(@data-testid, "-unfollow")]')
        if len(follows) > 0:
            follows[0].location_once_scrolled_into_view
            follows[0].send_keys(Keys.ENTER)
            follow_count += 1
        elif len(unfollows) > 0:
            unfollows[-1].location_once_scrolled_into_view
            sleep(1)
        else:
            print("アカウントが一つも存在しませんでした")
            break

        if follow_count >= num:
            print("規定数に到達しました")
            break

        sleep(random.uniform(interval / 2, interval * 3 / 2))

        follows = driver.find_elements_by_xpath('//div[contains(@data-testid, "-follow")]')
        if len(follows) == 0:
            print("条件に合うアカウントを全てフォローしました")
            break

    print("終了")


# クローリングしながらより詳細なフォロー、いいねをする
def crawling_users(want_num, follow_num, like_num):
    follow_count = 0
    like_count = 0
    user_ids = []
    for i in range(100):
        tmp_ids = driver.find_elements_by_xpath('//div/span[contains(text(), "@")]')
        for tmp_id in tmp_ids:
            if tmp_id.text.split("@")[0] == "":
                print(tmp_id.text.split("@")[1])
                user_ids.append(tmp_id.text.split("@")[1])

        user_ids = sorted(set(user_ids), key=user_ids.index)

        if len(user_ids) >= want_num*5:
            break
        tmp_ids[-1].location_once_scrolled_into_view
        sleep(1)

    for user_id in user_ids:
        detail = get_id_info(user_id)


# ユーザーページに移動し各種情報を取得
def get_id_info(id):
    driver.get("https://twitter.com/" + id)
    driver.set_page_load_timeout(10)
    sleep(5)

    name = driver.find_elements_by_xpath('//div[div[div[span[containts(text(), {0})]]]]/div[0]'.format(id))
    info = driver.find_elements_by_xpath('//main/div/div[2]/div/div/div/div/div/div/div[1]/div/div[3]'.format(id))

    print(all[0].text)
    # names = driver.find_elements_by_tag_name('h1')
    # if len(names) == 1:
    #     name = ""
    # elif len(names) != 0:
    #     name = names[1].text
    # else:
    #     name = ""
    # nums = driver.find_elements_by_xpath('//ul/li/*/span')
    # post = num_to_int(nums[0].text)
    # byfollow = num_to_int(driver.find_element_by_xpath('//a[@href="/{0}/followers"]').get_attribute("title"))
    # follow = num_to_int(driver.find_element_by_xpath('//a[@href="/{0}/following"]').get_attribute("title"))
    # intros = driver.find_elements_by_xpath("//main/div/div[1]/span")
    # if len(intros) != 0:
    #     intro = intros[0].text
    # else:
    #     intro = ""
    # # ストップワード
    # official = (len(driver.find_elements_by_xpath('//span[@title="認証済み"]')) != 0 or
    #             "official" in id or
    #             "circle" in id or
    #             "group" in id or
    #             "club" in id or
    #             "team" in id or
    #             "japan" in id or
    #             "shop" in id or
    #             "協会" in name or
    #             "公式" in name or
    #             "団体" in name or
    #             "日本" in name or
    #             "店" in name or
    #             "お問い合わせ" in intro or
    #             "プレゼント" in intro or
    #             "海外投資" in intro or
    #             "ご予約" in intro or
    #             "ご案内" in intro or
    #             "ご紹介" in intro or
    #             "お客様" in intro or
    #             "弊社" in intro or
    #             "開業" in intro or
    #             "公式" in intro or
    #             "公認" in intro or
    #             "開催" in intro or
    #             "無料" in intro or
    #             "投資" in intro or
    #             "稼ぎ" in intro
    #             )
    # id = id.lower()
    # return {"id":id, "name":name, "post":post, "follow":follow, "byfollow":byfollow, "intro":intro, "official":official}


# falseだと0になる
def f(bool, num):
    if bool:
        return num

    return 0


# 〇〇千などを数値化
def num_to_int(num):
    if "," in num:
        parts = num.split(",")
        return int(parts[0])*1000 + int(parts[1])
    elif "K" in num:
        return int(float(num.split("K")[0])*1000)
    elif "万" in num:
        return int(float(num.split("万")[0])*10000)
    elif "M" in num:
        return int(float(num.split("M")[0])*1000000)
    elif "億" in num:
        return int(float(num.split("億")[0])*100000000)
    else:
        return int(num)


# 文字列にひらがなorカタカナが入っていればTrue
def kana_in(word):
    kana_set = {chr(i) for i in range(12353, 12436)}
    for kana in {chr(i) for i in range(12449, 12533)}:
        kana_set.add(kana)
    word_set = set(word)
    if kana_set - word_set == kana_set:
        return False
    else:
        return True


# 韓国語または中国語特有の漢字が入っていればTrue
def asian_check(in_str):
    return (set(in_str) - set(in_str.encode('sjis','ignore').decode('sjis'))) != set([])


# グッドユーザーを選別
def good_user(user, jap=True, foreign=False, official=True, over_follow=True, over_byfollow=True, min_follow=5, min_byfollow=5, min_post=1):
    flag = 0
    if jap==False or kana_in(user["intro"]) or kana_in(user["name"]): # jap=True:名前か説明文にひらがながないとはじく
        flag += 1
    if foreign==False or asian_check(user["intro"]): # foreign=True:説明文に韓国語や中国語があるとはじく
        flag += 1
    if official==False or user["official"]==False: # official=True:認証済みアカウントをはじく
        flag += 1
    if over_follow==False or (user["follow"] <= user["byfollow"]*3): # over_follow=True:フォローがフォロワーより三倍以上多いとはじく
        flag += 1
    if over_byfollow==False or (user["byfollow"] <= user["follow"]*3): # over_byfollow=True:フォロワーがフォローより三倍以上多いとはじく
        flag += 1
    if user["follow"] >= min_follow: # min_follow=int:フォローがint人以下ははじく
        flag += 1
    if user["byfollow"] >= min_byfollow: # min_byfollow=int:フォロワーがint人以下ははじく
        flag += 1
    if user["post"] >= min_post: # min_post=int:投稿がint件以下ははじく
        flag += 1
    if user["followed"] == False: # 既にフォローしているユーザーははじく
        flag += 1

    if flag == 9:
        good_user_list.append(user["id"])
        return True
    return False


# ココから下が実行部

make_driver()
if login_check():
    check_new_twitter()
    search(onwords, offwords, jap, pos, neg, que, span, span_since, span_until, loc, loc_near, rep, rep_to)
    mode_select(mode, num, interval)


