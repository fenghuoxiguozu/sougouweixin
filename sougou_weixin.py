import requests
import time
import datetime
import random
import re
import pymongo
from lxml import etree
from urllib.parse import urlencode
from requests.exceptions import ConnectionError,ReadTimeout

client=pymongo.MongoClient('localhost')
db=client['weixin']
proxy=None
data={}
base_url = 'http://weixin.sogou.com/weixin?'
header = {
    'Host': 'weixin.sogou.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
    'Cookie':'SUV=1499910768997732; pgv_pvi=8240447488; SUID=1AC0E3793865860A596481D000022D9A; dt_ssuid=8189762110; pex=C864C03270DED3DD8A06887A372DA219231FFAC25A9D64AE09E82AED12E416AC; ssuid=7806872269; GOTO=Af12784; usid=BeTtbpha_3Czby3E; CXID=A3F56DA60274BDDADFD2098DDC590E3A; LSTMV=270%2C284; LCLKINT=3381; tv_play_records=tvshow_2255230:20160619; IPLOC=CN3205; __guid=14337457.3934378981210230300.1538276274448.43; wuid=AAG3miobJAAAAAqLEyLHeAoAGwY=; ABTEST=0|1548424655|v1; weixinIndexVisited=1; SUIR=9D8224437274F139C4F9E57C727558A1; SNUID=A278FB81B0B430FBB9799B88B1AD4521; JSESSIONID=aaa_2XnKUWOx69Welk6Hw; PHPSESSID=2bek9su5oruue0beg2fe0p6bi0; ppinf=5|1548488664|1549698264|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZTo0NTolRTYlOTYlOTclRTclODklOUIlRTglQTYlODElRTQlQjglOEQlRTglQTYlODF8Y3J0OjEwOjE1NDg0ODg2NjR8cmVmbmljazo0NTolRTYlOTYlOTclRTclODklOUIlRTglQTYlODElRTQlQjglOEQlRTglQTYlODF8dXNlcmlkOjQ0Om85dDJsdU40Yk5uY1A4NXl0aks0T2E2WlNMQUlAd2VpeGluLnNvaHUuY29tfA; pprdig=CbWyFIHWkZjNnXI-gIItqn73bvfgvjHeVtFBh-RSiD7YGX9s5OpZEvLORqwXNKqtPi85WY2vp0ouKtbIjT8LGcQe-W2j7dCct2GPWjfl6buzq2XpnySgglGsNqb0fZHW4bJxlAk2uSLbpFRMWTRqaWdhf6t0aINtJClNsf85KDk; sgid=24-38952256-AVxMD9gPiciaIKFfGHOHR6xrg; ppmdig=15484886640000006ebe5365d10d699132324292eca275ee; sct=7; monitor_count=88'
}

#构造每一页URL
def get_url(keyword,page):
    data={
        'query': keyword,
        'type': 2,
        'page':page
    }
    query=urlencode(data)
    url=base_url+query
    return url

#获取网页源码
def get_html(url):
    print('正在抓取>>>', url)
    global proxy
    try:
        if proxy:
            proxies = {'http': 'http://' + proxy}
            response = requests.get(url=url, headers=header, proxies=proxies, allow_redirects=False, timeout=3)
        else:
            response = requests.get(url=url, headers=header, allow_redirects=False)

        if response.status_code == 200:
            html=response.text
            return html
        if response.status_code == 302:
            proxy=get_proxy()
            time.sleep(1+random.random())
            if proxy:
                print('Using proxy:',proxy)
                return get_html(url)
            else:
                print('Failed to get proxy')
                return None

    except (ConnectionError,ReadTimeout):
        proxy=get_proxy()
        time.sleep(1 + random.random())
        return get_html(url)

#解析每页需要提取的数据
def get_info(html):
    data = etree.HTML(html)
    contents = data.xpath('.//ul[@class="news-list"]/li')
    for content in contents:
        title="".join(content.xpath('.//h3//text()'))
        title = title.replace(' ','').strip()
        info = "".join(content.xpath('.//p[@class="txt-info"]//text()'))
        url= content.xpath('.//h3/a/@href')[0]
        author = content.xpath('.//a[@class="account"]/text()')[0]
        for i in range(len(contents)):
            times = re.findall(r'write\(timeConvert\(\'(\d+)\'\)\)</script>',html, re.S)
            times = times[i]
            times = datetime.datetime.fromtimestamp(int(times))
            publish_time = times.strftime('%Y-%m-%d')
        data={
            '标题': title,
            'URL': url,
            '内容': info,
            '作者': author,
            '发表时间':publish_time
        }
        save_to_Mongdb(data)

#从免费代理池每次获取一个代理
def get_proxy():
    # proxy_url = 'http://ip.11jsq.com/index.php/api/entry?method=proxyServer.generate_api_url&packid=0&fa=0&fetch_key=&qty=1&time=100&pro=&city=&port=1&format=txt&ss=1&css=&dt=1&specialTxt=3&specialJson='
    proxy_url ='http://localhost:5555/random'
    try:
        response=requests.get(url=proxy_url)
        if response.status_code==200:
            return response.text
        return None
    except ConnectionError:
        return None

#保存到MongDB
def save_to_Mongdb(data):
    if db['sougouweixin'].update({'URL':data['URL']},{'$set':data},True):
        print('Saved to Mongo successful',data['URL'])
    else:
        print('>>>Failed save to Mongo successful', data['URL'])


def main():
    keyword='国足'
    for page in range(1,101):
        url=get_url(keyword,page)
        time.sleep(3)
        html=get_html(url)
        if html:
            get_info(html)
        else:
            get_html(url)


if __name__ == '__main__':
    main()