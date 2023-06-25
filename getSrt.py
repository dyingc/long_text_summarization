# A function to get bilibili cc subtitle 获取哔哩哔哩视频的cc字幕
# created by huilongyeo on 2022/5/6
# modified by dyingc on 2023/6/25
# Original github: https://github.com/huilongyeo/bilibiliGetSrt.git

import json
import math
from bs4 import BeautifulSoup

from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import ui
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
import time, sys
import pickle
import os.path
import requests


# Connect Bilibili with login by selenium in Microsoft Edge
def getSrtJson(bvid:str, pageNo:int=1)->dict:
    global driver  # driver 需要设为全局变量，否则会闪退
    options = Options()  # use Chrome as driver
    options.headless = False  # show Chrome driver
    options.headless = True  # show Chrome driver
    # enable Performance Logging of Chrome
    caps = DesiredCapabilities.CHROME
    caps['loggingPrefs'] = {'performance': 'ALL'}
    options.add_argument("--ignore-certificate-errors")  # Ignores any certification errors if there is any
    options.add_experimental_option('w3c', False)  # run in non-W3C mode to get network log
    driver = webdriver.Chrome(options=options, 
                          desired_capabilities=caps)  # Chrome driver location

    # if have not cookie of login, let user login manual and save cookie
    if not os.path.exists('cookies.pickle'):
        web_url = "https://www.bilibili.com/"
        driver.get(web_url)

        # wait element response
        time.sleep(3)
        input("After login, press enter to continue...")
        with open("cookies.pickle", 'wb') as file:
            # 3rd argument 0 means ASCII protocol, avoid pickle garbled
            pickle.dump(driver.get_cookies(), file, 0)
        print(driver.get_cookies())
        driver.close()

    title = "null"  # save title of video
    # use cookies to login
    with open("cookies.pickle", 'rb') as file:
        cookiesList = pickle.load(file)
    # access before add cookie avoid driver request an empty page
    try:
        url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        driver.get(url)
        for cookie in cookiesList:
            driver.add_cookie(cookie)

        # access again after driver get cookies
        driver.get(url)

        # Get "aid" and "cid" according to the page number
        try:
          html = driver.page_source
          soup = BeautifulSoup(html, 'html.parser')
          body = soup.find('body').text
          v_data0 = json.loads(body)
          
          aid = v_data0.get('data').get('aid')
          # import ipdb; ipdb.set_trace()
          cid = v_data0.get('data').get('pages')[pageNo-1].get('cid')
        except Exception as ex:
          print(f"Error occurs while fetch aid/cid for page: {pageNo}: {ex}")
          sys.exit(-1)

        # Get subtitle URL
        url = f"https://api.bilibili.com/x/player/wbi/v2?aid={aid}&cid={cid}"
        driver.get(url)
        try:
          html = driver.page_source
          soup = BeautifulSoup(html, 'html.parser')
          body = soup.find('body').text
          v_data = json.loads(body)
          # print(v_data.get('data').keys())
          
          subtitle = v_data.get('data').get('subtitle').get('subtitles')[0]
          subtitle_id = subtitle.get('id')
          subtitle_lan = subtitle.get('lan')
          subtitle_url = "http:" + subtitle.get('subtitle_url')
        except Exception as ex:
          print(f"Error occurs while fetch subtitle: {ex}")
          print(f"Number of subtitles: {len(v_data.get('data').get('subtitle').get('subtitles')):d}")
          # import ipdb; ipdb.set_trace()
          sys.exit(-1)
        try:
          driver.get(subtitle_url)
        except Exception as ex:
          print(f"Error fetch subtitle at: {subtitle_url}\nError message: {ex}")
          sys.exit(-1)
        try:
          html = driver.page_source
          soup = BeautifulSoup(html, 'html.parser')
          subtitle_json = json.loads(soup.find('body').text) # A json
          # Output to srt file
          srt_file = v_data.get('data').get('title') if (v_data.get('data').get('title')!=None and v_data.get('data').get('title')!='') else v_data.get('data').get('bvid')
          json_to_srt(subtitle_json, srt_file)
        except Exception as ex:
          print(f"Error retrieve subtitle from {subtitle_url}\nError message: {ex}")
          sys.exit(-1)
        
        driver.close()

        final_result = dict()
        final_result['tname'] = v_data.get('data').get('tname') # Video category
        final_result['title'] = v_data.get('data').get('title') # Video title
        final_result['desc'] = v_data.get('data').get('desc') # Video title
        final_result['subtitle_json'] = subtitle_json # Video subtitle (json)

        return final_result
         
    except Exception as ex_outer:
        print()
        raise RuntimeError(f"Error: {ex_outer}")

#     if cc_url:
#         subtitle = requests.get(cc_url)
#         return subtitle.json(), title

    else:
        print("find not subtitle")
        return {'tname': None, 'title': None, 'desc': None, 'subtitle_json': None}


def json_to_srt(srtJson, title):
    file = ''
    i = 1  # sequence number
    for data in srtJson['body']:
        start = data['from']  # get start time
        stop = data['to']  # get stop time
        content = data['content']  # get the content of subtitle
        file += '{}\n'.format(i)  # add sequence number
        hour = math.floor(start) // 3600
        minute = (math.floor(start) - hour * 3600) // 60
        sec = math.floor(start) - hour * 3600 - minute * 60
        minisec = int(math.modf(start)[0] * 100)  # process start time
        file += str(hour).zfill(2) + ':' + str(minute).zfill(2) + ':' + str(sec).zfill(2) + ',' + str(
            minisec).zfill(2)  # fill number by 0 and write to file
        file += ' --> '
        hour = math.floor(stop) // 3600
        minute = (math.floor(stop) - hour * 3600) // 60
        sec = math.floor(stop) - hour * 3600 - minute * 60
        minisec = abs(int(math.modf(stop)[0] * 100 - 1))  # -1 to avoid 2 subtitle show in same time
        file += str(hour).zfill(2) + ':' + str(minute).zfill(2) + ':' + str(sec).zfill(2) + ',' + str(
            minisec).zfill(2)
        file += '\n' + content + '\n\n'  # write content to file
        i += 1

    try:
        with open("{}.srt".format(title), 'w', encoding='utf-8') as f:
            f.write(file)
            f.close()
            # print("{}.srt".format(title))
    except Exception:
        with open("{}.srt".format("temp"), 'w', encoding='utf-8') as f:
            f.write(file)
            f.close()
            print("title error")
            print("{}.srt".format(title))
