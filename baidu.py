# -*- coding: utf-8 -*-
import execjs
import requests
import re
import threading
from queue import Queue
from fake_useragent import UserAgent

JS_CODE = """
function a(r, o) {
    for (var t = 0; t < o.length - 2; t += 3) {
        var a = o.charAt(t + 2);
        a = a >= "a" ? a.charCodeAt(0) - 87 : Number(a),
        a = "+" === o.charAt(t + 1) ? r >>> a: r << a,
        r = "+" === o.charAt(t) ? r + a & 4294967295 : r ^ a
    }
    return r
}
var C = null;
var token = function(r, _gtk) {
    var o = r.length;
    o > 30 && (r = "" + r.substr(0, 10) + r.substr(Math.floor(o / 2) - 5, 10) + r.substring(r.length, r.length - 10));
    var t = void 0,
    t = null !== C ? C: (C = _gtk || "") || "";
    for (var e = t.split("."), h = Number(e[0]) || 0, i = Number(e[1]) || 0, d = [], f = 0, g = 0; g < r.length; g++) {
        var m = r.charCodeAt(g);
        128 > m ? d[f++] = m: (2048 > m ? d[f++] = m >> 6 | 192 : (55296 === (64512 & m) && g + 1 < r.length && 56320 === (64512 & r.charCodeAt(g + 1)) ? (m = 65536 + ((1023 & m) << 10) + (1023 & r.charCodeAt(++g)), d[f++] = m >> 18 | 240, d[f++] = m >> 12 & 63 | 128) : d[f++] = m >> 12 | 224, d[f++] = m >> 6 & 63 | 128), d[f++] = 63 & m | 128)
    }
    for (var S = h,
    u = "+-a^+6",
    l = "+-3^+b+-f",
    s = 0; s < d.length; s++) S += d[s],
    S = a(S, u);
    return S = a(S, l),
    S ^= i,
    0 > S && (S = (2147483647 & S) + 2147483648),
    S %= 1e6,
    S.toString() + "." + (S ^ h)
}
"""


class Dict:
    def __init__(self):
        self.sess = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
            'Cookie':'BAIDUID=44BFB20CF1AB2EB760D7E9C313B719BE:FG=1; to_lang_often=%5B%7B%22value%22%3A%22en%22%2C%22text%22%3A%22%u82F1%u8BED%22%7D%2C%7B%22value%22%3A%22zh%22%2C%22text%22%3A%22%u4E2D%u6587%22%7D%5D; REALTIME_TRANS_SWITCH=1; FANYI_WORD_SWITCH=1; HISTORY_SWITCH=1; SOUND_SPD_SWITCH=1; SOUND_PREFER_SWITCH=1; Hm_lvt_64ecd82404c51e03dc91cb9e8c025574=1582719028; from_lang_often=%5B%7B%22value%22%3A%22zh%22%2C%22text%22%3A%22%u4E2D%u6587%22%7D%2C%7B%22value%22%3A%22en%22%2C%22text%22%3A%22%u82F1%u8BED%22%7D%5D; __yjsv5_shitong=1.0_7_2a2e9f24fbc8c2db223fb2c517d22ceb63f9_300_1582720783557_163.125.213.202_6c62c1a0; yjs_js_security_passport=e8a85ae8229f3d4904fc43511373742c9624c683_1582720784_js; Hm_lpvt_64ecd82404c51e03dc91cb9e8c025574=1582720898'
        }
        self.token = None
        self.gtk = None
        self.javascript = execjs.compile(JS_CODE)

        # 获得token和gtk
        # 必须要加载两次保证token是最新的，否则会出现998的错误
        self.loadMainPage()
        self.loadMainPage()

    def loadMainPage(self):
        """
            load main page : https://fanyi.baidu.com/
            and get token, gtk
        """
        url = 'https://fanyi.baidu.com'

        try:
            r = self.sess.get(url, headers=self.headers)
            self.token = re.findall(r"token: '(.*?)',", r.text)[0]
            self.gtk = re.findall(r"window.gtk = '(.*?)';", r.text)[0]
        except Exception as e:
            raise e

    def langdetect(self, query):
        """
            post query to https://fanyi.baidu.com/langdetect
            return json like
            {"error":0,"msg":"success","lan":"en"}
        """
        url = 'https://fanyi.baidu.com/langdetect'
        data = {'query': query}
        try:
            r = self.sess.post(url=url, data=data)
        except Exception as e:
            raise e

        json = r.json()
        if 'msg' in json and json['msg'] == 'success':
            return json['lan']
        return None

    def dictionary(self,query,dst='zh', src='en'):
        """
            get translate result from https://fanyi.baidu.com/v2transapi
        """
        self.loadMainPage()
        url = 'https://fanyi.baidu.com/v2transapi'
        useragent = UserAgent()
        self.headers = {
            'User-Agent': useragent.chrome,
            'Cookie': 'BAIDUID=44BFB20CF1AB2EB760D7E9C313B719BE:FG=1; to_lang_often=%5B%7B%22value%22%3A%22en%22%2C%22text%22%3A%22%u82F1%u8BED%22%7D%2C%7B%22value%22%3A%22zh%22%2C%22text%22%3A%22%u4E2D%u6587%22%7D%5D; REALTIME_TRANS_SWITCH=1; FANYI_WORD_SWITCH=1; HISTORY_SWITCH=1; SOUND_SPD_SWITCH=1; SOUND_PREFER_SWITCH=1; Hm_lvt_64ecd82404c51e03dc91cb9e8c025574=1582719028; from_lang_often=%5B%7B%22value%22%3A%22zh%22%2C%22text%22%3A%22%u4E2D%u6587%22%7D%2C%7B%22value%22%3A%22en%22%2C%22text%22%3A%22%u82F1%u8BED%22%7D%5D; __yjsv5_shitong=1.0_7_2a2e9f24fbc8c2db223fb2c517d22ceb63f9_300_1582720783557_163.125.213.202_6c62c1a0; yjs_js_security_passport=e8a85ae8229f3d4904fc43511373742c9624c683_1582720784_js; Hm_lpvt_64ecd82404c51e03dc91cb9e8c025574=1582720898'
        }
        print(self.headers)
        sign = self.javascript.call('token', query, self.gtk)
        if not src:
            src = self.langdetect(query)

        data = {
             'from': src,
             'to': dst,
             'query': query,
             'simple_means_flag': 3,
            'sign': sign,
            'token': self.token,
        }
        print('request data:',data)
        try:
            r = self.sess.post(url=url, data=data, headers=self.headers)
        except Exception as e:
            raise e
        print('response status code:',r.status_code)
        if r.status_code == 200:
            json = r.json()
            if 'error' in json:
                raise Exception('baidu sdk error: {}'.format(json['error']))
                    # 998错误则意味需要重新加载主页获取新的token
            print(json)
            return json
        return None


class Mythread(threading.Thread):
    def __init__(self, func):
        threading.Thread.__init__(self)
        self.func = func

    def run(self):
        self.func()

def worker():
    while not q.empty():
        query = q.get()  # 或得任务
        tran.dictionary(query)

import time
def main():
    threads = []
    with open('data.txt', 'r') as fr:
        for line in fr:
            q.put(line)
    print('queue length:', q.qsize())
    for i in range(5):
        # mythread = Mythread(tran.dictionary)
        mythread = Mythread(worker)
        mythread.start()
        threads.append(mythread)

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    tran = Dict()
    q = Queue()
    start_time = time.time()
    main()
    end_time = time.time()
    print('耗时：',end_time-start_time)
